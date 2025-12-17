"""
Test that null Team values are properly handled in player models.
"""

from fangraphs_api_extractor.managers import PlayersManager
from fangraphs_api_extractor.models.base_player import PlayerModel


def test_null_team_sets_free_agent():
    """Test that a null Team value in the JSON is processed as 'FA' in the player model."""
    # Create mock data with null team
    test_data = [
        {
            "Team": None,  # Null team (free agent)
            "playerid": "12345",
            "PlayerName": "Free Agent Player",
            "xMLBAMID": 123456,
            "teamid": -1,
            "AB": 400,
            "PA": 450,
            "RBI": 50,
        }
    ]

    # Parse the players
    players = PlayersManager("test").parse_players(test_data)

    # Assert that we got one player
    assert len(players) == 1

    null_team_player = players[0]

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
