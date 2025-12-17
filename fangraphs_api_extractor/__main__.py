"""
CLI entry point for the Fangraphs API Extractor package.

This module provides command-line interface functionality for extracting
player data from the Fangraphs Baseball API.
"""

import argparse
import sys

from fangraphs_api_extractor.runners import PlayerRunner


def parse_args():
    """Parse command line arguments."""
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
        "--batch_size",
        type=int,
        default=100,
        help="Number of players to process in each batch for progress tracking (default: 100)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=".",
        help="Path to write JSON output (default: current directory)",
    )
    parser.add_argument(
        "--sample_size",
        type=int,
        default=None,
        help="Optional maximum number of players to process for sampling",
    )

    return parser.parse_args()


def main():
    """Main CLI entry point."""
    args = parse_args()

    try:
        # Initialize the extractor
        extractor = PlayerRunner(
            year=args.year,
            threads=args.threads,
            batch_size=args.batch_size,
        )

        # Run the extraction
        players = extractor.run(
            sample_size=args.sample_size,
            output_dir=args.output_dir,
        )

        if players:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
