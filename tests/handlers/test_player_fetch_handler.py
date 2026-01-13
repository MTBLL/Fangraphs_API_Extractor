"""Tests for PlayerFetchHandler."""

from unittest.mock import MagicMock

import pytest

from fangraphs_api_extractor.handlers import PlayerFetchHandler
from fangraphs_api_extractor.models import HitterModel, PitcherModel
from fangraphs_api_extractor.requests.core_fangraphs import CoreFangraphs


@pytest.fixture
def mock_core_fangraphs():
    """Create a mock CoreFangraphs instance."""
    mock = MagicMock(spec=CoreFangraphs)
    mock.year = 2025
    return mock


@pytest.fixture
def hitter_fixture_data():
    """Create mock hitter fixture data."""
    return [
        {
            "Team": "NYY",
            "playerid": "15640",
            "PlayerName": "Aaron Judge",
            "xMLBAMID": 592450,
            "teamid": 9,
            "AB": 500,
            "PA": 550,
            "RBI": 100,
            "HR": 30,
            "AVG": 0.300,
        },
        {
            "Team": "KCR",
            "playerid": "25764",
            "PlayerName": "Bobby Witt Jr.",
            "xMLBAMID": 677951,
            "teamid": 7,
            "AB": 600,
            "PA": 650,
            "RBI": 90,
            "HR": 25,
            "AVG": 0.290,
        },
    ]


@pytest.fixture
def pitcher_fixture_data():
    """Create mock pitcher fixture data."""
    return [
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


def test_fetch_hitters_success(mock_core_fangraphs, hitter_fixture_data):
    """Test successful hitter fetch."""
    # Setup mock to return fixture data
    mock_core_fangraphs.get_projections_data.return_value = hitter_fixture_data

    handler = PlayerFetchHandler(mock_core_fangraphs)
    players = handler.fetch_hitters()

    # Verify API was called correctly (now includes projection_source parameter)
    mock_core_fangraphs.get_projections_data.assert_called_once_with(
        "bat", projections_system="steamer"
    )

    # Verify results
    assert len(players) == 2
    assert all(isinstance(p, HitterModel) for p in players)
    assert "Aaron Judge" in [p.name for p in players]
    assert "Bobby Witt Jr." in [p.name for p in players]


def test_fetch_hitters_empty_response(mock_core_fangraphs):
    """Test hitter fetch with empty/None response."""
    mock_core_fangraphs.get_projections_data.return_value = None

    handler = PlayerFetchHandler(mock_core_fangraphs)
    players = handler.fetch_hitters()

    # Should return empty list
    assert players == []
    mock_core_fangraphs.get_projections_data.assert_called_once_with(
        "bat", projections_system="steamer"
    )


def test_fetch_hitters_exception(mock_core_fangraphs):
    """Test hitter fetch with API exception."""
    mock_core_fangraphs.get_projections_data.side_effect = Exception("API Error")

    handler = PlayerFetchHandler(mock_core_fangraphs)
    players = handler.fetch_hitters()

    # Should catch exception and return empty list
    assert players == []


def test_fetch_pitchers_success(mock_core_fangraphs, pitcher_fixture_data):
    """Test successful pitcher fetch."""
    # Setup mock to return fixture data
    mock_core_fangraphs.get_projections_data.return_value = pitcher_fixture_data

    handler = PlayerFetchHandler(mock_core_fangraphs)
    players = handler.fetch_pitchers()

    # Verify API was called correctly (now includes projection_source parameter)
    mock_core_fangraphs.get_projections_data.assert_called_once_with(
        "pit", projections_system="steamer"
    )

    # Verify results
    assert len(players) == 1
    assert all(isinstance(p, PitcherModel) for p in players)
    assert players[0].name == "Test Pitcher"


def test_fetch_pitchers_empty_response(mock_core_fangraphs):
    """Test pitcher fetch with empty/None response."""
    mock_core_fangraphs.get_projections_data.return_value = None

    handler = PlayerFetchHandler(mock_core_fangraphs)
    players = handler.fetch_pitchers()

    # Should return empty list
    assert players == []
    mock_core_fangraphs.get_projections_data.assert_called_once_with(
        "pit", projections_system="steamer"
    )


def test_fetch_pitchers_exception(mock_core_fangraphs):
    """Test pitcher fetch with API exception."""
    mock_core_fangraphs.get_projections_data.side_effect = Exception("API Error")

    handler = PlayerFetchHandler(mock_core_fangraphs)
    players = handler.fetch_pitchers()

    # Should catch exception and return empty list
    assert players == []


def test_handler_initialization(mock_core_fangraphs):
    """Test handler initialization."""
    handler = PlayerFetchHandler(mock_core_fangraphs)

    assert handler.core_fangraphs == mock_core_fangraphs
    assert handler.logger is not None
    assert handler.log is not None


def test_fetch_all_players_multi_source_success(
    mock_core_fangraphs, hitter_fixture_data, pitcher_fixture_data
):
    """Test fetching players from multiple sources."""
    # Setup mock to return different data for different calls
    def get_projections_side_effect(position_group, projections_system):
        if position_group == "bat":
            return hitter_fixture_data
        elif position_group == "pit":
            return pitcher_fixture_data
        return None

    mock_core_fangraphs.get_projections_data.side_effect = (
        get_projections_side_effect
    )

    handler = PlayerFetchHandler(mock_core_fangraphs)
    sources = {
        "batters": ["steamer", "fangraphsdc"],
        "pitchers": ["steamer", "fangraphsdc"],
    }
    batters_by_source, pitchers_by_source = handler.fetch_all_players_multi_source(
        sources
    )

    # Verify we got data for both sources
    assert len(batters_by_source) == 2
    assert "steamer" in batters_by_source
    assert "fangraphsdc" in batters_by_source
    assert len(pitchers_by_source) == 2
    assert "steamer" in pitchers_by_source
    assert "fangraphsdc" in pitchers_by_source

    # Verify steamer data (2 hitters, 1 pitcher)
    assert len(batters_by_source["steamer"]) == 2
    assert len(pitchers_by_source["steamer"]) == 1
    assert all(isinstance(p, HitterModel) for p in batters_by_source["steamer"])
    assert all(isinstance(p, PitcherModel) for p in pitchers_by_source["steamer"])

    # Verify fangraphsdc data (2 hitters, 1 pitcher)
    assert len(batters_by_source["fangraphsdc"]) == 2
    assert len(pitchers_by_source["fangraphsdc"]) == 1
    assert all(isinstance(p, HitterModel) for p in batters_by_source["fangraphsdc"])
    assert all(isinstance(p, PitcherModel) for p in pitchers_by_source["fangraphsdc"])

    # Verify API was called 4 times (2 sources × 2 position groups)
    assert mock_core_fangraphs.get_projections_data.call_count == 4


def test_fetch_all_players_multi_source_single_source(
    mock_core_fangraphs, hitter_fixture_data, pitcher_fixture_data
):
    """Test fetching players with a single source in the list."""
    def get_projections_side_effect(position_group, projections_system):
        if position_group == "bat":
            return hitter_fixture_data
        elif position_group == "pit":
            return pitcher_fixture_data
        return None

    mock_core_fangraphs.get_projections_data.side_effect = (
        get_projections_side_effect
    )

    handler = PlayerFetchHandler(mock_core_fangraphs)
    sources = {"batters": ["steamer"], "pitchers": ["steamer"]}
    batters_by_source, pitchers_by_source = handler.fetch_all_players_multi_source(
        sources
    )

    # Verify we got data for one source
    assert len(batters_by_source) == 1
    assert "steamer" in batters_by_source
    assert len(batters_by_source["steamer"]) == 2
    assert len(pitchers_by_source) == 1
    assert "steamer" in pitchers_by_source
    assert len(pitchers_by_source["steamer"]) == 1

    # Verify API was called 2 times (1 source × 2 position groups)
    assert mock_core_fangraphs.get_projections_data.call_count == 2


def test_fetch_all_players_multi_source_empty_sources(mock_core_fangraphs):
    """Test fetching players with empty sources list."""
    handler = PlayerFetchHandler(mock_core_fangraphs)
    sources: dict[str, list[str]] = {}
    batters_by_source, pitchers_by_source = handler.fetch_all_players_multi_source(
        sources
    )

    # Should return empty dictionaries
    assert batters_by_source == {}
    assert pitchers_by_source == {}
    # API should not be called
    mock_core_fangraphs.get_projections_data.assert_not_called()
