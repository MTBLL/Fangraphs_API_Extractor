BUILD_ID = "JnNS4pK_PHEa_Wk1StnE0"
FANGRAPHS_CORE_BUILD_ENDPOINT = "https://www.fangraphs.com/_next/data/" + BUILD_ID
FANGRAPHS_PROJECTIONS_ENDPOINT = FANGRAPHS_CORE_BUILD_ENDPOINT + "/projections.json"

# Requests
USER_AGENT_HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

PROJECTION_SYSTEMS = ["streamer", "zips", "zipsdc", "atc"]
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
