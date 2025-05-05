"""
Tests for the player manager functionality.
"""

import json
import os
from typing import Dict

import pytest

from fangraphs_api_extractor.managers.players_manager import parse_players
from fangraphs_api_extractor.models import HitterModel, HitterSteamerProjectionModel


@pytest.fixture
def hitter_projections_data() -> Dict:
    """Load multiple hitter projection data from fixture."""
    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "hitter_projections.json",
    )
    with open(fixture_path, "r") as f:
        return json.load(f)


def test_parse_players(hitter_projections_data):
    """Test parsing multiple players from the API response structure."""
    # Parse the player data using the manager function
    players = parse_players(hitter_projections_data)

    # Test basic assertions about the returned data
    assert players is not None
    assert isinstance(players, list)
    assert len(players) > 0  # We should have at least one player

    # Check that all returned objects are HitterModel instances
    for player in players:
        assert isinstance(player, HitterModel)

    # Test specific player data if we know what to expect
    # For example, if we know the fixture contains Bobby Witt Jr and Corbin Carroll
    player_names = [player.name for player in players]
    assert len(player_names) == 2  # The fixture contains 2 players

    # Check for specific data in the first player
    first_player = players[0]
    assert first_player.team == "KCR"  # Kansas City Royals
    assert "steamer" in first_player.projections

    # Check specific projection data
    proj = first_player.projections["steamer"]
    assert isinstance(proj, HitterSteamerProjectionModel)
    assert proj.pa > 0
    assert proj.hr > 0
    assert 0 < proj.avg < 1  # Batting average should be between 0 and 1

    # Check that the slug property is working
    assert first_player.slug == first_player.name.lower().replace(".", "").replace(
        " ", "-"
    )

    # Check that the stats_api property is working
    if first_player.upurl:
        assert "stats.json" in first_player.stats_api
        assert first_player.stats_api != first_player.upurl  # Should be transformed
