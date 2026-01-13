"""Additional tests for PlayersManager to cover untested paths."""

from fangraphs_api_extractor.managers import PlayersManager


def test_parse_players_with_list():
    """Test parsing players from a direct list."""
    data = [
        {
            "Team": "NYY",
            "playerid": "15640",
            "PlayerName": "Aaron Judge",
            "xMLBAMID": 592450,
            "teamid": 9,
            "AB": 500,
            "PA": 550,
            "RBI": 100,
        }
    ]

    manager = PlayersManager("hitters")
    players = manager.parse_players(data)

    assert len(players) == 1
    assert players[0].name == "Aaron Judge"


def test_parse_players_with_single_player():
    """Test parsing a single player dictionary."""
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

    manager = PlayersManager("hitters")
    players = manager.parse_players(data)

    assert len(players) == 1
    assert players[0].name == "Aaron Judge"


def test_parse_players_with_invalid_format():
    """Test parsing with unrecognized format returns empty list."""
    data = {"invalid": "format", "no": "pageProps"}

    manager = PlayersManager("hitters")
    players = manager.parse_players(data)

    # Should return empty list when unable to parse
    assert players == []


def test_parse_players_with_invalid_player_data():
    """Test parsing with invalid player data in list."""
    data = [
        {
            "Team": "NYY",
            "playerid": "15640",
            "PlayerName": "Aaron Judge",
            "xMLBAMID": 592450,
            "teamid": 9,
            "AB": 500,
            "PA": 550,
            "RBI": 100,
        },
        {
            # Missing required fields - should be skipped
            "invalid": "data",
        },
    ]

    manager = PlayersManager("hitters")
    players = manager.parse_players(data)

    # Should only parse the valid player
    assert len(players) == 1
    assert players[0].name == "Aaron Judge"


def test_parse_players_pitcher():
    """Test parsing pitcher data."""
    data = [
        {
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
    ]

    manager = PlayersManager("pitchers")
    players = manager.parse_players(data)

    assert len(players) == 1
    assert players[0].name == "Test Pitcher"


def test_parse_players_empty_list():
    """Test parsing empty list."""
    data: list[dict] = []

    manager = PlayersManager("hitters")
    players = manager.parse_players(data)

    assert players == []


def test_manager_initialization():
    """Test manager initialization with different player groups."""
    hitters_manager = PlayersManager("hitters")
    assert hitters_manager.logger is not None
    assert hitters_manager.log is not None
    assert hitters_manager.players == []

    pitchers_manager = PlayersManager("pitchers")
    assert pitchers_manager.logger is not None
    assert pitchers_manager.players == []


def test_parse_players_with_nested_structure_error():
    """Test parsing with nested structure that has invalid API structure."""
    # This should trigger the KeyError/IndexError exception handling
    data: dict = {
        "pageProps": {
            "dehydratedState": {
                "queries": []  # Empty list will cause IndexError
            }
        }
    }

    manager = PlayersManager("hitters")

    # Exception is caught and logged, returns empty list
    players = manager.parse_players(data)
    assert players == []


def test_parse_single_player_with_error():
    """Test parsing single player that raises exception."""
    # Invalid player data that will fail validation
    data = {
        "PlayerName": "Test Player",
        # Missing required fields like team, playerid, etc.
    }

    manager = PlayersManager("hitters")
    players = manager.parse_players(data)

    # Should handle the error and return empty list
    assert players == []


def test_parse_nested_with_pageprops_debug():
    """Test parsing with pageProps structure to trigger debug logging."""
    # Create data that will fail but has pageProps key for debug logging
    data = {
        "pageProps": {
            "wrongKey": "value"  # Missing expected structure
        }
    }

    manager = PlayersManager("hitters")

    # Should catch exception, log debug info about pageProps, and return empty list
    players = manager.parse_players(data)
    assert players == []


def test_parse_nested_player_with_individual_error():
    """Test parsing nested data where one player fails but others succeed."""
    # Create a list with valid and invalid players
    test_data = [
        {
            "Team": "NYY",
            "playerid": "15640",
            "PlayerName": "Aaron Judge",
            "xMLBAMID": 592450,
            "teamid": 9,
            "AB": 500,
            "PA": 550,
            "RBI": 100,
        },
        {
            # Invalid player (missing required fields)
            "InvalidKey": "InvalidValue"
        },
        {
            "Team": "LAD",
            "playerid": "12345",
            "PlayerName": "Valid Player",
            "xMLBAMID": 123456,
            "teamid": 10,
            "AB": 450,
            "PA": 500,
            "RBI": 80,
        },
    ]

    manager = PlayersManager("hitters")
    players = manager.parse_players(test_data)

    # Should parse 2 valid players and skip the invalid one
    # The invalid player triggers the exception warning in lines 43-45
    assert len(players) == 2
    assert "Aaron Judge" in [p.name for p in players]
    assert "Valid Player" in [p.name for p in players]


def test_parse_nested_with_pageprops_keyerror():
    """Test to trigger the pageProps debug logging path (line 59-60)."""
    # Create data with pageProps but missing nested keys to trigger KeyError
    data: dict = {
        "pageProps": {
            "dehydratedState": {
                "queries": [
                    {
                        "state": {
                            "missing_data_key": []  # This will cause KeyError when accessing "data"
                        }
                    }
                ]
            }
        }
    }

    manager = PlayersManager("hitters")

    # Should catch KeyError, log pageProps debug info, and return empty list
    players = manager.parse_players(data)
    assert players == []
