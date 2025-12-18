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
        "-o",
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
    parser.add_argument(
        "--sources",
        "-s",
        type=str,
        default=None,
        help="Comma-separated list of projection sources (e.g., 'steamer,fangraphsdc,zips,atc'). Overrides --winter_meetings.",
    )
    parser.add_argument(
        "--weights",
        "-w",
        type=str,
        default=None,
        help="Comma-separated integer weights for sources (e.g., '75,25' for 75%% and 25%%). Must match number of sources. If not provided, equal weights used.",
    )
    parser.add_argument(
        "--winter_meetings",
        action="store_true",
        help="Use winter meetings projection mix (steamer 75%%, fangraphsdc 25%%). Default is nominal mix (atc 50%%, steamer 25%%, zips 25%%).",
    )

    return parser.parse_args()


def main():
    """Main CLI entry point."""
    args = parse_args()

    try:
        # Determine sources and weights based on flags
        if args.sources:
            # Custom sources provided - use these regardless of --winter_meetings flag
            sources = [s.strip() for s in args.sources.split(",")]

            # Parse weights
            if args.weights:
                weights = [int(w.strip()) for w in args.weights.split(",")]
                if len(weights) != len(sources):
                    print(
                        f"Error: Number of weights ({len(weights)}) must match number of sources ({len(sources)})"
                    )
                    sys.exit(1)
            else:
                # Equal weights if not provided
                weights = [1] * len(sources)
        elif args.winter_meetings:
            # Winter meetings mode: steamer (75%) + fangraphsdc (25%)
            sources = ["steamer", "fangraphsdc"]
            weights = [75, 25]
        else:
            # Default nominal mode: atc (50%) + steamer (25%) + zips (25%)
            sources = ["atc", "steamer", "zips"]
            weights = [50, 25, 25]

        # Normalize weights to sum to 1.0
        total_weight = sum(weights)
        normalized_weights = {
            source: weight / total_weight for source, weight in zip(sources, weights)
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
