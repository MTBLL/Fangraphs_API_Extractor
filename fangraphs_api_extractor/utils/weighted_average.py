"""
Weighted averaging utilities for projection data.

This module provides functions to calculate weighted averages across multiple
projection sources for baseball player statistics.
"""

from typing import Any, Dict, List, Mapping

from fangraphs_api_extractor.models.base_player import BaseProjectionModel
from fangraphs_api_extractor.models.hitter import HitterProjectionModel
from fangraphs_api_extractor.models.pitcher import PitcherProjectionModel


def calculate_weighted_average_projections(
    projections: Mapping[str, BaseProjectionModel], weights: Mapping[str, float]
) -> Dict[str, Any]:
    """
    Calculate weighted average of projections from multiple sources.

    Handles cases where not all sources have the same stats available by
    redistributing weights proportionally among sources that have each stat.
    Preserves integer types by rounding when appropriate.

    Args:
        projections: Dictionary mapping source names to projection models
        weights: Dictionary mapping source names to normalized weights (sum to 1.0)

    Returns:
        Dictionary of averaged projection values

    Example:
        >>> projections = {
        ...     "steamer": HitterSteamerProjectionModel(...),
        ...     "fangraphsdc": HitterProjectionModel(...)
        ... }
        >>> weights = {"steamer": 0.75, "fangraphsdc": 0.25}
        >>> avg = calculate_weighted_average_projections(projections, weights)
    """
    if not projections:
        return {}

    # Get field names from first projection (all should have same structure)
    first_proj = next(iter(projections.values()))

    # Initialize result dictionary
    averaged = {}

    # Get all fields from the model class (not instance)
    for field_name, field_info in first_proj.__class__.model_fields.items():
        # Skip metadata fields that shouldn't be averaged
        if field_name in ["source", "percentiles"]:
            continue

        values_to_average = []
        weights_to_use = []
        is_integer_field = False

        # Collect values and weights from each source
        for source_name, projection in projections.items():
            if source_name not in weights:
                continue

            field_value = getattr(projection, field_name, None)

            # Only include non-None values in the average
            if field_value is not None:
                # Check if original value is an integer
                if isinstance(field_value, int):
                    is_integer_field = True

                values_to_average.append(float(field_value))
                weights_to_use.append(weights[source_name])

        # Calculate weighted average if we have values
        if values_to_average and weights_to_use:
            # Normalize weights for only the sources that have this field
            weight_sum = sum(weights_to_use)
            if weight_sum > 0:
                normalized_weights = [w / weight_sum for w in weights_to_use]
                weighted_sum = sum(
                    v * w for v, w in zip(values_to_average, normalized_weights)
                )

                # Round to integer if the field was originally an integer type
                if is_integer_field:
                    averaged[field_name] = int(round(weighted_sum))
                else:
                    averaged[field_name] = weighted_sum

    return averaged


def merge_player_projections(
    players_by_source: Mapping[str, List[Any]], weights: Mapping[str, float]
) -> List[Any]:
    """
    Merge player projections from multiple sources with weighted averaging.

    Takes players fetched from different projection sources and combines them,
    calculating weighted averages for all projection fields. Handles cases where
    sources have different stats available by redistributing weights proportionally.

    Args:
        players_by_source: Dictionary mapping source name to list of PlayerModel objects
        weights: Dictionary mapping source names to normalized weights

    Returns:
        List of PlayerModel objects with all source projections and averaged projections

    Example:
        >>> players_by_source = {
        ...     "steamer": [player1_steamer, player2_steamer],
        ...     "fangraphsdc": [player1_dc, player2_dc]
        ... }
        >>> weights = {"steamer": 0.75, "fangraphsdc": 0.25}
        >>> merged = merge_player_projections(players_by_source, weights)
    """
    if not players_by_source:
        return []

    # Build a dictionary of players by playerid
    players_by_id: Dict[int, Any] = {}

    # First pass: collect all players and their projections by ID
    for source_name, players in players_by_source.items():
        for player in players:
            player_id = player.playerid

            # Initialize player entry if not exists
            if player_id not in players_by_id:
                # Use the first player we encounter as the base
                players_by_id[player_id] = player
            else:
                # Merge projections from this source into the existing player
                if source_name in player.projections:
                    players_by_id[player_id].projections[source_name] = (
                        player.projections[source_name]
                    )

    # Second pass: calculate weighted averages for each player
    for player_id, player in players_by_id.items():
        if len(player.projections) > 1:
            # Calculate weighted average
            averaged_proj = calculate_weighted_average_projections(
                player.projections, weights
            )

            # Store averaged projection with a special key
            if averaged_proj:
                # Determine projection type using match statement
                first_proj = next(iter(player.projections.values()))
                match first_proj:
                    case HitterProjectionModel():
                        avg_model = HitterProjectionModel(**averaged_proj)
                    case PitcherProjectionModel():
                        avg_model = PitcherProjectionModel(**averaged_proj)
                    case _:
                        # Fallback to base model
                        avg_model = BaseProjectionModel(**averaged_proj)

                player.projections["weighted_average"] = avg_model

    return list(players_by_id.values())
