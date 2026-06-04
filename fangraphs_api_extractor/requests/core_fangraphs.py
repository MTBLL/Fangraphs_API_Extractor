import os
from enum import Enum
from threading import Lock
from typing import Any, Dict, Optional

import requests
from requests.sessions import RequestsCookieJar

from fangraphs_api_extractor.utils import (
    BATTING_POSITIONS,
    FANGRAPHS_API_ENDPOINT,
    PROJECTION_SYSTEMS,
    Logger,
)
from fangraphs_api_extractor.utils.constants import (
    FANGRAPHS_CHALLENGE_URL,
    USER_AGENT_HEADER,
)
from fangraphs_api_extractor.utils.errors import (
    InvalidPositionError,
    InvalidPositionGroupError,
    InvalidProjectionsSystemError,
)


class ResponseStatus(Enum):
    """Enum representing possible API response statuses"""

    SUCCESS = 200
    FORBIDDEN = 403
    NOT_FOUND = 404
    RATE_LIMITED = 429
    SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503
    UNKNOWN_ERROR = 0


class CoreFangraphs:
    """
    Core class for interacting with the Fangraphs API.
    Responsible only for making API requests and returning raw data.
    """

    def __init__(self, year: int, max_workers: Optional[int] = None):
        self.year = year
        self.logger = Logger("core_fangraphs")
        self.logger_lock = Lock()  # Thread-safe logging

        # Configure default number of workers if not specified (use CPU count)
        cpu_count = os.cpu_count() or 1
        self.max_workers = (
            max_workers if max_workers is not None else min(32, cpu_count * 4)
        )

        self.session = requests.Session()
        self.session.headers.update(USER_AGENT_HEADER)
        self.session.cookies = RequestsCookieJar()

        # Set the API URL
        self.fg_projections_url = FANGRAPHS_API_ENDPOINT

        # Cloudflare clearance. Fangraphs fronts the projections API with a
        # managed JS challenge that plain HTTP clients cannot pass. When
        # FLARESOLVERR_URL is set we delegate solving to a FlareSolverr sidecar,
        # then adopt the cf_clearance cookie + the exact User-Agent it used and
        # reuse them for every API call (cf_clearance is bound to that UA and the
        # egress IP). Unset → legacy behavior (requests go out unauthenticated
        # and will 403 while the challenge is active).
        self.flaresolverr_url = os.environ.get("FLARESOLVERR_URL")
        self._clearance_lock = Lock()
        self._clearance_ready = False

    def _check_request_status(
        self,
        status: int,
        extend: str = "",
    ) -> None:
        """
        Handles Fangraphs API response status codes by logging appropriate messages

        Args:
            status: HTTP status code from the response
            extend: The endpoint extension that was requested
            params: Query parameters used in the request
            headers: Headers used in the request
        """
        # For error cases, use thread-safe logging
        with self.logger_lock:
            match status:
                case ResponseStatus.SUCCESS.value:
                    return

                case ResponseStatus.FORBIDDEN.value:
                    self.logger.logging.warning(
                        "Forbidden (403) — Cloudflare challenge not satisfied. "
                        "Set FLARESOLVERR_URL to enable challenge solving."
                    )

                case ResponseStatus.NOT_FOUND.value:
                    self.logger.logging.warning(f"Endpoint not found: {extend}")

                case ResponseStatus.RATE_LIMITED.value:
                    self.logger.logging.warning("Rate limit exceeded")

                case ResponseStatus.SERVER_ERROR.value:
                    self.logger.logging.warning("Internal server error")

                case ResponseStatus.SERVICE_UNAVAILABLE.value:
                    self.logger.logging.warning("Service unavailable")

                case _:
                    self.logger.logging.warning(f"Unknown error: {status}")

    def _ensure_clearance(self) -> None:
        """Lazily obtain a Cloudflare clearance cookie before the first request.

        No-op when FLARESOLVERR_URL is unset or clearance is already held. The
        lock makes the one-time solve safe if requests are ever parallelized.
        """
        if not self.flaresolverr_url or self._clearance_ready:
            return
        with self._clearance_lock:
            if not self._clearance_ready:
                self._solve_cloudflare()

    def _solve_cloudflare(self) -> None:
        """Solve Fangraphs' Cloudflare challenge via FlareSolverr and apply the
        resulting cf_clearance cookie + User-Agent to the session.

        Raises on transport or solve failure so the caller (and Prefect's
        transient-retry) can react rather than silently 403-looping.
        """
        payload = {
            "cmd": "request.get",
            "url": FANGRAPHS_CHALLENGE_URL,
            "maxTimeout": 60000,
        }
        resp = requests.post(self.flaresolverr_url, json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise RuntimeError(
                "FlareSolverr could not solve the Cloudflare challenge: "
                f"{data.get('message')}"
            )
        solution = data["solution"]
        # cf_clearance is keyed to the solving browser's User-Agent — adopt it
        # verbatim, overriding the static USER_AGENT_HEADER set at construction.
        self.session.headers["User-Agent"] = solution["userAgent"]
        for cookie in solution.get("cookies", []):
            # FlareSolverr normally returns a domain; fall back to the Fangraphs
            # zone (the only host we solve) so cookie matching never sees None.
            self.session.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie.get("domain") or ".fangraphs.com",
            )
        self._clearance_ready = True
        with self.logger_lock:
            self.logger.logging.info(
                "Obtained Cloudflare clearance via FlareSolverr"
            )

    def _get(
        self,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        extend: str = "",
    ) -> Dict[str, Any]:
        """
        Make a GET request to the Fangraphs API.

        Args:
            params: Query parameters for the request
            headers: Additional headers for the request
            extend: URL path extension

        Returns:
            The JSON response from the API
        """
        self._ensure_clearance()
        endpoint = self.fg_projections_url + extend
        # Use the session (not module-level requests.get) so the cf_clearance
        # cookie and solved User-Agent travel with every call.
        r = self.session.get(endpoint, params=params, headers=headers)

        # A 403 mid-run means the cf_clearance cookie expired or was rejected.
        # Re-solve once and retry before surfacing the failure.
        if r.status_code == ResponseStatus.FORBIDDEN.value and self.flaresolverr_url:
            with self.logger_lock:
                self.logger.logging.warning(
                    "403 from Fangraphs — refreshing Cloudflare clearance"
                )
            with self._clearance_lock:
                self._clearance_ready = False
            self._ensure_clearance()
            r = self.session.get(endpoint, params=params, headers=headers)

        self._check_request_status(r.status_code, extend)

        # Only a 200 carries a JSON body. On any other status (e.g. an
        # unresolved 403 serving the Cloudflare challenge HTML) raise a clear
        # error rather than letting r.json() throw a cryptic JSONDecodeError —
        # get_projections_data catches this and returns None.
        if r.status_code != ResponseStatus.SUCCESS.value:
            raise RuntimeError(
                f"Fangraphs returned HTTP {r.status_code} for "
                f"'{extend or 'projections'}'"
            )

        data = r.json()
        if self.logger:
            with self.logger_lock:
                self.logger.log_request(
                    endpoint=endpoint, params=params, headers=headers, response=data
                )

        return data

    def get_projections_data(
        self,
        position_group: str,
        params: Optional[Dict[str, Any]] = None,
        position: str = "all",
        projections_system: str = "steamer",
    ) -> Optional[Dict[str, Any]]:
        """
        Get raw projection data from the Fangraphs API.

        Args:
            position_group: Type of player data to get (bat, pit, sta, rel)
            params: Additional query parameters
            position: Position filter (all, c, 1b, etc.)
            projections_system: Projection system to use (steamer, zips, etc.)

        Returns:
            Raw JSON data from the API, or None if an error occurred
        """
        try:
            if position_group not in ["bat", "pit", "sta", "rel"]:
                raise InvalidPositionGroupError(position_group)
            if position_group == "bat":
                if position not in BATTING_POSITIONS:
                    raise InvalidPositionError(position)
            if position_group in ["pit", "sta", "rel"]:
                if position != "all":
                    raise InvalidPositionError(position)

            if projections_system not in PROJECTION_SYSTEMS:
                raise InvalidProjectionsSystemError(projections_system)

        except InvalidPositionError as e:
            self.logger.logging.error(f"Invalid position: {e}")
            return None
        except InvalidPositionGroupError as e:
            self.logger.logging.error(f"Invalid position group: {e}")
            return None
        except InvalidProjectionsSystemError as e:
            self.logger.logging.error(f"Invalid projections system: {e}")
            return None

        merged_params = {
            "pos": position,
            "stats": position_group,
            "type": projections_system,
        }
        merged_params.update(params or {})

        try:
            self.logger.logging.debug(
                f"Fetching {position_group} projections with {projections_system}"
            )
            raw_data = self._get(params=merged_params)
            return raw_data
        except Exception as e:
            self.logger.logging.error(f"Error fetching projections: {e}")
            return None
