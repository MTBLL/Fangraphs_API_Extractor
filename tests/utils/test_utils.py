"""Tests for utility functions."""

import json
import os
import tempfile

import pytest

from fangraphs_api_extractor.models import HitterModel
from fangraphs_api_extractor.utils.utils import (
    get_nested_values,
    save_extraction_results,
    serialize_players,
)


@pytest.fixture
def sample_hitter():
    """Create a sample hitter for testing."""
    data = {
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
    }
    return HitterModel.model_validate(data)


def test_serialize_players_single(sample_hitter):
    """Test serializing a single player."""
    players = [sample_hitter]
    result = serialize_players(players)

    assert len(result) == 1
    assert result[0]["name"] == "Aaron Judge"
    assert result[0]["team"] == "NYY"
    assert result[0]["playerid"] == "15640"
    assert result[0]["slug"] == "aaron-judge"
    assert "projection" in result[0]
    assert result[0]["projection"] == {}


def test_serialize_players_multiple(sample_hitter):
    """Test serializing multiple players."""
    players = [sample_hitter, sample_hitter]
    result = serialize_players(players)

    assert len(result) == 2
    assert all(p["name"] == "Aaron Judge" for p in result)


def test_serialize_players_empty():
    """Test serializing empty list."""
    result = serialize_players([])
    assert result == []


def test_serialize_players_with_projection(sample_hitter):
    """Test that projection data is included in serialization."""
    # Add a projection
    from fangraphs_api_extractor.models import HitterSteamerProjectionModel

    proj_data = {
        "Season": "2025",
        "PA": 550,
        "AB": 500,
        "HR": 30,
        "AVG": 0.300,
    }
    sample_hitter.projection = HitterSteamerProjectionModel.model_validate(proj_data)

    result = serialize_players([sample_hitter])

    assert "projection" in result[0]
    # Check that projection data was serialized with aliases (field name is uppercase 'HR')
    assert result[0]["projection"]["HR"] == 30


def test_save_extraction_results_from_fixtures(single_pitcher, single_hitter):
    """Test saving extraction results using real fixture data."""
    timestamp = "20250101_010203"

    with tempfile.TemporaryDirectory() as tmpdir:
        save_extraction_results(
            pitchers=[single_pitcher],
            batters=[single_hitter],
            output_dir=tmpdir,
            year=2025,
            timestamp=timestamp,
        )

        pitcher_path = os.path.join(
            tmpdir, f"fangraph_pitchers_2025_{timestamp}.json"
        )
        batter_path = os.path.join(
            tmpdir, f"fangraph_batters_2025_{timestamp}.json"
        )

        assert os.path.exists(pitcher_path)
        assert os.path.exists(batter_path)

        with open(pitcher_path, "r") as f:
            pitcher_output = json.load(f)
        with open(batter_path, "r") as f:
            batter_output = json.load(f)

        assert len(pitcher_output) == 1
        assert len(batter_output) == 1
        assert "projection" in pitcher_output[0]
        assert "projection" in batter_output[0]


def test_save_extraction_results_write_errors(
    single_pitcher, single_hitter, monkeypatch, tmp_path
):
    """Test save_extraction_results handles write errors gracefully."""

    def fail_open(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("builtins.open", fail_open)

    save_extraction_results(
        pitchers=[single_pitcher],
        batters=[single_hitter],
        output_dir=str(tmp_path),
        year=2025,
        timestamp="20250101_010203",
    )

    pitcher_path = tmp_path / "fangraph_pitchers_2025_20250101_010203.json"
    batter_path = tmp_path / "fangraph_batters_2025_20250101_010203.json"

    assert not pitcher_path.exists()
    assert not batter_path.exists()


def test_get_nested_values_simple():
    """Test getting nested values from simple dict."""
    data = {"a": {"b": {"c": "value"}}}
    result = get_nested_values(data, ["a", "b", "c"])
    assert result == "value"


def test_get_nested_values_with_list():
    """Test getting nested values with list index."""
    data = {"items": [{"name": "first"}, {"name": "second"}]}
    result = get_nested_values(data, ["items", 1, "name"])
    assert result == "second"


def test_get_nested_values_mixed():
    """Test getting nested values with mixed dict and list."""
    data = {
        "level1": {
            "level2": [
                {"id": 1, "value": "first"},
                {"id": 2, "value": "second"},
            ]
        }
    }
    result = get_nested_values(data, ["level1", "level2", 0, "value"])
    assert result == "first"


def test_get_nested_values_missing_key():
    """Test getting nested values with missing key returns None."""
    data = {"a": {"b": "value"}}
    # When key 'c' is missing, get returns None, then trying to access 'd' on None raises AssertionError
    result = get_nested_values(data, ["a", "c"])
    assert result is None


def test_get_nested_values_invalid_path():
    """Test getting nested values with invalid path type."""
    data = {"a": {"b": "value"}}

    with pytest.raises(AssertionError):
        # Trying to access dict key on a string value
        get_nested_values(data, ["a", "b", "c"])


def test_serialize_players_with_missing_attributes():
    """Test serialization handles players with missing optional attributes."""
    # Create a minimal player without optional fields
    data = {
        "Team": "FA",
        "playerid": "12345",
        "PlayerName": "Test Player",
        "xMLBAMID": -1,
        "teamid": -1,
        "AB": 100,
        "PA": 110,
        "RBI": 10,
    }
    player = HitterModel.model_validate(data)

    result = serialize_players([player])

    assert len(result) == 1
    assert result[0]["name"] == "Test Player"
    assert result[0]["team"] == "FA"
    assert result[0]["xmlbam_id"] == -1


def test_serialize_players_with_projection_error():
    """Test serialization when projection processing fails."""
    from unittest.mock import MagicMock

    # Create a player with a projection that will fail to serialize
    player = MagicMock()
    player.name = "Test Player"
    player.ascii_name = "Test Player"
    player.team = "NYY"
    player.playerid = "12345"
    player.xmlbam_id = 123456
    player.slug = "test-player"
    player.stats_api = "/players/test-player/12345/stats.json"

    # Create a projection that will raise an exception
    bad_projection = MagicMock()
    bad_projection.model_dump.side_effect = Exception("Projection serialization error")
    player.projection = bad_projection

    result = serialize_players([player])

    # Should still serialize the player with empty projection
    assert len(result) == 1
    assert result[0]["name"] == "Test Player"
    assert result[0]["projection"] == {}


def test_serialize_players_with_player_error():
    """Test serialization when player processing completely fails."""

    # Create a player that has a name but raises exception on projection access
    class BadPlayer:
        name = "Error Player"

        @property
        def projection(self):
            raise RuntimeError("Cannot access projection")

    result = serialize_players([BadPlayer()])  # type: ignore[list-item]

    # Should add player with error info from exception handler
    assert len(result) == 1
    assert "error" in result[0]
    assert result[0]["name"] == "Error Player"
