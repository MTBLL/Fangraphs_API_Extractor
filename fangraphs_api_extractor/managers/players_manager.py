from typing import Any, Dict, List

from fangraphs_api_extractor.models.base_player import PlayerModel
from fangraphs_api_extractor.utils import Logger, get_nested_values

FG_PAGE_PROPS_API_PATH = ["dehydratedState", "queries", 0, "state", "data"]


class PlayersManager:
    def __init__(self, player_group: str = "hitters"):
        self.logger = Logger(f"{player_group}_players_manager")
        self.log = self.logger.logging
        self.players = []

    def _parse_nested_player_data(self, data: Dict[str, Any]):
        if self.log:
            self.log.debug("Handling API response structure with pageProps")
        try:
            unnested_data = get_nested_values(data, FG_PAGE_PROPS_API_PATH)
            assert isinstance(unnested_data, list)
            if self.log:
                self.log.debug(f"Found {len(unnested_data)} players in unnested data")

            for i, player_data in enumerate(unnested_data):
                if self.log and i < 5:  # Log details for first 5 players only
                    self.log.debug(f"Processing player {i + 1} of {len(unnested_data)}")
                    self.log.debug(f"Player data keys: {list(player_data.keys())[:5]}")

                try:
                    player = PlayerModel.parse_player(player_data)

                    if self.log and i < 5:
                        self.log.debug(f"Successfully parsed player: {player.name}")
                        self.log.debug(f"Player type: {type(player)}")

                    self.players.append(player)
                except Exception as e:
                    if self.log:
                        self.log.warning(
                            f"Error parsing individual player {i + 1}: {e}"
                        )

            if self.log:
                self.log.info(
                    f"Completed processing {len(self.players)} players successfully"
                )

        except (KeyError, IndexError, TypeError) as e:
            if self.log:
                self.log.error(f"Error in API structure: {e}")
                self.log.debug(f"Keys in data: {list(data.keys())}")
                if "pageProps" in data:
                    self.log.debug(
                        f"Keys in pageProps: {list(data['pageProps'].keys())}"
                    )
            raise ValueError(f"Error unpacking API response structure: {e}")

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
            # Handle full API response structure
            if isinstance(data, dict) and "pageProps" in data:
                self._parse_nested_player_data(data["pageProps"])

            # Handle direct list of player data
            elif isinstance(data, list):
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
