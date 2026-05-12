from enum import Enum

FANGRAPHS_API_ENDPOINT = "https://www.fangraphs.com/api/projections?"

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

    Pre-season systems produce full-season forecasts and are available before/during the season.
    Rest-of-season (RoS) systems are updated mid-season and project only remaining games.

    Pitcher notes:
      - thebatx has no pitcher data; the fetch handler automatically maps it to thebat.
      - rthebatx has no pitcher data; the fetch handler automatically maps it to rthebat.
      - oopsy and roopsydc are valid for both hitters and pitchers.

    Add new sources here — PROJECTION_SYSTEMS is derived from this enum automatically.
    """

    # Pre-season projections
    STEAMER = "steamer"
    ZIPS = "zips"
    ZIPS_DC = "zipsdc"
    ATC = "atc"
    DEPTH_CHARTS = "fangraphsdc"
    THE_BAT = "thebat"
    THE_BATX = "thebatx"
    OOPSY = "oopsy"

    # Rest-of-season projections
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
# The app has two modes:
#   - In-season (default): DEFAULT_ROS_* — used for daily runs during the regular
#     season, the only time the underlying projections change day to day.
#   - Pre-draft (opt-in via --predraft): DEFAULT_PREDRAFT_* — used before the
#     draft / during the offseason, mirrors the RoS mix structure with
#     pre-season source equivalents.
#
# steamer/steamerr weight is always 0.0 in these mixes — it contributes only
# its qq/tt percentile fields (handled specially in weighted_average.py).
# Pitchers use oopsy/roopsydc instead of thebatx/rthebatx (no batx pitcher data).
# ---------------------------------------------------------------------------

DEFAULT_ROS_SOURCES = {
    "batters": [
        ProjectionSource.RTHE_BATX.value,
        ProjectionSource.RFANGRAPHS_DC.value,
        ProjectionSource.RATC_DC.value,
        ProjectionSource.STEAMER_R.value,
    ],
    "pitchers": [
        ProjectionSource.ROOPSY_DC.value,
        ProjectionSource.RFANGRAPHS_DC.value,
        ProjectionSource.RATC_DC.value,
        ProjectionSource.STEAMER_R.value,
    ],
}

DEFAULT_ROS_WEIGHTS = {
    "batters": {
        ProjectionSource.RTHE_BATX.value: 0.50,
        ProjectionSource.RFANGRAPHS_DC.value: 0.25,
        ProjectionSource.RATC_DC.value: 0.25,
        ProjectionSource.STEAMER_R.value: 0.00,
    },
    "pitchers": {
        ProjectionSource.ROOPSY_DC.value: 0.50,
        ProjectionSource.RFANGRAPHS_DC.value: 0.25,
        ProjectionSource.RATC_DC.value: 0.25,
        ProjectionSource.STEAMER_R.value: 0.00,
    },
}

DEFAULT_PREDRAFT_SOURCES = {
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

DEFAULT_PREDRAFT_WEIGHTS = {
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
