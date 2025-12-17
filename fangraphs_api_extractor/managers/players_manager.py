from typing import Any, Dict, List

from fangraphs_api_extractor.models.base_player import PlayerModel
from fangraphs_api_extractor.utils import Logger

FG_PAGE_PROPS_API_PATH: List[str | int] = [
    "dehydratedState",
    "queries",
    0,
    "state",
    "data",
]


class PlayersManager:
    def __init__(self, player_group: str = "hitters"):
        self.logger = Logger(f"{player_group}_players_manager")
        self.log = self.logger.logging
        self.players: List[PlayerModel] = []

    def _parse_player_data_list(self, data: List):
        if self.log:
            self.log.debug(f"Handling list of player data, length: {len(data)}")

        for i, player_data in enumerate(data):
            if self.log and i < 5:
                self.log.debug(f"Processing list item {i + 1}")

            try:
                player = PlayerModel.parse_player(player_data)
                if self.log and i < 5:
                    self.log.debug(
                        f"Successfully parsed player from list: {player.name}"
                    )
                self.players.append(player)
            except Exception as e:
                if self.log:
                    self.log.warning(
                        f"Error parsing player from list item {i + 1}: {e}"
                    )

    def _parse_single_player_data(self, data: Dict[str, Any]):
        if self.log:
            self.log.debug("Handling single player data")

        try:
            player = PlayerModel.parse_player(data)
            if self.log:
                self.log.debug(f"Successfully parsed single player: {player.name}")
            self.players.append(player)
        except Exception as e:
            if self.log:
                self.log.warning(f"Error parsing single player: {e}")

    def parse_players(self, data: Dict[str, Any] | List) -> List[PlayerModel]:
        """
        Parse player data from various formats into a list of PlayerModel objects.

        Args:
            data: API response data - can be in various formats

        Returns:
            List of PlayerModel objects

        Raises:
            ValueError: If unable to parse the data
        """
        self.log.debug(f"Starting parse_players with data type: {type(data)}")

        try:
            # Handle direct list of player data
            if isinstance(data, list):
                self._parse_player_data_list(data)

            # Handle single player data
            elif isinstance(data, dict) and "PlayerName" in data:
                self._parse_single_player_data(data)

            else:
                if self.log:
                    self.log.error(f"Unrecognized data format. Data type: {type(data)}")
                    if isinstance(data, dict):
                        self.log.debug(f"Keys in data: {list(data.keys())[:10]}")

                raise ValueError(f"Unrecognized data format: {type(data)}")

        except Exception as e:
            # Log error details
            if self.log:
                self.log.error(f"Top-level error in parse_players: {e}")

        return self.players
