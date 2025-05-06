import json
import os
from typing import Dict, List, Optional

from typing_extensions import TYPE_CHECKING
from fangraphs_api_extractor.models import PlayerModel
from fangraphs_api_extractor.utils import Logger

if TYPE_CHECKING:
    pass


def serialize_players(players: List[PlayerModel], logger: Logger) -> List[Dict]:
    """
    Serialize a list of PlayerModel objects into a JSON-serializable dictionary.

    Args:
        players: List of PlayerModel objects
        logger: Logger for logging messages

    Returns:
        List of dictionaries representing player data
    """
    log = logger.logging
    log.debug(f"Starting serialization of {len(players)} players")
    
    player_data_list = []

    for i, player in enumerate(players):
        try:
            log.debug(f"Processing player {i+1}: {getattr(player, 'name', 'unknown')}")
            if i < 5:  # Only log detailed debug info for first 5 players
                log.debug(f"Player type: {type(player)}")
                log.debug(f"Has model_dump: {hasattr(player, 'model_dump')}")
            
            # Ensure we have the basic player fields
            serialized_player = {
                "name": getattr(player, "name", "unknown"),
                "team": getattr(player, "team", "FA"),
                "playerid": getattr(player, "playerid", "unknown"),
                "xmlbam_id": getattr(player, "xmlbam_id", -1),
                "slug": getattr(player, "slug", ""),
                "stats_api": getattr(player, "stats_api", ""),
                "projections": {},
            }
            
            # Add projection data
            if hasattr(player, 'projections'):
                if i < 5:
                    log.debug(f"Projections type: {type(player.projections)}")
                    
                try:
                    for proj_name, proj_data in player.projections.items():
                        if i < 5:
                            log.debug(f"Processing projection: {proj_name}")
                            
                        if hasattr(proj_data, 'model_dump'):
                            # Convert projection model to dictionary using model_dump
                            proj_dict = proj_data.model_dump(exclude_none=True)
                            serialized_player["projections"][proj_name] = proj_dict
                        else:
                            # Fallback if model_dump is not available
                            log.warning(f"Projection {proj_name} has no model_dump method")
                except Exception as proj_e:
                    log.error(f"Error processing projections: {proj_e}")
                        
            player_data_list.append(serialized_player)
            
            if i % 100 == 0:  # Log progress every 100 players
                log.info(f"Serialized {i+1}/{len(players)} players")
                
        except Exception as e:
            log.error(f"Error serializing player {i+1}: {e}")
                
            # Still add basic info even if there's an error
            player_data_list.append({
                "name": getattr(player, "name", "unknown"),
                "error": str(e)
            })

    log.info(f"Completed serialization with {len(player_data_list)} results")
        
    return player_data_list


def write_json_file(
    data: List[Dict], 
    output_path: str, 
    logger: Logger,
    indent: Optional[int] = 2
) -> None:
    """
    Write player data to a JSON file.

    Args:
        data: Data to write (JSON-serializable)
        output_path: Path to output file
        indent: Indentation level for JSON formatting
        logger: Logger for logging messages
    """
    log = logger.logging
    log.debug(f"Writing data to {output_path}")
    log.debug(f"Data contains {len(data)} items")
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    try:
        # Write the data to the file
        with open(output_path, "w") as f:
            json.dump(data, f, indent=indent)
            
        log.info(f"Data successfully written to {output_path}")
            
    except Exception as e:
        log.error(f"Error writing data to {output_path}: {e}")
