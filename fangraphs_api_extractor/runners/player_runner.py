"""
Player extraction runner.

This module contains the core runner logic for extracting player data
from the Fangraphs Baseball API. It coordinates the workflow of fetching,
parsing, and serializing player data.
"""

from typing import List, Optional

from fangraphs_api_extractor.handlers import PlayerFetchHandler
from fangraphs_api_extractor.models import PlayerModel
from fangraphs_api_extractor.requests.core_fangraphs import CoreFangraphs
from fangraphs_api_extractor.utils import Logger, serialize_players, write_json_file


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
    ):
        """
        Initialize the PlayerExtractor.

        Args:
            year: League year to fetch data for
            threads: Number of threads to use for player hydration (default: 4x CPU cores)
            batch_size: Number of players to process in each batch for progress tracking
        """
        self.year = year
        self.logger = Logger("player_extractor")
        self.log = self.logger.logging
        self.threads = threads
        self.batch_size = batch_size
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
            output_dir: Optional directory path to write the JSON output. If None, no file is written.

        Returns:
            List of PlayerModel objects if successful, None otherwise
        """
        handler = PlayerFetchHandler(self.core_fangraphs)
        # Fetch hitters and pitchers
        hitters = handler.fetch_hitters()
        pitchers = handler.fetch_pitchers()

        # Combine all players
        players = hitters + pitchers
        self.log.info(f"Total players: {len(players)}")

        # Apply sample size limit if provided
        if sample_size and sample_size < len(players):
            players = self._apply_sample_limit(hitters, pitchers, sample_size)

        # Serialize player data
        player_data = serialize_players(players)

        # Write to file if output directory is provided
        if output_dir:
            write_json_file(player_data, output_dir, "fangraph_players.json")

        return players
