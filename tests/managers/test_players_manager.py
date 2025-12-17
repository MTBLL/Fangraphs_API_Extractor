"""
Tests for the player manager functionality.
"""

import pytest

from fangraphs_api_extractor.managers import PlayersManager
from fangraphs_api_extractor.models import HitterModel


@pytest.fixture
def hitter_projections_data() -> list:
    """Create mock hitter projection data."""
    return [
        {
            "Team": "NYY",
            "playerid": "15640",
            "PlayerName": "Aaron Judge",
            "xMLBAMID": 592450,
            "teamid": 9,
            "minpos": "OF",
            "UPURL": "/players/aaron-judge/15640/stats?position=OF",
            "AB": 500,
            "PA": 550,
            "RBI": 100,
            "HR": 30,
            "AVG": 0.300,
        },
        {
            "Team": "KCR",
            "playerid": "25764",
            "PlayerName": "Bobby Witt Jr.",
            "xMLBAMID": 677951,
            "teamid": 7,
            "minpos": "SS",
            "UPURL": "/players/bobby-witt-jr/25764/stats?position=SS",
            "AB": 600,
            "PA": 650,
            "RBI": 90,
            "HR": 25,
            "AVG": 0.290,
        },
        {
            "Team": "SEA",
            "playerid": "30001",
            "PlayerName": "Julio Rodríguez",
            "xMLBAMID": 677594,
            "teamid": 11,
            "minpos": "OF",
            "AB": 580,
            "PA": 630,
            "RBI": 85,
            "HR": 28,
            "AVG": 0.285,
        },
    ]


def test_parse_players(hitter_projections_data):
    """Test parsing multiple players from the API response structure."""
    # Parse the player data using the manager function
    players = PlayersManager("test").parse_players(hitter_projections_data)

    # Test basic assertions about the returned data
    assert players is not None
    assert isinstance(players, list)
    assert len(players) == 3  # We have 3 mock players

    # Check that all returned objects are HitterModel instances
    for player in players:
        assert isinstance(player, HitterModel)

    # Test specific player data
    player_names = [player.name for player in players]
    assert "Aaron Judge" in player_names
    assert "Bobby Witt Jr." in player_names
    assert "Julio Rodríguez" in player_names  # Check for player with non-ASCII name

    # Check for specific data in the first player (Aaron Judge)
    first_player = players[0]
    assert first_player.team == "NYY"
    assert first_player.name == "Aaron Judge"
    assert first_player.playerid == "15640"

    # Check that the slug property is working with UPURL
    aaron_judge = next(p for p in players if p.name == "Aaron Judge")
    assert aaron_judge.slug == "aaron-judge"  # Extracted from UPURL

    bobby_witt = next(p for p in players if p.name == "Bobby Witt Jr.")
    assert bobby_witt.slug == "bobby-witt-jr"  # Extracted from UPURL

    # Check that the stats_api property is working
    if aaron_judge.upurl:
        assert "stats.json" in aaron_judge.stats_api
        assert aaron_judge.stats_api != aaron_judge.upurl  # Should be transformed
