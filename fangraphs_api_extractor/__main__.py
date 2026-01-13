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
        help="Comma-separated list of projection sources (e.g., 'steamer,fangraphsdc,zips,atc,thebatx,oopsy'). Overrides --winter_meetings.",
    )
    parser.add_argument(
        "--pitcher-sources",
        "-p",
        type=str,
        default=None,
        help="Comma-separated list of projection sources (e.g., 'steamer,fangraphsdc,zips,atc,thebat,oopsy'). Overrides --winter_meetings.",
    )
    parser.add_argument(
        "--weights",
        "-w",
        type=str,
        default=None,
        help="Comma-separated integer weights for sources (e.g., '75,25' for 75%% and 25%%). Must match number of sources. If not provided, equal weights used.",
    )
    parser.add_argument(
        "--winter-meetings",
        action="store_true",
        help="Use winter meetings projection mix (thebatx 50%%, fangraphsdc 50%%, plus steamer for qq/tt only). Default is regular season mix (thebatx 50%%, fangraphsdc 25%%, atc 25%%, plus steamer for qq/tt only).",
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
            # Custom sources provided - use these regardless of --winter_meetings flag
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
        elif args.winter_meetings:
            # Winter meetings mode: thebatx (50%) + fangraphsdc (50%) + steamer (qq/tt only)
            sources = {
                "batters": ["thebatx", "fangraphsdc", "steamer"],
                "pitchers": ["oopsy", "fangraphsdc", "steamer"],
            }
            weights = [50.0, 50.0, 0.0]  # steamer weight is 0 (qq/tt fields only)
        else:
            # Default regular season mode: thebatx (50%) + fangraphsdc (25%) + atc (25%) + steamer (qq/tt only)
            sources = {
                "batters": ["thebatx", "fangraphsdc", "atc", "steamer"],
                "pitchers": ["oopsy", "fangraphsdc", "atc", "steamer"],
            }
            weights = [50.0, 25.0, 25.0, 0.0]  # steamer weight is 0 (qq/tt fields only)

        # Normalize weights to sum to 1.0
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
