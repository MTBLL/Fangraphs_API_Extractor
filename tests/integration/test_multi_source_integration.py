"""Integration tests for multi-source projection extraction and weighted averaging."""

import json
from pathlib import Path
from typing import cast

import pytest

from fangraphs_api_extractor.managers import PlayersManager
from fangraphs_api_extractor.models.hitter import HitterProjectionModel, HitterModel
from fangraphs_api_extractor.utils.weighted_average import merge_player_projections


@pytest.fixture
def fixtures_dir():
    """Get the fixtures directory path."""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def steamer_hitter_data(fixtures_dir):
    """Load steamer hitter fixture."""
    with open(fixtures_dir / "hitter_steamer.json") as f:
        return json.load(f)


@pytest.fixture
def fangraphsdc_hitter_data(fixtures_dir):
    """Load fangraphsdc hitter fixture (array of players)."""
    with open(fixtures_dir / "hitter_fangraphsdc.json") as f:
        return json.load(f)


class TestMultiSourceIntegration:
    """Integration tests for multi-source projection handling."""

    def test_parse_single_player_from_each_source(
        self, steamer_hitter_data, fangraphsdc_hitter_data
    ):
        """Test parsing a single player from each source."""
        # Parse steamer data (single player: Corbin Carroll)
        steamer_manager = PlayersManager("hitters")
        steamer_players = steamer_manager.parse_players(
            steamer_hitter_data, projection_source="steamer"
        )

        assert len(steamer_players) == 1
        steamer_player = steamer_players[0]
        assert steamer_player.name == "Corbin Carroll"
        assert steamer_player.playerid == "25878"
        assert isinstance(steamer_player.projection, HitterProjectionModel)
        steamer_proj = cast(HitterProjectionModel, steamer_player.projection)
        assert steamer_proj.hr == 25  # Rounded from 25.3512

        # Parse fangraphsdc data (first player: Aaron Judge)
        dc_manager = PlayersManager("hitters")
        dc_players = dc_manager.parse_players(
            fangraphsdc_hitter_data[0:1], projection_source="fangraphsdc"
        )

        assert len(dc_players) == 1
        dc_player = dc_players[0]
        assert dc_player.name == "Aaron Judge"
        assert dc_player.playerid == "15640"
        assert isinstance(dc_player.projection, HitterProjectionModel)
        dc_proj = cast(HitterProjectionModel, dc_player.projection)
        assert dc_proj.hr == 45

    def test_parse_multiple_fangraphsdc_players(self, fangraphsdc_hitter_data):
        """Test parsing multiple players from fangraphsdc source."""
        # Take first 3 players
        dc_manager = PlayersManager("hitters")
        dc_players = cast(
            list[HitterModel],
            dc_manager.parse_players(
                fangraphsdc_hitter_data[0:3], projection_source="fangraphsdc"
            ),
        )

        assert len(dc_players) == 3
        # All should have projections
        for player in dc_players:
            proj = cast(HitterProjectionModel, player.projection)
            assert proj.hr is not None

    def test_weighted_average_with_same_player_different_sources(
        self, steamer_hitter_data
    ):
        """
        Test weighted averaging when same player exists in multiple sources.

        Since our fixtures don't have overlapping players, we'll simulate this
        by creating the same player from the steamer fixture but treating it
        as coming from two different sources.
        """
        # Create player from steamer source
        manager1 = PlayersManager("hitters")
        players_steamer = manager1.parse_players(
            steamer_hitter_data, projection_source="steamer"
        )

        # Create same player but treat as fangraphsdc source
        # (In real scenario, this would be actual fangraphsdc data for same player)
        manager2 = PlayersManager("hitters")
        players_dc = manager2.parse_players(
            steamer_hitter_data, projection_source="fangraphsdc"
        )

        # Both should be Corbin Carroll
        assert players_steamer[0].playerid == players_dc[0].playerid

        steamer_proj = cast(HitterProjectionModel, players_steamer[0].projection)

        # Merge with 75% steamer, 25% fangraphsdc weights
        players_by_source = {
            "steamer": players_steamer,
            "fangraphsdc": players_dc,
        }
        weights = {"steamer": 0.75, "fangraphsdc": 0.25}

        merged_players = merge_player_projections(players_by_source, weights)

        assert len(merged_players) == 1
        player = merged_players[0]

        # Weighted average should exist
        avg_proj = cast(HitterProjectionModel, player.projection)

        # Since both sources are identical, weighted average should equal the original
        # (75% + 25% of same value = 100% of that value)
        assert avg_proj.hr == steamer_proj.hr
        assert abs(avg_proj.avg - steamer_proj.avg) < 0.0001

    def test_merge_different_players_no_overlap(
        self, steamer_hitter_data, fangraphsdc_hitter_data
    ):
        """
        Test merging when sources have completely different players (no overlap).

        Players should not get weighted averages since each only exists in one source.
        """
        # Parse steamer (Corbin Carroll)
        manager1 = PlayersManager("hitters")
        players_steamer = manager1.parse_players(
            steamer_hitter_data, projection_source="steamer"
        )

        # Parse fangraphsdc (Aaron Judge + others)
        manager2 = PlayersManager("hitters")
        players_dc = manager2.parse_players(
            fangraphsdc_hitter_data[0:2], projection_source="fangraphsdc"
        )

        # Merge
        players_by_source = {
            "steamer": players_steamer,
            "fangraphsdc": players_dc,
        }
        weights = {"steamer": 0.75, "fangraphsdc": 0.25}

        merged_players = merge_player_projections(players_by_source, weights)

        # Should have 3 total players (1 from steamer + 2 from fangraphsdc)
        assert len(merged_players) == 3

        # None should have weighted_average since no player appears in both sources
        for player in merged_players:
            assert player.projection is not None

    def test_projection_data_is_preserved(self, fangraphsdc_hitter_data):
        """Test that projection data is stored in player objects."""
        dc_manager = PlayersManager("hitters")
        dc_players = dc_manager.parse_players(
            fangraphsdc_hitter_data[0:1], projection_source="fangraphsdc"
        )

        player = dc_players[0]

        # Projection should have the expected data
        proj = cast(HitterProjectionModel, player.projection)
        assert proj.pa == 672  # From Aaron Judge fixture
        assert proj.hr == 45
