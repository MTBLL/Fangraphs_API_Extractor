from enum import Enum

FANGRAPHS_API_ENDPOINT = "https://www.fangraphs.com/api/projections?"

# Cloudflare-protected HTML page used to mint a cf_clearance cookie via
# FlareSolverr. Fangraphs fronts the whole fangraphs.com zone with a managed JS
# challenge; solving against this page yields a cf_clearance cookie that
# authorizes the same-zone /api/projections calls.
FANGRAPHS_CHALLENGE_URL = "https://www.fangraphs.com/projections"

# deprecated
BUILD_ID = "hkm1KP0YmmKjp8AmZS3FM"
FANGRAPHS_CORE_BUILD_ENDPOINT = "https://www.fangraphs.com/_next/data/" + BUILD_ID
FANGRAPHS_PROJECTIONS_ENDPOINT = FANGRAPHS_CORE_BUILD_ENDPOINT + "/projections.json"


# Requests
USER_AGENT_HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}


class ProjectionSource(str, Enum):
    """Valid Fangraphs projection system identifiers.

    Three categories of full-season-or-RoS data:
      - Pre-season: full-season forecasts; available before and during the season,
        but the underlying numbers don't change mid-season.
      - Projections updated: full-season forecasts refit with in-season data; only available
        once the season is underway. Currently only Steamer and ZiPS publish these.
      - Rest-of-season (RoS): project only remaining games (162 − games played);
        updated mid-season.

    Pitcher notes:
      - thebatx has no pitcher data; the fetch handler automatically maps it to thebat.
      - rthebatx has no pitcher data; the fetch handler automatically maps it to rthebat.
      - oopsy / roopsydc are valid for both hitters and pitchers.

    Add new sources here — PROJECTION_SYSTEMS is derived from this enum automatically.
    """

    # Pre-season projections (full-season; not updated mid-season)
    STEAMER = "steamer"
    ZIPS = "zips"
    ZIPS_DC = "zipsdc"
    ATC = "atc"
    DEPTH_CHARTS = "fangraphsdc"
    THE_BAT = "thebat"
    THE_BATX = "thebatx"
    OOPSY = "oopsy"

    # Updated projections (full-season; refit with in-season data)
    UZIPS = "uzips"
    STEAMER_U = "steameru"

    # Rest-of-season projections (remaining games only)
    STEAMER_R = "steamerr"
    RZIPS = "rzips"
    RZIPS_DC = "rzipsdc"
    RFANGRAPHS_DC = "rfangraphsdc"
    RATC_DC = "ratcdc"
    RTHE_BAT = "rthebat"
    RTHE_BATX = "rthebatx"
    ROOPSY_DC = "roopsydc"


PRESEASON_PROJECTION_SYSTEMS = [
    ProjectionSource.STEAMER.value,
    ProjectionSource.ZIPS.value,
    ProjectionSource.ZIPS_DC.value,
    ProjectionSource.ATC.value,
    ProjectionSource.DEPTH_CHARTS.value,
    ProjectionSource.THE_BAT.value,
    ProjectionSource.THE_BATX.value,
    ProjectionSource.OOPSY.value,
]

UPDATED_PROJECTION_SYSTEMS = [
    ProjectionSource.UZIPS.value,
    ProjectionSource.STEAMER_U.value,
]

ROS_PROJECTION_SYSTEMS = [
    ProjectionSource.STEAMER_R.value,
    ProjectionSource.RZIPS.value,
    ProjectionSource.RZIPS_DC.value,
    ProjectionSource.RFANGRAPHS_DC.value,
    ProjectionSource.RATC_DC.value,
    ProjectionSource.RTHE_BAT.value,
    ProjectionSource.RTHE_BATX.value,
    ProjectionSource.ROOPSY_DC.value,
]

# Derived from the enum — add new sources to ProjectionSource above, not here
PROJECTION_SYSTEMS = [s.value for s in ProjectionSource]

# ---------------------------------------------------------------------------
# Default projection mixes
#
# Each player carries THREE independent projection blobs:
#   - projections: pre-season full-year forecast (the canonical mix — also the
#                  only one that exposes qq/tt percentile fields, via steamer
#                  at weight 0).
#   - updates:     full-year forecast refit with in-season data (only published
#                  during the season — empty pre-draft).
#   - ros:         rest-of-season forecast (only published during the season —
#                  empty pre-draft).
#
# All three fetches always run. Pre-draft mode naturally returns empty `updates`
# and `ros` because Fangraphs hasn't published those endpoints yet; they
# serialize as {} rather than null so downstream consumers see a stable shape.
#
# Pitchers use oopsy / roopsydc instead of thebatx / rthebatx (no batx pitcher
# data). Empirically only pre-season `steamer` emits qq/tt percentile fields
# — neither steameru nor steamerr emits them — so the steamer-at-weight-0
# trick only applies to DEFAULT_PROJECTIONS_*.
# ---------------------------------------------------------------------------

DEFAULT_PROJECTIONS_SOURCES = {
    "batters": [
        ProjectionSource.THE_BATX.value,
        ProjectionSource.DEPTH_CHARTS.value,
        ProjectionSource.ATC.value,
        ProjectionSource.STEAMER.value,
    ],
    "pitchers": [
        ProjectionSource.OOPSY.value,
        ProjectionSource.DEPTH_CHARTS.value,
        ProjectionSource.ATC.value,
        ProjectionSource.STEAMER.value,
    ],
}

DEFAULT_PROJECTIONS_WEIGHTS = {
    "batters": {
        ProjectionSource.THE_BATX.value: 0.50,
        ProjectionSource.DEPTH_CHARTS.value: 0.25,
        ProjectionSource.ATC.value: 0.25,
        ProjectionSource.STEAMER.value: 0.00,
    },
    "pitchers": {
        ProjectionSource.OOPSY.value: 0.50,
        ProjectionSource.DEPTH_CHARTS.value: 0.25,
        ProjectionSource.ATC.value: 0.25,
        ProjectionSource.STEAMER.value: 0.00,
    },
}

DEFAULT_UPDATES_SOURCES = {
    "batters": [
        ProjectionSource.UZIPS.value,
        ProjectionSource.STEAMER_U.value,
    ],
    "pitchers": [
        ProjectionSource.UZIPS.value,
        ProjectionSource.STEAMER_U.value,
    ],
}

DEFAULT_UPDATES_WEIGHTS = {
    # Equal-weight average across the two updated sources Fangraphs publishes.
    # Neither emits qq/tt percentile fields, so there's no point holding one at
    # weight 0 like the pre-season `projections` mix does.
    "batters": {
        ProjectionSource.UZIPS.value: 0.50,
        ProjectionSource.STEAMER_U.value: 0.50,
    },
    "pitchers": {
        ProjectionSource.UZIPS.value: 0.50,
        ProjectionSource.STEAMER_U.value: 0.50,
    },
}

DEFAULT_ROS_SOURCES = {
    "batters": [
        ProjectionSource.RTHE_BATX.value,
        ProjectionSource.RFANGRAPHS_DC.value,
        ProjectionSource.RATC_DC.value,
    ],
    "pitchers": [
        ProjectionSource.ROOPSY_DC.value,
        ProjectionSource.RFANGRAPHS_DC.value,
        ProjectionSource.RATC_DC.value,
    ],
}

DEFAULT_ROS_WEIGHTS = {
    "batters": {
        ProjectionSource.RTHE_BATX.value: 0.50,
        ProjectionSource.RFANGRAPHS_DC.value: 0.25,
        ProjectionSource.RATC_DC.value: 0.25,
    },
    "pitchers": {
        ProjectionSource.ROOPSY_DC.value: 0.50,
        ProjectionSource.RFANGRAPHS_DC.value: 0.25,
        ProjectionSource.RATC_DC.value: 0.25,
    },
}

BATTING_POSITIONS = [
    "all",
    "c",
    "1b",
    "2b",
    "3b",
    "ss",
    "lf",
    "cf",
    "rf",
    "of",
    "dh",
]
