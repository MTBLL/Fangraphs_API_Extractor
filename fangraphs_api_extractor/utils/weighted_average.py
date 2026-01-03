"""
Weighted averaging utilities for projection data.

This module provides functions to calculate weighted averages across multiple
projection sources for baseball player statistics.
"""

from typing import Any, Dict, List, Mapping, Union

from fangraphs_api_extractor.models.base_player import BaseProjectionModel
from fangraphs_api_extractor.models.hitter import HitterProjectionModel
from fangraphs_api_extractor.models.pitcher import PitcherProjectionModel


def calculate_weighted_average_projections(
    projections: Mapping[str, BaseProjectionModel], weights: Mapping[str, float]
) -> Dict[str, Any]:
    """
    Calculate weighted average of projections from multiple sources.

    Handles cases where not all sources have the same stats available by
    redistributing missing weight evenly among sources that have each stat.
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
    averaged: Dict[str, Any] = {}

    # Get all fields from the model class (not instance)
    for field_name, field_info in first_proj.__class__.model_fields.items():
        # Skip metadata fields that shouldn't be averaged
        if field_name in ["source", "percentiles"]:
            continue

        values_to_average = []
        weights_to_use = []
        missing_weight = 0.0
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
            else:
                missing_weight += weights[source_name]

        # Calculate weighted average if we have values
        if values_to_average and weights_to_use:
            # Split missing weight evenly across sources with values for this field.
            if missing_weight > 0:
                redistributed = missing_weight / len(weights_to_use)
                weights_to_use = [w + redistributed for w in weights_to_use]

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
                    averaged[field_name] = float(weighted_sum)

    return averaged


def merge_player_projections(
    players_by_source: Mapping[str, List[Any]], weights: Mapping[str, float]
) -> List[Any]:
    """
    Merge player projections from multiple sources with weighted averaging.

    Takes players fetched from different projection sources and combines them,
    calculating weighted averages for all projection fields. Handles cases where
    sources have different stats available by redistributing missing weight evenly.
    Aggregates per-source projections onto a single player per playerid and
    clears transient projections after merging.

    Args:
        players_by_source: Dictionary mapping source name to list of PlayerModel objects
        weights: Dictionary mapping source names to normalized weights

    Returns:
        List of PlayerModel objects with a single weighted projection

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
    players_by_id: Dict[str, Any] = {}

    # First pass: collect all players and attach projections to the base player
    for source_name, players in players_by_source.items():
        for player in players:
            player_id = player.playerid

            base_player = players_by_id.get(player_id)
            if base_player is None:
                base_player = player
                players_by_id[player_id] = base_player

            source_projections = getattr(player, "_source_projections", None)
            if source_projections:
                if source_projections is not base_player._source_projections:
                    base_player._source_projections.update(source_projections)
            else:
                projection = getattr(player, "projection", None)
                if projection is not None:
                    base_player._source_projections[source_name] = projection

            if player is not base_player:
                player.projection = None
                if hasattr(player, "_source_projections"):
                    player._source_projections.clear()

    # Second pass: calculate weighted averages for each player
    for player in players_by_id.values():
        projections = player._source_projections
        if len(projections) > 1:
            averaged_proj = calculate_weighted_average_projections(projections, weights)
            if averaged_proj:
                first_proj = next(iter(projections.values()))
                avg_model: Union[
                    HitterProjectionModel, PitcherProjectionModel, BaseProjectionModel
                ]
                match first_proj:
                    case HitterProjectionModel():
                        avg_model = HitterProjectionModel(**averaged_proj)
                    case PitcherProjectionModel():
                        avg_model = PitcherProjectionModel(**averaged_proj)
                    case _:
                        avg_model = BaseProjectionModel(**averaged_proj)
                player.projection = avg_model
            else:
                player.projection = next(iter(projections.values()))
        elif projections:
            player.projection = next(iter(projections.values()))
        else:
            player.projection = None

        player._source_projections.clear()

    return list(players_by_id.values())
