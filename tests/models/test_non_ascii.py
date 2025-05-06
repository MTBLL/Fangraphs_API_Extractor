"""
Tests for handling non-ASCII characters in player names.
"""

import json
import os

import pytest

from fangraphs_api_extractor.models import PlayerModel
from fangraphs_api_extractor.utils.utils import normalize_string


@pytest.fixture
def hitter_projections_data():
    """Load hitter projections data that includes players with non-ASCII characters."""
    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "fixtures", "hitter_projections.json"
    )
    with open(fixture_path, "r") as f:
        data = json.load(f)
        # Get the 4th player (Julio Rodríguez) from the fixture data
        return data["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"][3]


def test_non_ascii_name_handling(hitter_projections_data):
    """Test that names with non-ASCII characters are handled properly."""
    # Parse the player data
    player = PlayerModel.parse_player(hitter_projections_data, projection_source="steamer")

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