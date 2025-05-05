import argparse
from typing import List, Optional, Union

from fangraphs_api_extractor.requests.core_fangraphs import CoreFangraphs
from fangraphs_api_extractor.utils import Logger


def main(
    sample_size: Optional[int] = None,
    output_file: Optional[str] = None,
    pretty: bool = True,
) -> Union[List[Player], List[PlayerModel]]:
    """
    Main function to extract player data from Fangraphs Baseball API.

    Args:
        sample_size: Optional maximum number of players to process. If provided,
                    this will limit API calls to save time when only a sample is needed.
        output_file: Optional path to write the JSON output. If None, no file is written.
        pretty: Whether to pretty-print the JSON output with indentation.

    Returns:
        Either a list of Player objects or PlayerModel objects (if as_models=True)
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
        "--as-models",
        action="store_true",
        help="Return Pydantic models instead of Player objects (default: False)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to write JSON output. If not specified, no file is written.",
    )

    args = parser.parse_args()

    # Override args with function parameters if provided
    if output_file is not None:
        args.output = output_file

    logger = Logger("fangraphs-player-extractor")
    year = args.year

    cf = CoreFangraphs(year=year, logger=logger)


if __name__ == "__main__":
    main()
