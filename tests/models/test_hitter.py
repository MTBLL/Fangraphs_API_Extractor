"""
Tests for the hitter models.
"""
import json
import os
import pytest
from fangraphs_api_extractor.models import (
    PlayerModel,
    HitterModel,
    HitterProjectionModel,
    HitterSteamerProjectionModel
)


@pytest.fixture
def hitter_steamer_data():
    """Load hitter data from Steamer projections."""
    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "hitter_steamer.json"
    )
    with open(fixture_path, "r") as f:
        return json.load(f)


def test_hitter_basic_parsing(hitter_steamer_data):
    """Test the basic parsing of hitter data from a single projection source."""
    # Parse the player data
    player = PlayerModel.parse_player(hitter_steamer_data, projection_source="steamer")
    
    # Test basic player identification
    assert isinstance(player, HitterModel)
    assert player.player_name == "Corbin Carroll"
    assert player.team == "ARI"
    assert player.league == "NL"
    assert player.player_id == "25878"
    assert player.xmlbam_id == 682998
    
    # Test that we have the projection source
    assert "steamer" in player.projections
    assert isinstance(player.projections["steamer"], HitterSteamerProjectionModel)
    
    # Test some basic projection data
    proj = player.projections["steamer"]
    assert proj.hr == 25.3512
    assert proj.pa == 657.643
    assert proj.avg == 0.264213
    assert pytest.approx(proj.war) == 4.69297
    assert proj.wrc_plus == 128.79
    
    # Test some derived stats
    assert proj.obp == 0.351206
    assert proj.k_percent == 0.18463
    assert proj.bb_percent == 0.105
    
    # Check that percentiles were captured
    assert proj.q50 == 0.357
    assert proj.tt_q50 == 0.357