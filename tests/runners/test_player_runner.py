"""Tests for PlayerRunner."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fangraphs_api_extractor.managers import PlayersManager
from fangraphs_api_extractor.models import HitterModel, PitcherModel
from fangraphs_api_extractor.runners import PlayerRunner


@pytest.fixture
def sample_hitters():
    """Create sample hitter models."""
    hitters = []
    for i in range(5):
        data = {
            "Team": "NYY",
            "playerid": f"1000{i}",
            "PlayerName": f"Hitter {i}",
            "xMLBAMID": 100000 + i,
            "teamid": 9,
            "AB": 500,
            "PA": 550,
            "RBI": 100,
            "HR": 30,
            "AVG": 0.300,
        }
        hitters.append(HitterModel.model_validate(data))
    return hitters


@pytest.fixture
def sample_pitchers():
    """Create sample pitcher models."""
    pitchers = []
    for i in range(3):
        data = {
            "Team": "LAD",
            "playerid": f"2000{i}",
            "PlayerName": f"Pitcher {i}",
            "xMLBAMID": 200000 + i,
            "teamid": 10,
            "W": 10,
            "L": 5,
            "ERA": 3.50,
            "IP": 150.0,
        }
        pitchers.append(PitcherModel.model_validate(data))
    return pitchers


def test_player_runner_initialization():
    """Test PlayerRunner initialization."""
    runner = PlayerRunner(year=2025, threads=4, batch_size=50)

    assert runner.year == 2025
    assert runner.threads == 4
    assert runner.batch_size == 50
    assert runner.logger is not None
    assert runner.log is not None
    assert runner.core_fangraphs is not None
    assert runner.fetch_handler is not None


def test_player_runner_initialization_defaults():
    """Test PlayerRunner initialization with default values."""
    runner = PlayerRunner(year=2025)

    assert runner.year == 2025
    assert runner.threads is None  # Should use default
    assert runner.batch_size == 100  # Default value


def test_apply_sample_limit_within_limit(sample_hitters, sample_pitchers):
    """Test _apply_sample_limit when sample size is larger than total."""
    runner = PlayerRunner(year=2025)

    # Sample size larger than total (5 hitters + 3 pitchers = 8 total)
    result = runner._apply_sample_limit(sample_hitters, sample_pitchers, sample_size=10)

    # Should return all players
    assert len(result) == 8


def test_apply_sample_limit_exceeds_total(sample_hitters, sample_pitchers):
    """Test _apply_sample_limit when sample size is smaller than total."""
    runner = PlayerRunner(year=2025)

    # Sample size smaller than total (5 hitters + 3 pitchers = 8 total)
    # With sample_size=4, takes min(4, 5) hitters + min(4, 3) pitchers = 4 + 3 = 7
    result = runner._apply_sample_limit(sample_hitters, sample_pitchers, sample_size=4)

    # Should have 4 hitters + 3 pitchers = 7
    assert len(result) == 7


def test_apply_sample_limit_splits_evenly(sample_hitters, sample_pitchers):
    """Test _apply_sample_limit distributes between hitters and pitchers."""
    runner = PlayerRunner(year=2025)

    # Sample size of 6 with 5 hitters and 3 pitchers
    # Takes min(6, 5) hitters + min(6, 3) pitchers = 5 + 3 = 8
    result = runner._apply_sample_limit(sample_hitters, sample_pitchers, sample_size=6)

    # Should return all 8 players (5 hitters + 3 pitchers)
    assert len(result) == 8


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
def test_run_success(mock_handler_class, sample_hitters, sample_pitchers):
    """Test successful run execution."""
    # Setup mock handler
    mock_handler = MagicMock()
    # Mock the multi-source fetch method
    mock_handler.fetch_all_players_multi_source.return_value = {
        "steamer": sample_hitters + sample_pitchers
    }
    mock_handler_class.return_value = mock_handler

    runner = PlayerRunner(year=2025)
    players = runner.run()

    # Verify results
    assert players is not None
    assert len(players) == 8  # 5 hitters + 3 pitchers

    # Verify handler method was called with correct sources
    mock_handler.fetch_all_players_multi_source.assert_called_once_with(["steamer"])


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
def test_run_with_sample_size(mock_handler_class, sample_hitters, sample_pitchers):
    """Test run with sample size limit."""
    # Setup mock handler
    mock_handler = MagicMock()
    # Mock the multi-source fetch method
    mock_handler.fetch_all_players_multi_source.return_value = {
        "steamer": sample_hitters + sample_pitchers
    }
    mock_handler_class.return_value = mock_handler

    runner = PlayerRunner(year=2025)
    players = runner.run(sample_size=3)

    # With the new logic, sample_size just limits the final combined list
    # So we get the first 3 players from the combined list (5 hitters + 3 pitchers)
    assert players is not None
    assert len(players) == 3


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
@patch("fangraphs_api_extractor.runners.player_runner.save_extraction_results")
def test_run_with_output_dir(
    mock_save_results, mock_handler_class, sample_hitters, sample_pitchers
):
    """Test run with output directory specified."""
    # Setup mock handler
    mock_handler = MagicMock()
    # Mock the multi-source fetch method
    mock_handler.fetch_all_players_multi_source.return_value = {
        "steamer": sample_hitters + sample_pitchers
    }
    mock_handler_class.return_value = mock_handler

    with tempfile.TemporaryDirectory() as tmpdir:
        runner = PlayerRunner(year=2025)
        players = runner.run(output_dir=tmpdir)

        # Verify save_extraction_results was called with split lists
        mock_save_results.assert_called_once()
        _, call_kwargs = mock_save_results.call_args
        assert call_kwargs["output_dir"] == tmpdir
        assert call_kwargs["year"] == 2025
        assert len(call_kwargs["batters"]) == 5
        assert len(call_kwargs["pitchers"]) == 3

        # Verify players returned
        assert players is not None
        assert len(players) == 8


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
def test_run_without_output_dir(mock_handler_class, sample_hitters, sample_pitchers):
    """Test run without output directory (no file written)."""
    # Setup mock handler
    mock_handler = MagicMock()
    # Mock the multi-source fetch method
    mock_handler.fetch_all_players_multi_source.return_value = {
        "steamer": sample_hitters + sample_pitchers
    }
    mock_handler_class.return_value = mock_handler

    runner = PlayerRunner(year=2025)
    players = runner.run(output_dir=None)

    # Should still return players
    assert players is not None
    assert len(players) == 8


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
def test_run_with_empty_results(mock_handler_class):
    """Test run when no players are fetched."""
    # Setup mock handler to return empty result
    mock_handler = MagicMock()
    # Mock the multi-source fetch method returning empty source
    mock_handler.fetch_all_players_multi_source.return_value = {"steamer": []}
    mock_handler_class.return_value = mock_handler

    runner = PlayerRunner(year=2025)
    players = runner.run()

    # Should return empty list
    assert players == []


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
def test_run_creates_handler_with_correct_year(
    mock_handler_class, sample_hitters, sample_pitchers
):
    """Test that run creates handler with correct CoreFangraphs instance."""
    # Setup mock handler
    mock_handler = MagicMock()
    # Mock the multi-source fetch method
    mock_handler.fetch_all_players_multi_source.return_value = {
        "steamer": sample_hitters + sample_pitchers
    }
    mock_handler_class.return_value = mock_handler

    runner = PlayerRunner(year=2024)
    runner.run()

    # Verify handler was created with correct core_fangraphs
    assert mock_handler_class.called
    # The first arg should be the core_fangraphs instance
    call_args = mock_handler_class.call_args
    assert call_args[0][0] == runner.core_fangraphs


def test_apply_sample_limit_zero_sample(sample_hitters, sample_pitchers):
    """Test _apply_sample_limit with zero sample size."""
    runner = PlayerRunner(year=2025)

    result = runner._apply_sample_limit(sample_hitters, sample_pitchers, sample_size=0)

    # With sample_size=0, should return empty list
    assert len(result) == 0


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
def test_run_with_multiple_sources(mock_handler_class):
    """Test run with multiple projection sources using real fixtures."""
    # Load real fixture data
    fixtures_dir = Path(__file__).parent.parent / "fixtures"

    with open(fixtures_dir / "hitter_steamer.json") as f:
        steamer_hitter_data = json.load(f)

    with open(fixtures_dir / "hitter_fangraphsdc.json") as f:
        fangraphsdc_hitter_data = json.load(f)

    # Parse players from each source
    steamer_manager = PlayersManager("hitters")
    steamer_players = steamer_manager.parse_players(
        steamer_hitter_data, projection_source="steamer"
    )

    fangraphsdc_manager = PlayersManager("hitters")
    fangraphsdc_players = fangraphsdc_manager.parse_players(
        fangraphsdc_hitter_data[0:1], projection_source="fangraphsdc"
    )

    # Setup mock handler
    mock_handler = MagicMock()
    # Mock the multi-source fetch method returning data from two sources
    mock_handler.fetch_all_players_multi_source.return_value = {
        "steamer": steamer_players,
        "fangraphsdc": fangraphsdc_players,
    }
    mock_handler_class.return_value = mock_handler

    # Create runner with multiple sources and weights
    sources = ["steamer", "fangraphsdc"]
    weights = {"steamer": 0.75, "fangraphsdc": 0.25}
    runner = PlayerRunner(year=2025, sources=sources, weights=weights)
    players = runner.run()

    # Verify results
    assert players is not None
    assert len(players) > 2

    # Verify handler method was called with correct sources
    mock_handler.fetch_all_players_multi_source.assert_called_once_with(
        ["steamer", "fangraphsdc"]
    )

    # Verify each player has a projection
    for player in players:
        assert player.projection is not None
