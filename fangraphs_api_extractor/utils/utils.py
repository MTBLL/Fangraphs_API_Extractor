import json
import os
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)

from fangraphs_api_extractor.utils import Logger
from fangraphs_api_extractor.utils.string_utils import normalize_string

if TYPE_CHECKING:
    from fangraphs_api_extractor.models import PlayerModel


_ROUND_QUANTUM = Decimal("0.001")


def round_floats(obj: Any) -> Any:
    """Recursively round float values to 3 decimal places, half-away-from-zero.

    Python's built-in round() uses banker's rounding (round-half-to-even), which
    gives 0.0005 -> 0.0. The requirement here is 0.0005 -> 0.001, so use Decimal
    with ROUND_HALF_UP. Walks dicts and lists; leaves non-float scalars alone.
    """
    if isinstance(obj, float):
        return float(
            Decimal(repr(obj)).quantize(_ROUND_QUANTUM, rounding=ROUND_HALF_UP)
        )
    if isinstance(obj, dict):
        return {k: round_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [round_floats(v) for v in obj]
    return obj


def serialize_players(players: List["PlayerModel"]) -> List[Dict]:
    """
    Serialize a list of PlayerModel objects into a JSON-serializable dictionary.

    Args:
        players: List of PlayerModel objects

    Returns:
        List of dictionaries representing player data
    """
    logger = Logger("serialize_players")
    log = logger.logging
    log.debug(f"Starting serialization of {len(players)} players")

    player_data_list = []

    def _dump(model: Any) -> Dict[str, Any]:
        """Dump a projection model to dict, or return {} if model is missing.

        Both slots always serialize as dicts (empty when no data) so downstream
        consumers can rely on the shape — e.g. pre-draft players have `ros: {}`
        rather than `ros: null`.
        """
        if model is None or not hasattr(model, "model_dump"):
            return {}
        return model.model_dump(by_alias=True, exclude_none=True)

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task("Serializing players", total=len(players))
        for i, player in enumerate(players):
            try:
                # Ensure we have the basic player fields
                serialized_player: Dict[str, Any] = {
                    "name": getattr(player, "name", "unknown"),
                    "ascii_name": getattr(
                        player,
                        "ascii_name",
                        normalize_string(getattr(player, "name", "unknown")),
                    ),
                    "team": getattr(player, "team", "FA"),
                    "playerid": getattr(player, "playerid", "unknown"),
                    "xmlbam_id": getattr(player, "xmlbam_id", -1),
                    "slug": getattr(player, "slug", ""),
                    "stats_api": getattr(player, "stats_api", ""),
                    "projections": {},
                    "projs_updated": {},
                    "ros": {},
                }

                for slot in ("projections", "projs_updated", "ros"):
                    try:
                        serialized_player[slot] = _dump(getattr(player, slot, None))
                    except Exception as e:
                        log.error(f"Error processing {slot} for player {i + 1}: {e}")

                # Round all float values in the player record to 3 decimal places
                serialized_player = round_floats(serialized_player)

                player_data_list.append(serialized_player)

            except Exception as e:
                log.error(f"Error serializing player {i + 1}: {e}")

                # Still add basic info even if there's an error
                name = getattr(player, "name", "unknown")
                player_data_list.append(
                    {"name": name, "ascii_name": normalize_string(name), "error": str(e)}
                )
            finally:
                progress.update(task, advance=1)

    log.info(f"Completed serialization with {len(player_data_list)} results")

    return player_data_list


def save_extraction_results(
    pitchers: List["PlayerModel"],
    batters: List["PlayerModel"],
    output_dir: str,
    year: Optional[int] = None,
    timestamp: Optional[str] = None,
    indent: Optional[int] = 2,
) -> None:
    """
    Serialize and save extracted player data to JSON files.

    Args:
        pitchers: List of pitcher PlayerModel objects
        batters: List of batter PlayerModel objects
        output_dir: Directory path to write JSON output files
        year: Optional year to include in file names
        timestamp: Optional timestamp override (format: YYYYMMDD_HHMMSS)
        indent: Indentation level for JSON formatting
    """
    logger = Logger("save_extraction_results")
    log = logger.logging
    log.info(f"Saving {len(pitchers)} pitchers and {len(batters)} batters")

    os.makedirs(output_dir, exist_ok=True)
    timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")

    name_parts = ["fangraph_pitchers"]
    if year is not None:
        name_parts.append(str(year))
    name_parts.append(timestamp)
    pitcher_file_name = "_".join(name_parts) + ".json"

    name_parts = ["fangraph_batters"]
    if year is not None:
        name_parts.append(str(year))
    name_parts.append(timestamp)
    batter_file_name = "_".join(name_parts) + ".json"

    pitcher_data = serialize_players(pitchers)
    batter_data = serialize_players(batters)

    pitcher_path = os.path.join(output_dir, pitcher_file_name)
    batter_path = os.path.join(output_dir, batter_file_name)

    try:
        with open(pitcher_path, "w") as f:
            json.dump(pitcher_data, f, indent=indent)
        log.info(f"Saved {len(pitchers)} pitchers to {pitcher_path}")
    except Exception as e:
        log.error(f"Error writing pitchers to {pitcher_path}: {e}")

    try:
        with open(batter_path, "w") as f:
            json.dump(batter_data, f, indent=indent)
        log.info(f"Saved {len(batters)} batters to {batter_path}")
    except Exception as e:
        log.error(f"Error writing batters to {batter_path}: {e}")


def get_nested_values(
    data: Dict[str, Any], path: List[str | int]
) -> Dict | List | None:
    """Extract a value from nested dictionary following the given path."""
    current: Dict | List | None = data
    for key in path:
        if isinstance(key, int):
            assert isinstance(current, list), f"Expected list, got {type(current)}"
            current = current[key]
        elif isinstance(key, str):
            assert isinstance(current, dict), f"Expected dict, got {type(current)}"
            current = current.get(key, None)
    return current
