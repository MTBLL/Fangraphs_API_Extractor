import argparse
from typing import List, Optional, Union

from fangraphs_api_extractor.managers import PlayersManager
from fangraphs_api_extractor.models import PlayerModel
from fangraphs_api_extractor.requests.core_fangraphs import CoreFangraphs
from fangraphs_api_extractor.utils import Logger, serialize_players, write_json_file


def main(
    sample_size: Optional[int] = None,
    output_dir: Optional[str] = None,
    use_test_data: bool = False,
) -> Union[List[PlayerModel], None]:
    """
    Main function to extract player data from Fangraphs Baseball API.

    Args:
        sample_size: Optional maximum number of players to process. If provided,
                    this will limit API calls to save time when only a sample is needed.
        output_file: Optional path to write the JSON output. If None, no file is written.
        pretty: Whether to pretty-print the JSON output with indentation.
        use_test_data: If True, use test fixture data instead of making API calls.

    Returns:
        List of PlayerModel objects if successful, None otherwise
    """
    parser = argparse.ArgumentParser(description="Access Fangraphs Baseball API")

    parser.add_argument(
        "--year", type=int, default=2025, help="League year (default: 2025)"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="Number of threads to use for player hydration (default: 4x CPU cores)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of players to process in each batch for progress tracking (default: 100)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=".",
        help="Path to write JSON output.",
    )

    args = parser.parse_args()

    # Override args with function parameters if provided
    if output_dir is not None:
        args.output_dir = output_dir

    logger = Logger("fangraphs-player-extractor")
    log = logger.logging
    year = args.year

    cf = CoreFangraphs(year=year, logger=logger)
    hitters: List[PlayerModel] = []
    pitchers: List[PlayerModel] = []
    players: List[PlayerModel] = []

    # Get hitter projections
    log.info(f"Fetching hitter projections for {year}...")
    try:
        # Get raw hitter data from API
        hitter_data = cf.get_projections_data("bat")
        if hitter_data:
            hitters_manager = PlayersManager("hitters")
            # Parse the raw data into player models
            hitters = hitters_manager.parse_players(hitter_data)
            log.info(f"Parsed {len(hitters)} hitters")
            players.extend(hitters)
        else:
            log.warning("Failed to fetch hitter data")
            hitters = []
    except Exception as e:
        log.error(f"Error fetching hitter data: {e}")
        hitters = []

    # Get pitcher projections
    log.info(f"Fetching pitcher projections for {year}...")
    try:
        # Get raw pitcher data from API
        pitcher_data = cf.get_projections_data("pit")
        if pitcher_data:
            pitchers_manager = PlayersManager("pitchers")
            # Parse the raw data into player models
            pitchers = pitchers_manager.parse_players(pitcher_data)
            log.info(f"Parsed {len(pitchers)} pitchers")
            players.extend(pitchers)
        else:
            log.warning("Failed to fetch pitcher data")
            pitchers = []
    except Exception as e:
        log.error(f"Error fetching pitcher data: {e}")
        pitchers = []

    log.info(f"Total players: {len(players)}")

    # Apply sample size limit if provided
    if sample_size and sample_size < len(players):
        log.info(f"Limiting to sample of {sample_size} players")
        limited_hitters = hitters[: min(sample_size, len(hitters))]
        limited_pitchers = pitchers[: min(sample_size, len(pitchers))]
        players = limited_hitters + limited_pitchers
        log.info(f"Limited to {len(players)} players")

    # Serialize player data
    player_data = serialize_players(players, logger)

    # Write to file if output path is provided
    if args.output_dir:
        write_json_file(player_data, args.output_dir, "fangraph_players.json", logger)

    return players


if __name__ == "__main__":
    main()
