"""
Test that null Team values are properly handled in player models.
"""

import json
import os

from fangraphs_api_extractor.managers.players_manager import parse_players
from fangraphs_api_extractor.models.base_player import PlayerModel
from fangraphs_api_extractor.utils import Logger


def test_null_team_sets_free_agent():
    """Test that a null Team value in the JSON is processed as 'FA' in the player model."""
    # Path to the fixture with a player that has a null Team value
    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "hitter_projections.json",
    )

    # Load the test data
    with open(fixture_path, "r") as f:
        test_data = json.load(f)

    # Parse the players
    players = parse_players(test_data, Logger("test"))

    # Find a player with null Team in the fixture
    # Whit Merrifield in the fixture has Team: null
    null_team_player = None
    for player in players:
        if player.name == "Whit Merrifield":
            null_team_player = player
            break

    # Assert that we found the player
    assert null_team_player is not None, (
        "Could not find Whit Merrifield in parsed players"
    )

    # Assert that the player's team is set to 'FA' instead of None
    assert null_team_player.team == "FA", (
        f"Expected team 'FA', got '{null_team_player.team}'"
    )


def test_direct_model_validation_with_null_values():
    """Test that Pydantic model validation directly handles null values."""
    # Test data with null values
    test_data = {
        "Team": None,
        "playerid": "12345",
        "PlayerName": "Test Player",
        "xMLBAMID": None,  # Null xMLBAMID
        "teamid": None,  # Null teamid
    }

    # Create a player model directly
    player = PlayerModel.model_validate(test_data)

    # Check that the values are set correctly
    assert player.team == "FA", f"Expected team 'FA', got '{player.team}'"
    assert player.xmlbam_id == -1, f"Expected xmlbam_id -1, got '{player.xmlbam_id}'"
    assert player.team_id == -1, f"Expected team_id -1, got '{player.team_id}'"


def test_player_parse_method_with_null_values():
    """Test that the parse_player factory method handles null values."""
    # Minimum test data with null values to parse a player
    test_data = {
        "Team": None,
        "playerid": "12345",
        "PlayerName": "Test Player",
        "xMLBAMID": None,  # Null xMLBAMID
        "teamid": None,  # Null teamid
        # Hitter-specific fields to ensure it's parsed as a hitter
        "AB": 500,
        "PA": 550,
        "RBI": 80,
        "HR": 20,
    }

    # Use the factory method to parse the player
    player = PlayerModel.parse_player(test_data)

    # Check that the values are set correctly
    assert player.team == "FA", f"Expected team 'FA', got '{player.team}'"
    assert player.xmlbam_id == -1, f"Expected xmlbam_id -1, got '{player.xmlbam_id}'"
    assert player.team_id == -1, f"Expected team_id -1, got '{player.team_id}'"
