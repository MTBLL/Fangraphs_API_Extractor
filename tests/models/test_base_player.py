"""Tests for base_player.py to achieve 100% coverage."""

import pytest

from fangraphs_api_extractor.models import (
    HitterATCProjectionModel,
    HitterModel,
    HitterProjectionModel,
    HitterTHEBATProjectionModel,
    PitcherATCProjectionModel,
    PitcherModel,
    PitcherProjectionModel,
    PitcherTHEBATProjectionModel,
    PlayerModel,
)

def test_parse_player_pitcher_atc():
    """Test parse_player with pitcher data and ATC projection system."""
    data = {
        "Team": "LAD",
        "playerid": "12345",
        "PlayerName": "Test Pitcher",
        "xMLBAMID": 123456,
        "teamid": 10,
        "W": 10,
        "L": 5,
        "ERA": 3.50,
        "IP": 150.0,
    }

    player = PlayerModel.parse_player(data, projection_source="atc")

    assert isinstance(player, PitcherModel)
    assert isinstance(player.projections, PitcherATCProjectionModel)


def test_parse_player_pitcher_the_bat():
    """Test parse_player with pitcher data and THE_BAT projection system."""
    data = {
        "Team": "LAD",
        "playerid": "12345",
        "PlayerName": "Test Pitcher",
        "xMLBAMID": 123456,
        "teamid": 10,
        "W": 10,
        "L": 5,
        "ERA": 3.50,
        "IP": 150.0,
    }

    player = PlayerModel.parse_player(data, projection_source="thebat")

    assert isinstance(player, PitcherModel)
    assert isinstance(player.projections, PitcherTHEBATProjectionModel)


def test_parse_player_pitcher_generic():
    """Test parse_player with pitcher data and unknown projection system."""
    data = {
        "Team": "LAD",
        "playerid": "12345",
        "PlayerName": "Test Pitcher",
        "xMLBAMID": 123456,
        "teamid": 10,
        "W": 10,
        "L": 5,
        "ERA": 3.50,
        "IP": 150.0,
    }

    player = PlayerModel.parse_player(data, projection_source="unknown_system")

    assert isinstance(player, PitcherModel)
    assert isinstance(player.projections, PitcherProjectionModel)


def test_parse_player_hitter_atc():
    """Test parse_player with hitter data and ATC projection system."""
    data = {
        "Team": "NYY",
        "playerid": "15640",
        "PlayerName": "Aaron Judge",
        "xMLBAMID": 592450,
        "teamid": 9,
        "AB": 500,
        "PA": 550,
        "RBI": 100,
    }

    player = PlayerModel.parse_player(data, projection_source="atc")

    assert isinstance(player, HitterModel)
    assert isinstance(player.projections, HitterATCProjectionModel)


def test_parse_player_hitter_the_bat():
    """Test parse_player with hitter data and THE_BAT projection system."""
    data = {
        "Team": "NYY",
        "playerid": "15640",
        "PlayerName": "Aaron Judge",
        "xMLBAMID": 592450,
        "teamid": 9,
        "AB": 500,
        "PA": 550,
        "RBI": 100,
    }

    player = PlayerModel.parse_player(data, projection_source="thebat")

    assert isinstance(player, HitterModel)
    assert isinstance(player.projections, HitterTHEBATProjectionModel)


def test_parse_player_hitter_generic():
    """Test parse_player with hitter data and unknown projection system."""
    data = {
        "Team": "NYY",
        "playerid": "15640",
        "PlayerName": "Aaron Judge",
        "xMLBAMID": 592450,
        "teamid": 9,
        "AB": 500,
        "PA": 550,
        "RBI": 100,
    }

    player = PlayerModel.parse_player(data, projection_source="zips")

    assert isinstance(player, HitterModel)
    assert isinstance(player.projections, HitterProjectionModel)


def test_parse_player_unknown_type():
    """Test parse_player with data that doesn't match hitter or pitcher."""
    data = {
        "Team": "NYY",
        "playerid": "15640",
        "PlayerName": "Unknown Player",
        "xMLBAMID": 592450,
        "teamid": 9,
        # Missing stats that would identify player type
    }

    with pytest.raises(ValueError, match="Unknown player type from data"):
        PlayerModel.parse_player(data)
