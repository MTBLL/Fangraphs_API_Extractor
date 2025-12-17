"""
Tests for handling non-ASCII characters in player names.
"""

import pytest

from fangraphs_api_extractor.models import PlayerModel
from fangraphs_api_extractor.utils.utils import normalize_string


@pytest.fixture
def hitter_projections_data():
    """Create mock hitter data with non-ASCII characters."""
    return {
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
    }


def test_non_ascii_name_handling(hitter_projections_data):
    """Test that names with non-ASCII characters are handled properly."""
    # Parse the player data
    player = PlayerModel.parse_player(
        hitter_projections_data, projection_source="steamer"
    )

    # Test that the original name is preserved with accents
    assert player.name == "Julio Rodríguez"

    # Test that the ASCII name property removes accents
    assert player.ascii_name == "Julio Rodriguez"

    # Test that the slug properly handles the non-ASCII character
    assert player.slug == "julio-rodriguez"

    # Test that the stats_api URL is properly formed with ASCII-only characters
    assert "/players/julio-rodriguez/" in player.stats_api
    assert "stats.json" in player.stats_api


def test_normalize_string_function():
    """Test the normalize_string utility function."""
    # Test various non-ASCII characters
    assert normalize_string("Julio Rodríguez") == "Julio Rodriguez"
    assert normalize_string("José Ramírez") == "Jose Ramirez"
    assert normalize_string("Shōhei Ohtani") == "Shohei Ohtani"
    assert normalize_string("Max Müller") == "Max Muller"
    assert normalize_string("François Pérez") == "Francois Perez"

    # Test with strings that are already ASCII-only
    assert normalize_string("Mike Trout") == "Mike Trout"
    assert normalize_string("Bryce Harper") == "Bryce Harper"
