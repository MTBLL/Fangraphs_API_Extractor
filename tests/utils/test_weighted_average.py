"""Tests for weighted averaging utility functions."""

from typing import Optional, cast

from pydantic import Field

from fangraphs_api_extractor.models.base_player import (
    BaseProjectionModel,
    PlayerModel,
)
from fangraphs_api_extractor.models.hitter import HitterModel, HitterProjectionModel
from fangraphs_api_extractor.models.pitcher import PitcherModel, PitcherProjectionModel
from fangraphs_api_extractor.utils.weighted_average import (
    _calculate_weighted_average_projections,
    _round_half_up_to_int,
    merge_player_projections,
)


def test_round_half_up_to_int_uses_half_away_from_zero():
    """Regression: integer-field rounding must use ROUND_HALF_UP, not banker's.

    Production case that surfaced the bug: Aaron Judge HR with uzips=51 and
    steameru=50 at 50/50 weights → 50.5 → must round UP to 51, not down to 50
    like Python's built-in round() would.
    """
    assert _round_half_up_to_int(50.5) == 51
    assert _round_half_up_to_int(49.5) == 50
    assert _round_half_up_to_int(50.50245) == 51
    assert _round_half_up_to_int(-50.5) == -51  # half-away-from-zero, not toward-zero
    assert _round_half_up_to_int(0.5) == 1
    assert _round_half_up_to_int(1.4) == 1
    assert _round_half_up_to_int(1.6) == 2


# Custom projection model for testing edge cases
class CustomProjectionModel(BaseProjectionModel):
    """Custom projection model with metadata fields for testing."""

    source: Optional[str] = None
    percentiles: Optional[dict] = None
    test_stat: Optional[int] = Field(None, alias="TestStat")


class TestCalculateWeightedAverageProjections:
    """Test weighted average calculation for projections."""

    def test_simple_weighted_average_hitter(self):
        """Test weighted average with two hitter projections."""
        # Create two hitter projections
        proj1 = HitterProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PA=600, AB=550, H=150, HR=30, R=90, RBI=100, AVG=0.273
        )
        proj2 = HitterProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PA=580, AB=530, H=140, HR=25, R=85, RBI=95, AVG=0.264
        )

        projections = {"steamer": proj1, "fangraphsdc": proj2}
        weights = {"steamer": 0.75, "fangraphsdc": 0.25}

        result = _calculate_weighted_average_projections(projections, weights)

        # Check weighted averages: 0.75 * proj1 + 0.25 * proj2
        # Note: Using field names (not aliases)
        assert result["pa"] == 0.75 * 600 + 0.25 * 580  # 595.0
        assert result["ab"] == 0.75 * 550 + 0.25 * 530  # 545.0
        # h should be integer (rounded)
        assert result["h"] == round(0.75 * 150 + 0.25 * 140)  # 148
        assert result["hr"] == round(0.75 * 30 + 0.25 * 25)  # 29
        assert abs(result["avg"] - (0.75 * 0.273 + 0.25 * 0.264)) < 0.001

    def test_weighted_average_with_missing_stats(self):
        """Test weighted average when sources have different stats available."""
        # Projection 1 has all stats
        proj1 = HitterProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PA=600, AB=550, H=150, HR=30, R=90, RBI=100, AVG=0.273, ISO=0.200
        )
        # Projection 2 missing ISO
        proj2 = HitterProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PA=580, AB=530, H=140, HR=25, R=85, RBI=95, AVG=0.264
        )

        projections = {"steamer": proj1, "fangraphsdc": proj2}
        weights = {"steamer": 0.75, "fangraphsdc": 0.25}

        result = _calculate_weighted_average_projections(projections, weights)

        # iso should use only proj1's value (weight redistributed to 1.0)
        assert result["iso"] == 0.200
        # Other stats should be weighted normally
        assert result["pa"] == 0.75 * 600 + 0.25 * 580

    def test_weighted_average_redistributes_missing_weight_evenly(self):
        """Test missing stat weight is split evenly across sources with values."""
        proj_a = CustomProjectionModel(TestStat=100)  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
        proj_b = CustomProjectionModel()  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
        proj_c = CustomProjectionModel(TestStat=40)  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]

        projections = {"source1": proj_a, "source2": proj_b, "source3": proj_c}
        weights = {"source1": 0.6, "source2": 0.3, "source3": 0.1}

        result = _calculate_weighted_average_projections(projections, weights)

        # source2 is missing TestStat, so its weight (0.3) is split evenly:
        # source1 -> 0.75, source3 -> 0.25
        assert result["test_stat"] == 85

    def test_weighted_average_pitcher(self):
        """Test weighted average with pitcher projections."""
        proj1 = PitcherProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            IP=180.0, W=12, L=8, ER=70, SO=200, BB=50, ERA=3.50, WHIP=1.15
        )
        proj2 = PitcherProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            IP=175.0, W=11, L=9, ER=75, SO=190, BB=55, ERA=3.86, WHIP=1.20
        )

        projections = {"steamer": proj1, "fangraphsdc": proj2}
        weights = {"steamer": 0.6, "fangraphsdc": 0.4}

        result = _calculate_weighted_average_projections(projections, weights)

        # Check weighted averages: 0.6 * proj1 + 0.4 * proj2
        assert (
            abs(result["innings_pitched"] - (0.6 * 180.0 + 0.4 * 175.0)) < 0.01
        )  # 178.0
        # wins is defined as float in the model, so it won't be rounded
        assert abs(result["wins"] - (0.6 * 12 + 0.4 * 11)) < 0.01  # 11.6
        assert abs(result["era"] - (0.6 * 3.50 + 0.4 * 3.86)) < 0.01

    def test_equal_weights(self):
        """Test with equal weights (50/50 split)."""
        proj1 = HitterProjectionModel(PA=600, AB=550, H=150, HR=30, AVG=0.273)  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
        proj2 = HitterProjectionModel(PA=580, AB=530, H=140, HR=26, AVG=0.264)  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]

        projections = {"source1": proj1, "source2": proj2}
        weights = {"source1": 0.5, "source2": 0.5}

        result = _calculate_weighted_average_projections(projections, weights)

        # Should be simple averages
        assert result["pa"] == (600 + 580) / 2  # 590.0
        assert result["h"] == round((150 + 140) / 2)  # 145
        assert result["hr"] == round((30 + 26) / 2)  # 28

    def test_integer_preservation(self):
        """Test that integer fields are properly rounded."""
        proj1 = HitterProjectionModel(H=150, HR=30)  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
        proj2 = HitterProjectionModel(H=141, HR=27)  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]

        projections = {"source1": proj1, "source2": proj2}
        weights = {"source1": 0.75, "source2": 0.25}

        result = _calculate_weighted_average_projections(projections, weights)

        # h and hr should be integers
        assert isinstance(result["h"], int)
        assert isinstance(result["hr"], int)
        # Check values: 0.75 * 150 + 0.25 * 141 = 147.75 -> 148
        assert result["h"] == 148
        # 0.75 * 30 + 0.25 * 27 = 29.25 -> 29
        assert result["hr"] == 29

    def test_three_sources_with_different_stats(self):
        """Test averaging three sources where they have different stats available."""
        proj1 = HitterProjectionModel(HR=30, RBI=100, AVG=0.300)  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
        proj2 = HitterProjectionModel(HR=28, RBI=95, AVG=0.290)  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
        proj3 = HitterProjectionModel(
            HR=32, AVG=0.310
        )  # Missing RBI  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]

        projections = {"source1": proj1, "source2": proj2, "source3": proj3}
        # Initial weights: 50%, 30%, 20%
        weights = {"source1": 0.5, "source2": 0.3, "source3": 0.2}

        result = _calculate_weighted_average_projections(projections, weights)

        # HR uses all three sources with original weights
        expected_hr = round(0.5 * 30 + 0.3 * 28 + 0.2 * 32)  # 29.8 -> 30
        assert result["hr"] == expected_hr

        # RBI uses only source1 and source2, weights redistributed to 0.625 and 0.375
        # 0.5 / (0.5 + 0.3) = 0.625, 0.3 / (0.5 + 0.3) = 0.375
        # RBI is defined as float, so it won't be rounded
        expected_rbi = 0.6 * 100 + 0.4 * 95  # 62.5 + 35.625 = 98.125
        assert abs(result["rbi"] - expected_rbi) < 0.01

    def test_empty_projections(self):
        """Test with empty projections dictionary."""
        result = _calculate_weighted_average_projections({}, {})
        assert result == {}

    def test_source_not_in_weights(self):
        """Test when a projection source is not in the weights dictionary."""
        proj1 = HitterProjectionModel(HR=30, RBI=100)  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
        proj2 = HitterProjectionModel(HR=28, RBI=95)  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]

        projections = {"steamer": proj1, "fangraphsdc": proj2}
        # Only provide weight for steamer, not fangraphsdc
        weights = {"steamer": 1.0}

        result = _calculate_weighted_average_projections(projections, weights)

        # Should only use steamer (since fangraphsdc not in weights)
        assert result["hr"] == 30
        assert result["rbi"] == 100.0

    def test_metadata_fields_skipped(self):
        """Test that 'source' and 'percentiles' fields are skipped in averaging."""
        # Create custom projections with source and percentiles fields
        proj1 = CustomProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            source="source1", percentiles={"p50": 100}, TestStat=30
        )
        proj2 = CustomProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            source="source2", percentiles={"p50": 90}, TestStat=20
        )

        projections = {"source1": proj1, "source2": proj2}
        weights = {"source1": 0.5, "source2": 0.5}

        result = _calculate_weighted_average_projections(projections, weights)

        # source and percentiles should NOT be in the result
        assert "source" not in result
        assert "percentiles" not in result
        # test_stat should be averaged
        assert result["test_stat"] == 25  # (30 + 20) / 2 = 25

    def test_calculate_weighted_average_projections_with_oopsy_source(
        self, mason_miller_oopsy, mason_miller_fangraphsdc
    ):
        proj_oopsy = mason_miller_oopsy.projections
        proj_dc = mason_miller_fangraphsdc.projections
        assert proj_oopsy is not None
        assert proj_dc is not None

        projections = {"oopsy": proj_oopsy, "fangraphsdc": proj_dc}
        weights = {"oopsy": 0.6, "fangraphsdc": 0.4}

        result = _calculate_weighted_average_projections(projections, weights)

        expected_wins = 0.6 * proj_oopsy.wins + 0.4 * proj_dc.wins
        expected_strikeouts = 0.6 * proj_oopsy.strikeouts + 0.4 * proj_dc.strikeouts
        expected_era = 0.6 * proj_oopsy.era + 0.4 * proj_dc.era
        expected_fpts_ip = 0.6 * proj_oopsy.fpts_ip + 0.4 * proj_dc.fpts_ip
        expected_svhd = 0.6 * proj_oopsy.svhd + 0.4 * proj_dc.svhd

        assert abs(result["wins"] - expected_wins) < 0.0001
        assert abs(result["strikeouts"] - expected_strikeouts) < 0.0001
        assert abs(result["era"] - expected_era) < 0.0001
        assert abs(result["fpts_ip"] - expected_fpts_ip) < 0.0001
        assert abs(result["svhd"] - expected_svhd) < 0.0001


class TestMergePlayerProjections:
    """Test player projection merging functionality."""

    def test_empty_players_by_source(self):
        """Test with empty players_by_source dictionary."""
        result = merge_player_projections({}, {})
        assert result == []

    def test_merge_pitcher_projections(self):
        """Test merging pitcher projections from multiple sources."""
        # Create pitcher with steamer projection
        pitcher1 = PitcherModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PlayerName="Test Pitcher",
            playerid="12345",
            Team="NYY",
            teamid=9,
            xMLBAMID=123456,
        )
        pitcher1.projections = PitcherProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            IP=180.0, W=12, ERA=3.50
        )

        # Same pitcher with fangraphsdc projection
        pitcher2 = PitcherModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PlayerName="Test Pitcher",
            playerid="12345",
            Team="NYY",
            teamid=9,
            xMLBAMID=123456,
        )
        pitcher2.projections = PitcherProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            IP=175.0, W=11, ERA=3.86
        )

        players_by_source = {"steamer": [pitcher1], "fangraphsdc": [pitcher2]}
        weights = {"steamer": 0.75, "fangraphsdc": 0.25}

        result = merge_player_projections(players_by_source, weights)

        assert len(result) == 1
        player = result[0]
        # Verify it's the base player with a weighted projection
        assert player is pitcher1
        assert isinstance(player.projections, PitcherProjectionModel)
        assert pitcher2.projections is None
        assert pitcher1._source_projections == {}
        assert pitcher2._source_projections == {}

    def test_merge_hitter_projections(self):
        """Test merging hitter projections from multiple sources."""
        # Create hitter with steamer projection
        hitter1 = HitterModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PlayerName="Test Hitter",
            playerid="54321",
            Team="LAD",
            teamid=10,
            xMLBAMID=654321,
        )
        hitter1.projections = HitterProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PA=600, HR=30, AVG=0.280
        )
        hitter1 = cast(PlayerModel, hitter1)

        # Same hitter with fangraphsdc projection
        hitter2 = HitterModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PlayerName="Test Hitter",
            playerid="54321",
            Team="LAD",
            teamid=10,
            xMLBAMID=654321,
        )
        hitter2.projections = HitterProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PA=580, HR=28, AVG=0.275
        )

        players_by_source = {"steamer": [hitter1], "fangraphsdc": [hitter2]}
        weights = {"steamer": 0.75, "fangraphsdc": 0.25}

        result = merge_player_projections(players_by_source, weights)

        assert len(result) == 1
        player = result[0]
        # Verify it's the base player with a weighted projection
        assert player is hitter1
        assert isinstance(player.projections, HitterProjectionModel)
        assert hitter2.projections is None
        assert hitter1._source_projections == {}
        assert hitter2._source_projections == {}

    def test_merge_no_overlap(self):
        """Test merging when players don't overlap (each only in one source)."""
        # Different players in each source
        hitter1 = HitterModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PlayerName="Player 1",
            playerid="11111",
            Team="NYY",
            teamid=9,
            xMLBAMID=111111,
        )
        hitter1.projections = HitterProjectionModel(HR=30)  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]

        hitter2 = HitterModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PlayerName="Player 2",
            playerid="22222",
            Team="LAD",
            teamid=10,
            xMLBAMID=222222,
        )
        hitter2.projections = HitterProjectionModel(HR=25)  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]

        players_by_source = {"steamer": [hitter1], "fangraphsdc": [hitter2]}
        weights = {"steamer": 0.75, "fangraphsdc": 0.25}

        result = merge_player_projections(players_by_source, weights)

        # Should have 2 players
        assert len(result) == 2
        # Each should keep its single projection
        hr_values = {player.projections.hr for player in result}
        assert hr_values == {30, 25}

    def test_merge_single_projection_keeps_projection(self):
        """Test merging when a player has only one projection source."""
        hitter = HitterModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PlayerName="Single Source",
            playerid="33333",
            Team="SEA",
            teamid=11,
            xMLBAMID=333333,
        )
        projection = HitterProjectionModel(HR=22)  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
        hitter.projections = projection
        hitter._source_projections["steamer"] = projection

        players_by_source = {"steamer": [hitter]}
        weights = {"steamer": 1.0}

        result = merge_player_projections(players_by_source, weights)

        assert len(result) == 1
        player = result[0]
        assert player is hitter
        assert player.projections is projection
        assert player._source_projections == {}

    def test_merge_with_base_projection_model(self):
        """Test merging when using BaseProjectionModel (fallback case)."""
        # Create a custom player model that uses BaseProjectionModel
        # instead of HitterProjectionModel or PitcherProjectionModel
        player1 = PlayerModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PlayerName="Test Player",
            playerid="99999",
            Team="NYY",
            teamid=9,
            xMLBAMID=999999,
        )
        # Add a custom projection using the CustomProjectionModel
        player1.projections = CustomProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            TestStat=100
        )

        player2 = PlayerModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PlayerName="Test Player",
            playerid="99999",
            Team="NYY",
            teamid=9,
            xMLBAMID=999999,
        )
        # Add another custom projection
        player2.projections = CustomProjectionModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            TestStat=80
        )
        player2 = cast(PitcherModel, player2)

        players_by_source: dict[str, list[PlayerModel]] = {
            "source1": [player1],
            "source2": [player2],
        }
        weights = {"source1": 0.6, "source2": 0.4}

        result = merge_player_projections(players_by_source, weights)

        assert len(result) == 1
        player = result[0]
        # Should be a BaseProjectionModel (not a HitterProjectionModel or PitcherProjectionModel)
        assert isinstance(player.projections, BaseProjectionModel)
        # Verify it's specifically BaseProjectionModel and not a subclass
        assert type(player.projections) is BaseProjectionModel

    def test_merge_with_empty_averaged_projection(self):
        """Test merging when weighted average yields no fields."""
        player1 = PlayerModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PlayerName="Test Player",
            playerid="77777",
            Team="NYY",
            teamid=9,
            xMLBAMID=777777,
        )
        player2 = PlayerModel(  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]
            PlayerName="Test Player",
            playerid="77777",
            Team="NYY",
            teamid=9,
            xMLBAMID=777777,
        )

        proj1 = BaseProjectionModel()  # type: ignore
        proj2 = BaseProjectionModel()  # type: ignore
        player1.projections = proj1
        player1._source_projections["source1"] = proj1
        player2.projections = proj2
        player2._source_projections["source2"] = proj2

        player2 = cast(PitcherModel, player2)

        players_by_source: dict[str, list[PlayerModel]] = {
            "source1": [player1],
            "source2": [player2],
        }
        weights = {"source1": 0.6, "source2": 0.4}

        result = merge_player_projections(players_by_source, weights)

        assert len(result) == 1
        player = result[0]
        assert player is player1
        assert player.projections is proj1
        assert player._source_projections == {}
        assert player2.projections is None
        assert player2._source_projections == {}

    def test_merge_player_projections_with_real_data(
        self, corbin_carroll_thebatx, corbin_carroll_fangraphsdc, corbin_carroll_steamer
    ):
        players_by_source = {
            "thebatx": [corbin_carroll_thebatx],
            "fangraphsdc": [corbin_carroll_fangraphsdc],
            "steamer": [corbin_carroll_steamer],
        }
        weights = {"thebatx": 0.5, "fangraphsdc": 0.5, "steamer": 0.0}
        results = merge_player_projections(players_by_source, weights)

        assert len(results) == 1
        player = results[0]
        assert player.projections is not None
        assert player.projections.q10 is not None
