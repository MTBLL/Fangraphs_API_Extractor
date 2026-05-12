"""
CLI entry point for the Fangraphs API Extractor package.

This module provides command-line interface functionality for extracting
player data from the Fangraphs Baseball API.
"""

import argparse
import sys

from fangraphs_api_extractor.runners import PlayerRunner
from fangraphs_api_extractor.utils.constants import (
    DEFAULT_PREDRAFT_SOURCES,
    DEFAULT_PREDRAFT_WEIGHTS,
    DEFAULT_ROS_SOURCES,
    DEFAULT_ROS_WEIGHTS,
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Access Fangraphs Baseball API")

    parser.add_argument(
        "--year", type=int, default=2026, help="League year (default: 2026)"
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
        "--output-dir",
        "-o",
        type=str,
        default=".",
        help="Path to write JSON output (default: current directory)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Optional maximum number of players to process for sampling",
    )
    parser.add_argument(
        "--batter-sources",
        "-s",
        type=str,
        default=None,
        help="Comma-separated list of projection sources (e.g., 'rthebatx,rfangraphsdc,ratcdc,steamerr'). Overrides --predraft.",
    )
    parser.add_argument(
        "--pitcher-sources",
        "-p",
        type=str,
        default=None,
        help="Comma-separated list of projection sources (e.g., 'roopsydc,rfangraphsdc,ratcdc,steamerr'). Overrides --predraft.",
    )
    parser.add_argument(
        "--weights",
        "-w",
        type=str,
        default=None,
        help="Comma-separated integer weights for sources (e.g., '75,25' for 75%% and 25%%). Must match number of sources. If not provided, equal weights used.",
    )
    parser.add_argument(
        "--predraft",
        action="store_true",
        help="Use the pre-draft (preseason) projection mix: thebatx/oopsy 50%%, fangraphsdc 25%%, atc 25%%, plus steamer for qq/tt only. Default (no flag) is the rest-of-season mix.",
    )

    return parser.parse_args()


def main():
    """Main CLI entry point."""
    args = parse_args()
    sources: dict = {}
    weights: list[float] = []
    try:
        # Determine sources and weights based on flags
        if args.batter_sources:
            # Custom sources provided - use these regardless of --predraft flag
            sources["batters"] = [s.strip() for s in args.batter_sources.split(",")]

            # Parse weights
            if args.weights:
                weights = [float(w.strip()) for w in args.weights.split(",")]
                if len(weights) != len(sources.get("batters", [])):
                    print(
                        f"Error: Number of weights ({len(weights)}) must match number of sources ({len(sources.get('batters', []))})"
                    )
                    sys.exit(1)
            else:
                # Equal weights if not provided
                weights = [1.0] * len(sources.get("batters", []))
        if args.pitcher_sources:
            sources["pitchers"] = [s.strip() for s in args.pitcher_sources.split(",")]

            if args.weights:
                weights = [float(w.strip()) for w in args.weights.split(",")]
                if len(weights) != len(sources.get("pitchers", [])):
                    print(
                        f"Error: Number of weights ({len(weights)}) must match number of sources ({len(sources.get('pitchers', []))})"
                    )
                    sys.exit(1)
            else:
                # Equal weights if not provided
                weights = [1.0] * len(sources.get("pitchers", []))
        elif args.predraft:
            sources = DEFAULT_PREDRAFT_SOURCES
            normalized_weights = DEFAULT_PREDRAFT_WEIGHTS
        else:
            # Daily in-season default: rest-of-season projections
            sources = DEFAULT_ROS_SOURCES
            normalized_weights = DEFAULT_ROS_WEIGHTS

        # Normalize weights for custom sources; default mixes are pre-normalized
        if weights:
            total_weight = sum(weights)
            assert "batters" in sources.keys()
            normalized_weights = {
                "batters": {
                    source: weight / total_weight
                    for source, weight in zip(sources["batters"], weights)
                },
                "pitchers": {
                    source: weight / total_weight
                    for source, weight in zip(sources["pitchers"], weights)
                },
            }

        # Initialize the extractor
        extractor = PlayerRunner(
            year=args.year,
            threads=args.threads,
            batch_size=args.batch_size,
            sources=sources,
            weights=normalized_weights,
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
