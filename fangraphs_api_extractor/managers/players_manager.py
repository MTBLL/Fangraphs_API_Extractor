from typing import Any, Dict, List, Optional, Union

from fangraphs_api_extractor.models.base_player import PlayerModel
from fangraphs_api_extractor.utils import Logger


def parse_players(data: Union[Dict[str, Any], List], logger: Logger) -> List[PlayerModel]:
    """
    Parse player data from various formats into a list of PlayerModel objects.

    Args:
        data: API response data - can be in various formats
        logger: Logger for logging messages

    Returns:
        List of PlayerModel objects

    Raises:
        ValueError: If unable to parse the data
    """
    log = logger.logging
    log.debug(f"Starting parse_players with data type: {type(data)}")
    
    players = []

    try:
        # Handle full API response structure
        if isinstance(data, dict) and "pageProps" in data:
            if log:
                log.debug("Handling API response structure with pageProps")
            try:
                unnested_data = data["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]
                if log:
                    log.debug(f"Found {len(unnested_data)} players in unnested data")
                
                for i, player_data in enumerate(unnested_data):
                    if log and i < 5:  # Log details for first 5 players only
                        log.debug(f"Processing player {i+1} of {len(unnested_data)}")
                        log.debug(f"Player data keys: {list(player_data.keys())[:5]}")
                    
                    try:
                        player = PlayerModel.parse_player(player_data)
                        
                        if log and i < 5:
                            log.debug(f"Successfully parsed player: {player.name}")
                            log.debug(f"Player type: {type(player)}")
                        
                        players.append(player)
                    except Exception as e:
                        if log:
                            log.warning(f"Error parsing individual player {i+1}: {e}")
                
                if log:
                    log.info(f"Completed processing {len(players)} players successfully")
                return players
            
            except (KeyError, IndexError, TypeError) as e:
                if log:
                    log.error(f"Error in API structure: {e}")
                    log.debug(f"Keys in data: {list(data.keys())}")
                    if "pageProps" in data:
                        log.debug(f"Keys in pageProps: {list(data['pageProps'].keys())}")
                raise ValueError(f"Error unpacking API response structure: {e}")

        # Handle direct list of player data
        elif isinstance(data, list):
            if log:
                log.debug(f"Handling list of player data, length: {len(data)}")
            
            for i, player_data in enumerate(data):
                if log and i < 5:
                    log.debug(f"Processing list item {i+1}")
                
                try:
                    player = PlayerModel.parse_player(player_data)
                    if log and i < 5:
                        log.debug(f"Successfully parsed player from list: {player.name}")
                    players.append(player)
                except Exception as e:
                    if log:
                        log.warning(f"Error parsing player from list item {i+1}: {e}")
            
            return players

        # Handle single player data
        elif isinstance(data, dict) and "PlayerName" in data:
            if log:
                log.debug("Handling single player data")
            
            try:
                player = PlayerModel.parse_player(data)
                if log:
                    log.debug(f"Successfully parsed single player: {player.name}")
                players.append(player)
            except Exception as e:
                if log:
                    log.warning(f"Error parsing single player: {e}")
            
            return players

        else:
            if log:
                log.error(f"Unrecognized data format. Data type: {type(data)}")
                if isinstance(data, dict):
                    log.debug(f"Keys in data: {list(data.keys())[:10]}")
            
            raise ValueError(f"Unrecognized data format: {type(data)}")

    except Exception as e:
        # Log error details
        if log:
            log.error(f"Top-level error in parse_players: {e}")

        # Return what we have instead of failing completely
        return players
