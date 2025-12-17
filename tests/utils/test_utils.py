"""Tests for utility functions."""

import json
import os
import tempfile

import pytest

from fangraphs_api_extractor.models import HitterModel
from fangraphs_api_extractor.utils.utils import (
    get_nested_values,
    serialize_players,
    write_json_file,
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
    assert "projections" in result[0]


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


def test_serialize_players_with_projections(sample_hitter):
    """Test that projections are included in serialization."""
    # Add a projection
    from fangraphs_api_extractor.models import HitterSteamerProjectionModel

    proj_data = {
        "Season": "2025",
        "PA": 550,
        "AB": 500,
        "HR": 30,
        "AVG": 0.300,
    }
    sample_hitter.projections["steamer"] = HitterSteamerProjectionModel.model_validate(
        proj_data
    )

    result = serialize_players([sample_hitter])

    assert "projections" in result[0]
    assert "steamer" in result[0]["projections"]
    # Check that projection data was serialized (field name is lowercase 'hr')
    assert result[0]["projections"]["steamer"]["hr"] == 30


def test_write_json_file():
    """Test writing JSON file."""
    data = [{"name": "Test Player", "team": "NYY"}]

    with tempfile.TemporaryDirectory() as tmpdir:
        write_json_file(data, tmpdir, "test_output.json")

        # Verify file was created
        output_path = os.path.join(tmpdir, "test_output.json")
        assert os.path.exists(output_path)

        # Verify content
        with open(output_path, "r") as f:
            loaded_data = json.load(f)

        assert loaded_data == data


def test_write_json_file_creates_directory():
    """Test that write_json_file creates directories if they don't exist."""
    data = [{"name": "Test Player"}]

    with tempfile.TemporaryDirectory() as tmpdir:
        nested_dir = os.path.join(tmpdir, "nested", "dir")
        write_json_file(data, nested_dir, "test.json")

        # Verify file was created in nested directory
        output_path = os.path.join(nested_dir, "test.json")
        assert os.path.exists(output_path)


def test_write_json_file_with_indent():
    """Test writing JSON file with custom indentation."""
    data = [{"name": "Test", "nested": {"key": "value"}}]

    with tempfile.TemporaryDirectory() as tmpdir:
        write_json_file(data, tmpdir, "test.json", indent=4)

        output_path = os.path.join(tmpdir, "test.json")
        with open(output_path, "r") as f:
            content = f.read()

        # Verify indentation (4 spaces)
        assert "    " in content


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
    player.projections = {"bad_proj": bad_projection}

    result = serialize_players([player])

    # Should still serialize the player with empty projections
    assert len(result) == 1
    assert result[0]["name"] == "Test Player"
    assert result[0]["projections"] == {}


def test_serialize_players_with_player_error():
    """Test serialization when player processing completely fails."""

    # Create a player that has a name but raises exception on projections access
    class BadPlayer:
        name = "Error Player"

        @property
        def projections(self):
            raise RuntimeError("Cannot access projections")

    result = serialize_players([BadPlayer()])  # type: ignore[list-item]

    # Should add player with error info from exception handler
    assert len(result) == 1
    assert "error" in result[0]
    assert result[0]["name"] == "Error Player"


def test_write_json_file_with_error():
    """Test write_json_file when file writing fails."""
    import tempfile
    from unittest.mock import patch

    data = [{"name": "Test"}]

    with tempfile.TemporaryDirectory() as tmpdir:
        # Try to write to a read-only directory (simulate write error)
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Should log error but not raise exception
            write_json_file(data, tmpdir, "test.json")
            # Test passes if no exception is raised
