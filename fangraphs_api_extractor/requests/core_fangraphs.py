import os
from enum import Enum
from threading import Lock
from typing import Any, Dict, Optional

import requests
from requests.sessions import RequestsCookieJar

from fangraphs_api_extractor.utils import (
    BATTING_POSITIONS,
    FANGRAPHS_PROJECTIONS_ENDPOINT,
    PROJECTION_SYSTEMS,
    Logger,
)
from fangraphs_api_extractor.utils.constants import USER_AGENT_HEADER
from fangraphs_api_extractor.utils.errors import (
    InvalidPositionError,
    InvalidPositionGroupError,
    InvalidProjectionsSystemError,
)


class ResponseStatus(Enum):
    """Enum representing possible API response statuses"""

    SUCCESS = 200
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

    def __init__(self, year: int, logger: Logger, max_workers: Optional[int] = None):
        self.year = year
        self.logger = logger
        self.logger_lock = Lock()  # Thread-safe logging

        # Configure default number of workers if not specified (use CPU count)
        cpu_count = os.cpu_count()
        if cpu_count is None:
            cpu_count = 1
        self.max_workers = (
            max_workers if max_workers is not None else min(32, cpu_count * 4)
        )

        self.session = requests.Session()
        self.session.headers.update(USER_AGENT_HEADER)
        self.session.cookies = RequestsCookieJar()

        # Set the API URL
        self.fg_projections_url = FANGRAPHS_PROJECTIONS_ENDPOINT

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

                case ResponseStatus.NOT_FOUND.value:
                    self.logger.logging.warn(f"Endpoint not found: {extend}")

                case ResponseStatus.RATE_LIMITED.value:
                    self.logger.logging.warn("Rate limit exceeded")

                case ResponseStatus.SERVER_ERROR.value:
                    self.logger.logging.warn("Internal server error")

                case ResponseStatus.SERVICE_UNAVAILABLE.value:
                    self.logger.logging.warn("Service unavailable")

                case _:
                    self.logger.logging.warn(f"Unknown error: {status}")

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
        endpoint = self.fg_projections_url + extend
        r = requests.get(
            endpoint, params=params, headers=headers, cookies=self.session.cookies
        )
        self._check_request_status(r.status_code, extend)

        if self.logger:
            with self.logger_lock:
                self.logger.log_request(
                    endpoint=endpoint, params=params, headers=headers, response=r.json()
                )

        return r.json()

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
            self.logger.logging.info(
                f"Fetching {position_group} projections with {projections_system}"
            )
            raw_data = self._get(params=merged_params)
            return raw_data
        except Exception as e:
            self.logger.logging.error(f"Error fetching projections: {e}")
            return None
