"""
Weighted averaging utilities for projection data.

This module provides functions to calculate weighted averages across multiple
projection sources for baseball player statistics.
"""

from typing import Any, Dict, List, Mapping, Union

from fangraphs_api_extractor.models import PlayerModel
from fangraphs_api_extractor.models.base_player import BaseProjectionModel
from fangraphs_api_extractor.models.hitter import HitterProjectionModel
from fangraphs_api_extractor.models.pitcher import PitcherProjectionModel


def _calculate_weighted_average_projections(
    projections: Mapping[str, BaseProjectionModel], weights: Mapping[str, float]
) -> Dict[str, Any]:
    """
    Calculate weighted average of projections from multiple sources.

    Handles cases where not all sources have the same stats available by
    redistributing missing weight evenly among sources that have each stat.
    Preserves integer types by rounding when appropriate.

    Special handling for Steamer source: Only qq and tt percentile fields are used
    from Steamer when its weight is 0. All other fields are ignored.

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

    # Steamer-family sources contribute qq/tt percentiles even at weight 0.
    # Both pre-season (steamer) and rest-of-season (steamerr) emit these fields.
    steamer_family = {"steamer", "steamerr"}

    # Define Steamer-only fields (qq and tt percentiles)
    # Note: qq values represent wOBA percentiles for hitters, RA/9 percentiles for pitchers
    #       tt values represent true talent (stabilized) percentiles
    steamer_only_fields = {
        "q10",
        "q20",
        "q30",
        "q40",
        "q50",
        "q60",
        "q70",
        "q80",
        "q90",
        "tt_q10",
        "tt_q20",
        "tt_q30",
        "tt_q40",
        "tt_q50",
        "tt_q60",
        "tt_q70",
        "tt_q80",
        "tt_q90",
    }

    # Get field names from first projection (all should have same structure)
    first_proj = next(iter(projections.values()))

    # Initialize result dictionary
    averaged: Dict[str, Any] = {}

    # Include computed fields (like svhd) in addition to model fields
    field_names = list(first_proj.__class__.model_fields.keys())
    computed_fields = getattr(first_proj.__class__, "model_computed_fields", {}) or {}
    for field_name in computed_fields.keys():
        if field_name not in field_names:
            field_names.append(field_name)

    # Get all fields from the model class (not instance)
    for field_name in field_names:
        # Skip metadata fields that shouldn't be averaged
        if field_name in ["source", "percentiles"]:
            continue

        values_to_average = []
        weights_to_use = []
        missing_weight = 0.0
        is_integer_field = False

        # Determine if this field should use Steamer data
        is_steamer_only_field = field_name in steamer_only_fields

        # Collect values and weights from each source
        for source_name, projection in projections.items():
            if source_name not in weights:
                continue

            # Special handling for Steamer-family source with weight 0
            if source_name in steamer_family and weights[source_name] == 0:
                # Only include Steamer for qq and tt fields
                if not is_steamer_only_field:
                    continue

            field_value = getattr(projection, field_name, None)

            # Only include non-None values in the average
            if field_value is not None:
                # Check if original value is an integer
                if isinstance(field_value, int):
                    is_integer_field = True

                values_to_average.append(float(field_value))
                # For Steamer-family qq/tt fields with weight 0, use full weight
                if (
                    source_name in steamer_family
                    and weights[source_name] == 0
                    and is_steamer_only_field
                ):
                    weights_to_use.append(1.0)
                else:
                    weights_to_use.append(weights[source_name])
            else:
                # Only count missing weight for non-Steamer sources or non-qq/tt fields
                if not (
                    source_name in steamer_family
                    and weights[source_name] == 0
                    and not is_steamer_only_field
                ):
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
    players_by_source: Mapping[str, List[PlayerModel]],
    weights: Mapping[str, float],
    target_slot: str = "projections",
) -> List[PlayerModel]:
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
                # parse_player attaches the parsed projection to `.projections`
                projection = getattr(player, "projections", None)
                if projection is not None:
                    base_player._source_projections[source_name] = projection

            if player is not base_player:
                player.projections = None
                if hasattr(player, "_source_projections"):
                    player._source_projections.clear()

    # Second pass: calculate weighted averages for each player and write the
    # result into the target slot (`projections` for full-year, `ros` for RoS).
    for player in players_by_id.values():
        projections = player._source_projections
        merged: Optional[
            Union[HitterProjectionModel, PitcherProjectionModel, BaseProjectionModel]
        ]
        if len(projections) > 1:
            averaged_proj = _calculate_weighted_average_projections(
                projections, weights
            )
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
                merged = avg_model
            else:
                merged = next(iter(projections.values()))
        elif projections:
            merged = next(iter(projections.values()))
        else:
            merged = None

        setattr(player, target_slot, merged)
        # If the merge target isn't `projections`, clear out the transient value
        # that parse_player wrote there.
        if target_slot != "projections":
            player.projections = None

        player._source_projections.clear()

    return list(players_by_id.values())
