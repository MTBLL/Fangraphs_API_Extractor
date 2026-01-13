from __future__ import annotations

import json
from pathlib import Path

import pytest
from typing_extensions import TYPE_CHECKING

from fangraphs_api_extractor.managers import PlayersManager

if TYPE_CHECKING:
    from fangraphs_api_extractor.models import PlayerModel


@pytest.fixture
def fixture_hitters() -> list[PlayerModel]:
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / "hitter_fangraphsdc.json") as f:
        hitter_data = json.load(f)

    manager = PlayersManager("hitters")
    return manager.parse_players(hitter_data, projection_source="fangraphsdc")


@pytest.fixture
def single_hitter(fixture_hitters) -> PlayerModel:
    return fixture_hitters[0]


@pytest.fixture
def fixture_pitchers():
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / "pitcher_fangraphsdc.json") as f:
        pitcher_data = json.load(f)

    manager = PlayersManager("pitchers")
    return manager.parse_players(pitcher_data, projection_source="fangraphsdc")


@pytest.fixture
def single_pitcher(fixture_pitchers):
    return fixture_pitchers[0]


@pytest.fixture
def fixture_hitters_thebatx() -> list[PlayerModel]:
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / "hitter_thebatx.json") as f:
        hitter_data = json.load(f)

    manager = PlayersManager("hitters")
    return manager.parse_players(hitter_data, projection_source="thebatx")


@pytest.fixture
def single_hitter_thebatx(fixture_hitters_thebatx) -> PlayerModel:
    return fixture_hitters_thebatx[0]


@pytest.fixture
def fixture_pitchers_thebat() -> list[PlayerModel]:
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / "pitcher_thebat.json") as f:
        pitcher_data = json.load(f)

    manager = PlayersManager("pitchers")
    return manager.parse_players(pitcher_data, projection_source="thebat")


@pytest.fixture
def single_pitcher_thebat(fixture_pitchers_thebat) -> PlayerModel:
    return fixture_pitchers_thebat[0]


@pytest.fixture
def fixture_hitters_steamer() -> list[PlayerModel]:
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / "hitter_steamer.json") as f:
        hitter_data = json.load(f)

    manager = PlayersManager("hitters")
    return manager.parse_players(hitter_data, projection_source="steamer")


@pytest.fixture
def single_hitter_steamer(fixture_hitters_steamer) -> PlayerModel:
    return fixture_hitters_steamer[0]


@pytest.fixture
def fixture_pitchers_steamer() -> list[PlayerModel]:
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / "pitcher_steamer.json") as f:
        pitcher_data = json.load(f)

    manager = PlayersManager("pitchers")
    return manager.parse_players(pitcher_data, projection_source="steamer")


@pytest.fixture
def single_pitcher_steamer(fixture_pitchers_steamer) -> PlayerModel:
    return fixture_pitchers_steamer[0]


# Specific player fixtures for consistent testing across sources
@pytest.fixture
def aaron_judge_steamer(fixture_hitters_steamer) -> PlayerModel:
    """Aaron Judge from Steamer projections."""
    return next(p for p in fixture_hitters_steamer if p.playerid == "15640")


@pytest.fixture
def aaron_judge_fangraphsdc(fixture_hitters) -> PlayerModel:
    """Aaron Judge from FanGraphs Depth Charts projections."""
    return next(p for p in fixture_hitters if p.playerid == "15640")


@pytest.fixture
def aaron_judge_thebatx(fixture_hitters_thebatx) -> PlayerModel:
    """Aaron Judge from THE BAT X projections."""
    return next(p for p in fixture_hitters_thebatx if p.playerid == "15640")


@pytest.fixture
def corbin_carroll_steamer(fixture_hitters_steamer) -> PlayerModel:
    """Corbin Carroll from Steamer projections."""
    return next(p for p in fixture_hitters_steamer if p.playerid == "25878")


@pytest.fixture
def corbin_carroll_fangraphsdc(fixture_hitters) -> PlayerModel:
    """Corbin Carroll from FanGraphs Depth Charts projections."""
    return next(p for p in fixture_hitters if p.playerid == "25878")


@pytest.fixture
def corbin_carroll_thebatx(fixture_hitters_thebatx) -> PlayerModel:
    """Corbin Carroll from THE BAT X projections."""
    return next(p for p in fixture_hitters_thebatx if p.playerid == "25878")


@pytest.fixture
def jose_ramirez_thebatx(fixture_hitters_thebatx) -> PlayerModel:
    """Jose Ramirez from THE BAT projections."""
    return next(p for p in fixture_hitters_thebatx if p.playerid == "13510")


@pytest.fixture
def jose_ramirez_fangraphsdc(fixture_hitters) -> PlayerModel:
    """Jose Ramirez from FanGraphs Depth Charts projections."""
    return next(p for p in fixture_hitters if p.playerid == "13510")


@pytest.fixture
def jose_ramirez_steamer(fixture_hitters_steamer) -> PlayerModel:
    """Jose Ramirez from Steamer projections."""
    return next(p for p in fixture_hitters_steamer if p.playerid == "13510")


@pytest.fixture
def paul_skenes_steamer(fixture_pitchers_steamer) -> PlayerModel:
    """Paul Skenes from Steamer projections."""
    return next(p for p in fixture_pitchers_steamer if p.playerid == "33677")


@pytest.fixture
def paul_skenes_fangraphsdc(fixture_pitchers) -> PlayerModel:
    """Paul Skenes from FanGraphs Depth Charts projections."""
    return next(p for p in fixture_pitchers if p.playerid == "33677")


@pytest.fixture
def paul_skenes_thebat(fixture_pitchers_thebat) -> PlayerModel:
    """Paul Skenes from THE BAT projections."""
    return next(p for p in fixture_pitchers_thebat if p.playerid == "33677")
