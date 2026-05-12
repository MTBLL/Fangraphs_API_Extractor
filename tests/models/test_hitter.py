"""
Tests for the hitter models.
"""

import json
import os

import pytest

from fangraphs_api_extractor.models import (
    HitterModel,
    HitterSteamerProjectionModel,
    PlayerModel,
)


@pytest.fixture
def hitter_steamer_data():
    """Load hitter data from Steamer projections."""
    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "fixtures", "hitter_steamer.json"
    )
    with open(fixture_path, "r") as f:
        return json.load(f)


def test_hitter_basic_parsing(hitter_steamer_data):
    """Test the basic parsing of hitter data from a single projection source."""
    # Parse the player data (select first player from fixture list)
    player = PlayerModel.parse_player(hitter_steamer_data[0], projection_source="steamer")

    # Test basic player identification
    assert isinstance(player, HitterModel)
    assert player.name == "Aaron Judge"
    assert player.team == "NYY"
    assert player.playerid == "15640"
    assert player.xmlbam_id == 592450
    assert "stats.json" in player.stats_api

    # Test that we have the projection
    assert isinstance(player.projections, HitterSteamerProjectionModel)

    # Test some basic projection data
    proj = player.projections
    assert proj.hr == 43  # Integer conversion from 42.7926
    assert proj.h == 146  # Integer conversion from 145.548
    assert proj.pa == 634.656
    assert proj.avg == 0.285498
    assert pytest.approx(proj.war) == 6.83793
    assert proj.wrc_plus == 171.745

    # Test some derived stats
    assert proj.obp == 0.417443
    assert proj.k_percent == 0.245
    assert proj.bb_percent == 0.177

    # Check that percentiles were captured
    assert proj.q50 == 0.415
    assert proj.tt_q50 == 0.416
