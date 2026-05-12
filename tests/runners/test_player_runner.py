"""Tests for PlayerRunner."""

import copy
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from fangraphs_api_extractor.models import (
    HitterModel,
    HitterProjectionModel,
    PitcherModel,
    PitcherProjectionModel,
)
from fangraphs_api_extractor.runners import PlayerRunner


@pytest.fixture
def sample_hitters():
    """Create sample hitter models with a parsed projection attached.

    Mirrors what `parse_player` produces — the merge reads `.projections` from
    each parsed input and aggregates into `_source_projections`.
    """
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
        h = HitterModel.model_validate(data)
        h.projections = HitterProjectionModel.model_validate(data)
        hitters.append(h)
    return hitters


@pytest.fixture
def sample_pitchers():
    """Create sample pitcher models with a parsed projection attached."""
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
        p = PitcherModel.model_validate(data)
        p.projections = PitcherProjectionModel.model_validate(data)
        pitchers.append(p)
    return pitchers


def _mock_triple_fetch(
    mock_handler, projections_result, projs_updated_result, ros_result
):
    """Configure the mocked fetch handler to return distinct results for the
    three calls PlayerRunner.run makes, in order: projections, projs_updated, ros.

    Deepcopies the inputs so each cycle operates on independent PlayerModel
    instances — mirrors production where the fetch handler returns fresh
    instances per call. Without this, later merges would wipe state on the
    same objects that earlier merges already wrote to.
    """
    mock_handler.fetch_all_players_multi_source.side_effect = [
        copy.deepcopy(projections_result),
        copy.deepcopy(projs_updated_result),
        copy.deepcopy(ros_result),
    ]


# Convenience: a "default" set of mock results that populates all three slots
# from the same fixture data. Useful when a test doesn't care about the
# per-slot distinction.
def _mock_all_slots_populated(mock_handler, sample_hitters, sample_pitchers):
    """All three fetches return the same sample data — each slot ends up
    populated with merged projections for every fixture player.
    """
    _mock_triple_fetch(
        mock_handler,
        projections_result=(
            {"thebatx": sample_hitters},
            {"oopsy": sample_pitchers},
        ),
        projs_updated_result=(
            {"uzips": sample_hitters},
            {"uzips": sample_pitchers},
        ),
        ros_result=(
            {"rthebatx": sample_hitters},
            {"roopsydc": sample_pitchers},
        ),
    )


def test_player_runner_initialization():
    """Test PlayerRunner initialization."""
    runner = PlayerRunner(year=2026, threads=4, batch_size=50)

    assert runner.year == 2026
    assert runner.threads == 4
    assert runner.batch_size == 50
    assert runner.logger is not None
    assert runner.log is not None
    assert runner.core_fangraphs is not None
    assert runner.fetch_handler is not None


def test_player_runner_initialization_defaults():
    """Test PlayerRunner initialization wires up all three default slots."""
    runner = PlayerRunner(year=2026)

    assert runner.year == 2026
    assert runner.threads is None
    assert runner.batch_size == 100
    # All three slots configured
    assert set(runner.sources.keys()) == {"projections", "projs_updated", "ros"}
    # projections slot uses the canonical pre-season mix
    assert runner.sources["projections"]["batters"][0] == "thebatx"
    # updates slot uses the two refit sources at equal weight
    assert runner.sources["projs_updated"]["batters"] == ["uzips", "steameru"]
    assert runner.weights["projs_updated"]["batters"] == {"uzips": 0.5, "steameru": 0.5}
    # ros slot uses the rest-of-season mix
    assert runner.sources["ros"]["batters"][0] == "rthebatx"


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
def test_run_success(mock_handler_class, sample_hitters, sample_pitchers):
    """Test successful run execution — three fetches: projections, updates, ros."""
    mock_handler = MagicMock()
    _mock_all_slots_populated(mock_handler, sample_hitters, sample_pitchers)
    mock_handler_class.return_value = mock_handler

    runner = PlayerRunner(year=2026)
    players = runner.run()

    # 5 unique hitter ids + 3 unique pitcher ids
    assert players is not None
    assert len(players) == 8

    # Handler was called three times: projections, updates, ros — in order
    assert mock_handler.fetch_all_players_multi_source.call_count == 3
    call_args = [
        c.args[0] for c in mock_handler.fetch_all_players_multi_source.call_args_list
    ]
    assert call_args[0]["batters"][0] == "thebatx"  # projections
    assert call_args[1] == {  # updates
        "batters": ["uzips", "steameru"],
        "pitchers": ["uzips", "steameru"],
    }
    assert call_args[2] == {  # ros
        "batters": ["rthebatx", "rfangraphsdc", "ratcdc"],
        "pitchers": ["roopsydc", "rfangraphsdc", "ratcdc"],
    }

    # Each player should have all three slots populated
    for p in players:
        assert p.projections is not None
        assert p.projs_updated is not None
        assert p.ros is not None


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
def test_run_with_sample_size(mock_handler_class, sample_hitters, sample_pitchers):
    """Test run with sample size limit applied to the merged player list."""
    mock_handler = MagicMock()
    _mock_all_slots_populated(mock_handler, sample_hitters, sample_pitchers)
    mock_handler_class.return_value = mock_handler

    runner = PlayerRunner(year=2026)
    players = runner.run(sample_size=3)

    assert players is not None
    assert len(players) == 3


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
@patch("fangraphs_api_extractor.runners.player_runner.save_extraction_results")
def test_run_with_output_dir(
    mock_save_results, mock_handler_class, sample_hitters, sample_pitchers
):
    """Test run with output directory persists results."""
    mock_handler = MagicMock()
    _mock_all_slots_populated(mock_handler, sample_hitters, sample_pitchers)
    mock_handler_class.return_value = mock_handler

    with tempfile.TemporaryDirectory() as tmpdir:
        runner = PlayerRunner(year=2026)
        players = runner.run(output_dir=tmpdir)

        mock_save_results.assert_called_once()
        _, call_kwargs = mock_save_results.call_args
        assert call_kwargs["output_dir"] == tmpdir
        assert call_kwargs["year"] == 2026
        assert len(call_kwargs["batters"]) == 5
        assert len(call_kwargs["pitchers"]) == 3

        assert players is not None
        assert len(players) == 8


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
def test_run_predraft_empty_updates_and_ros(
    mock_handler_class, sample_hitters, sample_pitchers
):
    """Pre-draft: only `projections` returns data; `updates` and `ros` are empty.

    Both empty slots should leave their attributes as None on the model
    (serializer emits them as {} downstream).
    """
    mock_handler = MagicMock()
    _mock_triple_fetch(
        mock_handler,
        projections_result=(
            {"thebatx": sample_hitters},
            {"oopsy": sample_pitchers},
        ),
        projs_updated_result=({}, {}),  # uzips/steameru not published yet
        ros_result=({}, {}),       # RoS not published yet
    )
    mock_handler_class.return_value = mock_handler

    runner = PlayerRunner(year=2026)
    players = runner.run()

    assert players is not None
    assert len(players) == 8
    for p in players:
        assert p.projections is not None
        assert p.projs_updated is None
        assert p.ros is None


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
def test_run_with_empty_results(mock_handler_class):
    """Test run when no players are fetched on any slot."""
    mock_handler = MagicMock()
    _mock_triple_fetch(
        mock_handler,
        projections_result=({}, {}),
        projs_updated_result=({}, {}),
        ros_result=({}, {}),
    )
    mock_handler_class.return_value = mock_handler

    runner = PlayerRunner(year=2026)
    players = runner.run()

    assert players == []


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
def test_run_creates_handler_with_correct_year(
    mock_handler_class, sample_hitters, sample_pitchers
):
    """Test that run creates handler with correct CoreFangraphs instance."""
    mock_handler = MagicMock()
    _mock_all_slots_populated(mock_handler, sample_hitters, sample_pitchers)
    mock_handler_class.return_value = mock_handler

    runner = PlayerRunner(year=2024)
    runner.run()

    assert mock_handler_class.called
    call_args = mock_handler_class.call_args
    assert call_args[0][0] == runner.core_fangraphs


@patch("fangraphs_api_extractor.runners.player_runner.PlayerFetchHandler")
def test_run_with_custom_sources(mock_handler_class, sample_hitters, sample_pitchers):
    """Test run with custom per-slot sources and weights."""
    mock_handler = MagicMock()
    _mock_triple_fetch(
        mock_handler,
        projections_result=(
            {"thebatx": sample_hitters},
            {"oopsy": sample_pitchers},
        ),
        projs_updated_result=(
            {"uzips": sample_hitters, "steameru": sample_hitters},
            {"uzips": sample_pitchers, "steameru": sample_pitchers},
        ),
        ros_result=(
            {"rthebatx": sample_hitters},
            {"roopsydc": sample_pitchers},
        ),
    )
    mock_handler_class.return_value = mock_handler

    sources = {
        "projections": {
            "batters": ["thebatx"],
            "pitchers": ["oopsy"],
        },
        "projs_updated": {
            "batters": ["uzips", "steameru"],
            "pitchers": ["uzips", "steameru"],
        },
        "ros": {
            "batters": ["rthebatx"],
            "pitchers": ["roopsydc"],
        },
    }
    weights = {
        "projections": {
            "batters": {"thebatx": 1.0},
            "pitchers": {"oopsy": 1.0},
        },
        "projs_updated": {
            "batters": {"uzips": 0.75, "steameru": 0.25},
            "pitchers": {"uzips": 0.75, "steameru": 0.25},
        },
        "ros": {
            "batters": {"rthebatx": 1.0},
            "pitchers": {"roopsydc": 1.0},
        },
    }
    runner = PlayerRunner(year=2026, sources=sources, weights=weights)
    players = runner.run()

    assert players is not None
    assert len(players) == 8
    for p in players:
        assert p.projections is not None
        assert p.projs_updated is not None
        assert p.ros is not None
