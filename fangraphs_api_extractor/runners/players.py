import argparse
from typing import List, Optional, Union

from fangraphs_api_extractor.managers.players_manager import parse_players
from fangraphs_api_extractor.models import PlayerModel
from fangraphs_api_extractor.requests.core_fangraphs import CoreFangraphs
from fangraphs_api_extractor.utils import Logger, serialize_players, write_json_file


def main(
    sample_size: Optional[int] = None,
    output_file: Optional[str] = None,
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
        "--output",
        type=str,
        default="player_data.json",
        help="Path to write JSON output. Default: player_data.json in current directory.",
    )

    args = parser.parse_args()

    # Override args with function parameters if provided
    if output_file is not None:
        args.output = output_file

    logger = Logger("fangraphs-player-extractor")
    year = args.year

    cf = CoreFangraphs(year=year, logger=logger)
    hitters: List[PlayerModel] = []
    pitchers: List[PlayerModel] = []
    players: List[PlayerModel] = []

    # Get hitter projections
    logger.logging.info(f"Fetching hitter projections for {year}...")
    try:
        # Get raw hitter data from API
        hitter_data = cf.get_projections_data("bat")
        if hitter_data:
            # Parse the raw data into player models
            hitters = parse_players(hitter_data, logger)
            logger.logging.info(f"Parsed {len(hitters)} hitters")
            players.extend(hitters)
        else:
            logger.logging.warning("Failed to fetch hitter data")
            hitters = []
    except Exception as e:
        logger.logging.error(f"Error fetching hitter data: {e}")
        hitters = []

    # Get pitcher projections
    logger.logging.info(f"Fetching pitcher projections for {year}...")
    try:
        # Get raw pitcher data from API
        pitcher_data = cf.get_projections_data("pit")
        if pitcher_data:
            # Parse the raw data into player models
            pitchers = parse_players(pitcher_data, logger)
            logger.logging.info(f"Parsed {len(pitchers)} pitchers")
            players.extend(pitchers)
        else:
            logger.logging.warning("Failed to fetch pitcher data")
            pitchers = []
    except Exception as e:
        logger.logging.error(f"Error fetching pitcher data: {e}")
        pitchers = []

    logger.logging.info(f"Total players: {len(players)}")

    # Apply sample size limit if provided
    if sample_size and sample_size < len(players):
        logger.logging.info(f"Limiting to sample of {sample_size} players")
        limited_hitters = hitters[:min(sample_size, len(hitters))]
        limited_pitchers = pitchers[:min(sample_size, len(pitchers))]
        players = limited_hitters + limited_pitchers
        logger.logging.info(f"Limited to {len(players)} players")

    # Serialize player data
    player_data = serialize_players(players, logger)

    # Write to file if output path is provided
    if args.output:
        write_json_file(player_data, args.output, logger, indent=2)

    return players


if __name__ == "__main__":
    main()
