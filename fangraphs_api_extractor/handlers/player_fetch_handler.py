"""
Player fetch handler.

This module contains the handler logic for fetching player data
from the Fangraphs Baseball API and parsing it into PlayerModel objects.
"""

from typing import List

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

    def fetch_hitters(self) -> List[PlayerModel]:
        """
        Fetch and parse hitter projections.

        Returns:
            List of hitter PlayerModel objects
        """
        year = self.core_fangraphs.year
        self.log.info(f"Fetching hitter projections for {year}...")
        try:
            hitter_data = self.core_fangraphs.get_projections_data("bat")
            if hitter_data:
                hitters_manager = PlayersManager("hitters")
                hitters = hitters_manager.parse_players(hitter_data)
                self.log.info(f"Parsed {len(hitters)} hitters")
                return hitters
            else:
                self.log.warning("Failed to fetch hitter data")
                return []
        except Exception as e:
            self.log.error(f"Error fetching hitter data: {e}")
            return []

    def fetch_pitchers(self) -> List[PlayerModel]:
        """
        Fetch and parse pitcher projections.

        Returns:
            List of pitcher PlayerModel objects
        """
        year = self.core_fangraphs.year
        self.log.info(f"Fetching pitcher projections for {year}...")
        try:
            pitcher_data = self.core_fangraphs.get_projections_data("pit")
            if pitcher_data:
                pitchers_manager = PlayersManager("pitchers")
                pitchers = pitchers_manager.parse_players(pitcher_data)
                self.log.info(f"Parsed {len(pitchers)} pitchers")
                return pitchers
            else:
                self.log.warning("Failed to fetch pitcher data")
                return []
        except Exception as e:
            self.log.error(f"Error fetching pitcher data: {e}")
            return []
