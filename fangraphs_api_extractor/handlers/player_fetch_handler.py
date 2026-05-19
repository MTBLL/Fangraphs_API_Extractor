"""
Player fetch handler.

This module contains the handler logic for fetching player data
from the Fangraphs Baseball API and parsing it into PlayerModel objects.
"""

import time
from typing import Dict, List, Tuple

from rich.console import Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

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

    def fetch_hitters(self, projection_source: str = "steamer") -> List[PlayerModel]:
        """
        Fetch and parse hitter projections from a specific source.

        Args:
            projection_source: Name of projection source (e.g., 'steamer', 'fangraphsdc')

        Returns:
            List of hitter PlayerModel objects
        """
        year = self.core_fangraphs.year
        self.log.debug(
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
                self.log.debug(f"Parsed {len(hitters)} hitters from {projection_source}")
                return hitters
            else:
                self.log.warning(
                    f"Failed to fetch hitter data from {projection_source}"
                )
                return []
        except Exception as e:
            self.log.error(f"Error fetching hitter data from {projection_source}: {e}")
            return []

    def fetch_pitchers(self, projection_source: str = "steamer") -> List[PlayerModel]:
        """
        Fetch and parse pitcher projections from a specific source.

        Args:
            projection_source: Name of projection source (e.g., 'steamer', 'fangraphsdc')

        Returns:
            List of pitcher PlayerModel objects

        Note:
            Pitchers use 'thebat' instead of 'thebatx' - this mapping is handled automatically.
        """
        # thebatx and rthebatx have no pitcher data; map to their thebat equivalents
        _batx_map = {"thebatx": "thebat", "rthebatx": "rthebat"}
        api_source = _batx_map.get(projection_source.lower(), projection_source)

        year = self.core_fangraphs.year
        self.log.debug(f"Fetching pitcher projections for {year} from {api_source}...")
        try:
            pitcher_data = self.core_fangraphs.get_projections_data(
                "pit", projections_system=api_source
            )
            if pitcher_data:
                pitchers_manager = PlayersManager("pitchers")
                pitchers = pitchers_manager.parse_players(
                    pitcher_data, projection_source=projection_source
                )
                self.log.debug(
                    f"Parsed {len(pitchers)} pitchers from {projection_source}"
                )
                return pitchers
            else:
                self.log.warning(
                    f"Failed to fetch pitcher data from {projection_source}"
                )
                return []
        except Exception as e:
            self.log.error(f"Error fetching pitcher data from {projection_source}: {e}")
            return []

    def fetch_all_players_multi_source(
        self, sources: Dict[str, List[str]]
    ) -> Tuple[Dict[str, List[PlayerModel]], Dict[str, List[PlayerModel]]]:
        """
        Fetch players from multiple projection sources.

        Args:
            sources: Dictionary mapping positions to lists of projection sources

        Returns:
            Tuple of dictionaries mapping source names to lists of PlayerModel objects
            (batters_by_source, pitchers_by_source)
        """
        batters_by_source: Dict[str, List[PlayerModel]] = {}
        pitchers_by_source: Dict[str, List[PlayerModel]] = {}

        batter_sources = sources.get("batters", [])
        pitcher_sources = sources.get("pitchers", [])
        for key in sources:
            if key not in ("batters", "pitchers"):
                self.log.warning(f"Invalid source structure: {key}")

        total_fetches = len(batter_sources) + len(pitcher_sources)
        fetch_start = time.perf_counter()

        progress_columns = (
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        )
        # Inner progress hosts the ephemeral "Fetching: <source>" label that
        # gets swapped per source — transient so it vanishes on exit. Outer
        # progress hosts the persistent Batters / Pitchers / Total bars so
        # their final elapsed times remain in scrollback after the run.
        inner_progress = Progress(*progress_columns, transient=True)
        outer_progress = Progress(*progress_columns, transient=False)

        with Live(
            Group(inner_progress, outer_progress), refresh_per_second=10
        ):
            overall_task = outer_progress.add_task(
                "Total progress", total=total_fetches
            )

            if batter_sources:
                batters_task = outer_progress.add_task(
                    "Batters", total=len(batter_sources)
                )
                for source in batter_sources:
                    label_task = inner_progress.add_task(
                        f"Fetching: {source}", total=1
                    )
                    try:
                        hitters = self.fetch_hitters(projection_source=source)
                        batters_by_source[source] = hitters
                        inner_progress.advance(label_task)
                        outer_progress.advance(batters_task)
                        outer_progress.advance(overall_task)
                    finally:
                        inner_progress.remove_task(label_task)

            if pitcher_sources:
                pitchers_task = outer_progress.add_task(
                    "Pitchers", total=len(pitcher_sources)
                )
                for source in pitcher_sources:
                    label_task = inner_progress.add_task(
                        f"Fetching: {source}", total=1
                    )
                    try:
                        pitchers = self.fetch_pitchers(projection_source=source)
                        pitchers_by_source[source] = pitchers
                        inner_progress.advance(label_task)
                        outer_progress.advance(pitchers_task)
                        outer_progress.advance(overall_task)
                    finally:
                        inner_progress.remove_task(label_task)

        fetch_elapsed = time.perf_counter() - fetch_start
        self.log.info(
            f"Fetched {total_fetches} Fangraphs sources in {fetch_elapsed:.1f}s"
        )

        return batters_by_source, pitchers_by_source
