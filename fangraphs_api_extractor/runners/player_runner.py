"""
Player extraction runner.

This module contains the core runner logic for extracting player data
from the Fangraphs Baseball API. It coordinates the workflow of fetching,
parsing, and serializing player data.
"""

from typing import Dict, List, Optional

from fangraphs_api_extractor.handlers import PlayerFetchHandler
from fangraphs_api_extractor.models import HitterModel, PitcherModel, PlayerModel
from fangraphs_api_extractor.requests.core_fangraphs import CoreFangraphs
from fangraphs_api_extractor.utils import (
    DEFAULT_PROJECTIONS_SOURCES,
    DEFAULT_PROJECTIONS_WEIGHTS,
    DEFAULT_ROS_SOURCES,
    DEFAULT_ROS_WEIGHTS,
    DEFAULT_UPDATES_SOURCES,
    DEFAULT_UPDATES_WEIGHTS,
    Logger,
    save_extraction_results,
)
from fangraphs_api_extractor.utils.weighted_average import merge_player_projections

# Nested per-slot structures
SlotSources = Dict[str, Dict[str, List[str]]]  # {slot: {position: [source, ...]}}
SlotWeights = Dict[
    str, Dict[str, Dict[str, float]]
]  # {slot: {position: {source: weight}}}

# The three slots, in the order they're fetched and combined. `projections`
# is the canonical full-year mix and the only slot that carries qq/tt
# percentile fields; the others are empty when Fangraphs hasn't published
# the corresponding endpoints (e.g. pre-draft).
SLOTS = ("projections", "projs_updated", "ros")


class PlayerRunner:
    """
    Handles extraction of player data from Fangraphs Baseball API.

    Each run produces a list of PlayerModel objects with three projection slots:
      - .projections: pre-season full-year (canonical) projection
      - .projs_updated:     in-season updated full-year projection (empty pre-draft)
      - .ros:         rest-of-season projection (empty pre-draft)

    All three fetch+merge passes always run. Empty fetches (typical pre-draft)
    leave the corresponding slot as None on the model, which serializes as {}.
    """

    def __init__(
        self,
        year: int,
        threads: Optional[int] = None,
        batch_size: int = 100,
        sources: Optional[SlotSources] = None,
        weights: Optional[SlotWeights] = None,
    ):
        """
        Initialize the PlayerRunner.

        Args:
            year: League year to fetch data for.
            threads: Number of threads to use for player hydration (default: 4x CPU cores).
            batch_size: Number of players to process in each batch for progress tracking.
            sources: Nested dict {slot: {position: [source, ...]}} with slot in
                {"projections", "updates", "ros"}. Omitted slots are skipped.
                Defaults to DEFAULT_*_SOURCES for all three slots.
            weights: Nested dict {slot: {position: {source: weight}}}, mirroring `sources`.
                Defaults to DEFAULT_*_WEIGHTS for all three slots.
        """
        self.year = year
        self.logger = Logger("player_extractor")
        self.log = self.logger.logging
        self.threads = threads
        self.batch_size = batch_size
        self.sources: SlotSources = sources or {
            "projections": DEFAULT_PROJECTIONS_SOURCES,
            "projs_updated": DEFAULT_UPDATES_SOURCES,
            "ros": DEFAULT_ROS_SOURCES,
        }
        self.weights: SlotWeights = weights or {
            "projections": DEFAULT_PROJECTIONS_WEIGHTS,
            "projs_updated": DEFAULT_UPDATES_WEIGHTS,
            "ros": DEFAULT_ROS_WEIGHTS,
        }
        self.core_fangraphs = CoreFangraphs(year=year)
        self.fetch_handler = PlayerFetchHandler(self.core_fangraphs)

    def _fetch_and_merge_slot(
        self, slot: str
    ) -> tuple[List[PlayerModel], List[PlayerModel]]:
        """Fetch one slot's sources and merge them. Returns (hitters, pitchers).

        Both lists may be empty — e.g. the `projs_updated` and `ros` slots in
        pre-draft mode before Fangraphs publishes those endpoints. That's a
        graceful no-op; the caller treats missing slots as None on the output.
        """
        slot_sources = self.sources.get(slot, {})
        slot_weights = self.weights.get(slot, {})

        if not slot_sources or not any(slot_sources.values()):
            self.log.info(f"Slot '{slot}' has no sources configured; skipping fetch")
            return [], []

        for position, src_list in slot_sources.items():
            if not src_list:
                continue
            w = slot_weights.get(position, {})
            self.log.info(
                f"Fetching {slot}/{position} from {len(src_list)} sources: "
                f"{', '.join(src_list)} with weights: {w}"
            )

        batters_by_source, pitchers_by_source = (
            self.fetch_handler.fetch_all_players_multi_source(slot_sources)
        )

        merged_hitters = merge_player_projections(
            batters_by_source, slot_weights.get("batters", {}), target_slot=slot
        )
        merged_pitchers = merge_player_projections(
            pitchers_by_source, slot_weights.get("pitchers", {}), target_slot=slot
        )
        self.log.info(
            f"Slot '{slot}': merged {len(merged_hitters)} hitters, "
            f"{len(merged_pitchers)} pitchers"
        )
        return merged_hitters, merged_pitchers

    @staticmethod
    def _combine_slots(
        slot_results: List[tuple[str, List[PlayerModel]]],
    ) -> List[PlayerModel]:
        """Merge per-slot result lists by playerid into one final list.

        Each input tuple is (slot_name, list_of_players_with_that_slot_set).
        For each unique playerid we keep one canonical PlayerModel (the first
        one encountered across the slots) and copy each slot's value onto it.
        """
        by_id: Dict[str, PlayerModel] = {}
        for slot_name, players in slot_results:
            for p in players:
                slot_value = getattr(p, slot_name, None)
                existing = by_id.get(p.playerid)
                if existing is None:
                    # First time seeing this player — keep this instance as
                    # the canonical record. Other slot values on it will be
                    # None until later slot results overwrite them.
                    by_id[p.playerid] = p
                else:
                    setattr(existing, slot_name, slot_value)
        return list(by_id.values())

    def run(
        self,
        sample_size: Optional[int] = None,
        output_dir: Optional[str] = None,
    ) -> Optional[List[PlayerModel]]:
        """
        Execute the player extraction workflow.

        Fetches and merges each configured slot (projections, projs_updated, ros)
        independently, then combines per-slot merged lists into a single output
        keyed by playerid.

        Args:
            sample_size: Optional max players to retain after merging.
            output_dir: Optional directory path to write JSON output files.

        Returns:
            List of PlayerModel objects with the configured slots populated.
        """
        hitter_results: List[tuple[str, List[PlayerModel]]] = []
        pitcher_results: List[tuple[str, List[PlayerModel]]] = []
        for slot in SLOTS:
            h, p = self._fetch_and_merge_slot(slot)
            hitter_results.append((slot, h))
            pitcher_results.append((slot, p))

        hitters = self._combine_slots(hitter_results)
        pitchers = self._combine_slots(pitcher_results)
        players = hitters + pitchers
        self.log.info(f"Total players: {len(players)}")

        if sample_size and sample_size < len(players):
            self.log.info(f"Limiting to sample of {sample_size} players")
            players = players[:sample_size]
            self.log.info(f"Limited to {len(players)} players")

        out_hitters: List[PlayerModel] = [
            x for x in players if isinstance(x, HitterModel)
        ]
        out_pitchers: List[PlayerModel] = [
            x for x in players if isinstance(x, PitcherModel)
        ]

        if output_dir:
            save_extraction_results(
                pitchers=out_pitchers,
                batters=out_hitters,
                output_dir=output_dir,
                year=self.year,
            )

        return players
