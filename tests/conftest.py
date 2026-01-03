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
