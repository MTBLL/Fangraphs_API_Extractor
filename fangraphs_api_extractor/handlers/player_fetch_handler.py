"""
Player fetch handler.

This module contains the handler logic for fetching player data
from the Fangraphs Baseball API and parsing it into PlayerModel objects.
"""

from typing import List, Dict

from fangraphs_api_extractor.managers import PlayersManager
from fangraphs_api_extractor.models import PlayerModel
from fangraphs_api_extractor.requests.core_fangraphs import CoreFangraphs
from fangraphs_api_extractor.utils import Logger


class PlayerFetchHandler:
    """
    Handles fetching and parsing of player data from Fangraphs Baseball API.

    This class encapsulates the logic for:
    1. Fetching raw data from the API
    2. Parsing it into PlayerModel objects
    3. Handling errors and logging
    """

    def __init__(self, core_fangraphs: CoreFangraphs):
        """
        Initialize the PlayerFetchHandler.

        Args:
            core_fangraphs: CoreFangraphs instance for API interactions
        """
        self.core_fangraphs = core_fangraphs
        self.logger = Logger("PlayerFetchHandler")
        self.log = self.logger.logging

    def fetch_hitters(
        self, projection_source: str = "steamer"
    ) -> List[PlayerModel]:
        """
        Fetch and parse hitter projections from a specific source.

        Args:
            projection_source: Name of projection source (e.g., 'steamer', 'fangraphsdc')

        Returns:
            List of hitter PlayerModel objects
        """
        year = self.core_fangraphs.year
        self.log.info(
            f"Fetching hitter projections for {year} from {projection_source}..."
        )
        try:
            hitter_data = self.core_fangraphs.get_projections_data(
                "bat", projections_system=projection_source
            )
            if hitter_data:
                hitters_manager = PlayersManager("hitters")
                hitters = hitters_manager.parse_players(
                    hitter_data, projection_source=projection_source
                )
                self.log.info(
                    f"Parsed {len(hitters)} hitters from {projection_source}"
                )
                return hitters
            else:
                self.log.warning(f"Failed to fetch hitter data from {projection_source}")
                return []
        except Exception as e:
            self.log.error(f"Error fetching hitter data from {projection_source}: {e}")
            return []

    def fetch_pitchers(
        self, projection_source: str = "steamer"
    ) -> List[PlayerModel]:
        """
        Fetch and parse pitcher projections from a specific source.

        Args:
            projection_source: Name of projection source (e.g., 'steamer', 'fangraphsdc')

        Returns:
            List of pitcher PlayerModel objects
        """
        year = self.core_fangraphs.year
        self.log.info(
            f"Fetching pitcher projections for {year} from {projection_source}..."
        )
        try:
            pitcher_data = self.core_fangraphs.get_projections_data(
                "pit", projections_system=projection_source
            )
            if pitcher_data:
                pitchers_manager = PlayersManager("pitchers")
                pitchers = pitchers_manager.parse_players(
                    pitcher_data, projection_source=projection_source
                )
                self.log.info(
                    f"Parsed {len(pitchers)} pitchers from {projection_source}"
                )
                return pitchers
            else:
                self.log.warning(f"Failed to fetch pitcher data from {projection_source}")
                return []
        except Exception as e:
            self.log.error(f"Error fetching pitcher data from {projection_source}: {e}")
            return []

    def fetch_all_players_multi_source(
        self, sources: List[str]
    ) -> Dict[str, List[PlayerModel]]:
        """
        Fetch players from multiple projection sources.

        Args:
            sources: List of projection source names

        Returns:
            Dictionary mapping source names to lists of PlayerModel objects
        """
        all_players_by_source: Dict[str, List[PlayerModel]] = {}

        for source in sources:
            self.log.info(f"Fetching data from source: {source}")
            hitters = self.fetch_hitters(projection_source=source)
            pitchers = self.fetch_pitchers(projection_source=source)
            all_players_by_source[source] = hitters + pitchers

        return all_players_by_source
