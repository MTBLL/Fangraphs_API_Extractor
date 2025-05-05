"""
Tests for the pitcher models.
"""
import json
import os
import pytest
from fangraphs_api_extractor.models import (
    PlayerModel,
    PitcherModel,
    PitcherProjectionModel,
    PitcherSteamerProjectionModel
)


@pytest.fixture
def pitcher_steamer_data():
    """Load pitcher data from Steamer projections."""
    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "pitcher_steamer.json"
    )
    with open(fixture_path, "r") as f:
        return json.load(f)


def test_pitcher_basic_parsing(pitcher_steamer_data):
    """Test the basic parsing of pitcher data from a single projection source."""
    # Parse the player data
    player = PlayerModel.parse_player(pitcher_steamer_data, projection_source="steamer")
    
    # Test basic player identification
    assert isinstance(player, PitcherModel)
    assert player.player_name == "Paul Skenes"
    assert player.team == "PIT"
    assert player.league == "NL"
    assert player.player_id == "33677"
    assert player.xmlbam_id == 694973
    
    # Test that we have the projection source
    assert "steamer" in player.projections
    assert isinstance(player.projections["steamer"], PitcherSteamerProjectionModel)
    
    # Test some basic projection data
    proj = player.projections["steamer"]
    assert proj.wins == 13.1876
    assert proj.losses == 8.6522
    assert proj.innings_pitched == 188.104
    assert proj.strikeouts == 241.243
    assert proj.era == 2.79206
    assert proj.whip == 1.07518
    
    # Test some derived stats
    assert proj.k_per_9 == 11.5424
    assert proj.bb_per_9 == 2.64692
    assert proj.k_per_bb == 4.3607
    assert proj.k_percent == 0.31793
    
    # Check pitching specific stats
    assert proj.fip == 2.67841
    assert proj.quality_starts == 21.1326
    assert pytest.approx(proj.lob_percent) == 0.762926
    
    # Check that percentiles were captured
    assert proj.q50 == 2.98
    assert proj.tt_q50 == 3.05