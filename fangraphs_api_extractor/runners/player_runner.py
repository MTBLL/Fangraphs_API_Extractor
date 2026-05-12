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
    DEFAULT_ROS_SOURCES,
    DEFAULT_ROS_WEIGHTS,
    Logger,
    save_extraction_results,
)
from fangraphs_api_extractor.utils.weighted_average import merge_player_projections


class PlayerRunner:
    """
    Handles extraction of player data from Fangraphs Baseball API.

    This class coordinates the workflow of:
    1. Fetching raw data from the API
    2. Parsing it into PlayerModel objects
    3. Serializing and optionally writing to disk
    """

    def __init__(
        self,
        year: int,
        threads: Optional[int] = None,
        batch_size: int = 100,
        sources: Optional[Dict[str, List[str]]] = None,
        weights: Optional[Dict[str, Dict[str, float]]] = None,
    ):
        """
        Initialize the PlayerExtractor.

        Args:
            year: League year to fetch data for
            threads: Number of threads to use for player hydration (default: 4x CPU cores)
            batch_size: Number of players to process in each batch for progress tracking
            sources: Dictionary mapping positions to lists of projection sources to fetch from.
                Defaults to DEFAULT_ROS_SOURCES (rest-of-season mix) — see utils.constants.
                All source strings must be values of ProjectionSource.
            weights: Normalized weights dict, e.g. {"batters": {"rthebatx": 0.5, ...}}.
                Defaults to DEFAULT_ROS_WEIGHTS.
                A steamer/steamerr weight of 0.0 is valid — it contributes only qq/tt percentile fields.
        """
        self.year = year
        self.logger = Logger("player_extractor")
        self.log = self.logger.logging
        self.threads = threads
        self.batch_size = batch_size
        self.sources = sources or DEFAULT_ROS_SOURCES
        self.weights = weights or DEFAULT_ROS_WEIGHTS
        self.core_fangraphs = CoreFangraphs(year=year)
        self.fetch_handler = PlayerFetchHandler(self.core_fangraphs)

    def _apply_sample_limit(
        self, hitters: List[PlayerModel], pitchers: List[PlayerModel], sample_size: int
    ) -> List[PlayerModel]:
        """
        Apply sample size limit to players.

        Args:
            hitters: List of hitter PlayerModel objects
            pitchers: List of pitcher PlayerModel objects
            sample_size: Maximum number of players to include

        Returns:
            Combined list of players limited to sample_size
        """
        self.log.info(f"Limiting to sample of {sample_size} players")
        limited_hitters = hitters[: min(sample_size, len(hitters))]
        limited_pitchers = pitchers[: min(sample_size, len(pitchers))]
        players = limited_hitters + limited_pitchers
        self.log.info(f"Limited to {len(players)} players")
        return players

    def run(
        self,
        sample_size: Optional[int] = None,
        output_dir: Optional[str] = None,
    ) -> Optional[List[PlayerModel]]:
        """
        Execute the player extraction workflow.

        Args:
            sample_size: Optional maximum number of players to process. If provided,
                        this will limit API calls to save time when only a sample is needed.
            output_dir: Optional directory path to write JSON output files
                (fangraph_pitchers_<year>_<timestamp>.json and
                fangraph_batters_<year>_<timestamp>.json). If None, no file is written.

        Returns:
            List of PlayerModel objects if successful, None otherwise
        """
        # Log sources and weights
        for position, sources in self.sources.items():
            sources_str = ", ".join(sources)
            weights = self.weights.get(position, {})
            if len(sources) > 1:
                self.log.info(
                    f"Fetching {position} from multiple sources: {sources_str} "
                    f"with weights: {weights}"
                )
            else:
                self.log.info(f"Fetching {position} from single source: {sources_str}")

        # Fetch from all sources (works for both single and multiple sources)
        batters_by_source, pitchers_by_source = (
            self.fetch_handler.fetch_all_players_multi_source(self.sources)
        )

        merged_hitters = merge_player_projections(
            batters_by_source, self.weights.get("batters", {})
        )
        merged_pitchers = merge_player_projections(
            pitchers_by_source, self.weights.get("pitchers", {})
        )
        players = merged_hitters + merged_pitchers
        self.log.info(f"Total players: {len(players)}")

        # Apply sample size limit if provided
        if sample_size and sample_size < len(players):
            self.log.info(f"Limiting to sample of {sample_size} players")
            players = players[:sample_size]
            self.log.info(f"Limited to {len(players)} players")

        hitters: List[PlayerModel] = [
            player for player in players if isinstance(player, HitterModel)
        ]
        pitchers: List[PlayerModel] = [
            player for player in players if isinstance(player, PitcherModel)
        ]

        # Write to file if output directory is provided
        if output_dir:
            save_extraction_results(
                pitchers=pitchers,
                batters=hitters,
                output_dir=output_dir,
                year=self.year,
            )

        return players
