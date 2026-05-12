"""
CLI entry point for the Fangraphs API Extractor package.

Each run pulls three independent projection sets per player:
  - projections: canonical pre-season full-year mix
  - updates:     in-season-refit full-year mix (uzips + steameru)
  - ros:         rest-of-season mix

Pre-draft, the `updates` and `ros` fetches return empty and those slots
serialize as {}. There is no separate pre-draft "mode" — the same defaults
work year-round because empty data is handled gracefully.
"""

import argparse
import sys
from typing import Dict, List

from fangraphs_api_extractor.runners import PlayerRunner
from fangraphs_api_extractor.utils.constants import (
    DEFAULT_PROJECTIONS_SOURCES,
    DEFAULT_PROJECTIONS_WEIGHTS,
    DEFAULT_ROS_SOURCES,
    DEFAULT_ROS_WEIGHTS,
    DEFAULT_UPDATES_SOURCES,
    DEFAULT_UPDATES_WEIGHTS,
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
        help="Comma-separated list of projection sources for the `projections` slot only "
        "(e.g., 'thebatx,fangraphsdc,atc,steamer'). Does not affect the `updates` or `ros` "
        "slots — those continue to use their defaults. For per-slot overrides on updates/ros, "
        "use the Python API.",
    )
    parser.add_argument(
        "--pitcher-sources",
        "-p",
        type=str,
        default=None,
        help="Comma-separated list of pitcher projection sources for the `projections` slot only. "
        "See --batter-sources notes.",
    )
    parser.add_argument(
        "--weights",
        "-w",
        type=str,
        default=None,
        help="Comma-separated weights for sources passed via --batter-sources / --pitcher-sources "
        "(e.g., '50,25,25,0'). Must match the number of sources. If omitted, equal weights are used.",
    )

    return parser.parse_args()


def _build_custom_projections_slot(
    args: argparse.Namespace,
) -> tuple[Dict[str, List[str]], Dict[str, Dict[str, float]]]:
    """Build a custom `projections` slot from CLI overrides."""
    if not args.batter_sources or not args.pitcher_sources:
        print(
            "Error: --batter-sources and --pitcher-sources must both be provided "
            "when overriding the `projections` slot via the CLI."
        )
        sys.exit(1)

    batters = [s.strip() for s in args.batter_sources.split(",")]
    pitchers = [s.strip() for s in args.pitcher_sources.split(",")]

    if len(batters) != len(pitchers):
        print(
            f"Error: --batter-sources has {len(batters)} entries but "
            f"--pitcher-sources has {len(pitchers)}. They must match because "
            "--weights is a single list applied positionally to both."
        )
        sys.exit(1)

    if args.weights:
        raw_weights = [float(w.strip()) for w in args.weights.split(",")]
        if len(raw_weights) != len(batters):
            print(
                f"Error: --weights has {len(raw_weights)} entries; must match "
                f"the {len(batters)} sources."
            )
            sys.exit(1)
    else:
        raw_weights = [1.0] * len(batters)

    total = sum(raw_weights)
    if total <= 0:
        print("Error: --weights must sum to > 0.")
        sys.exit(1)

    sources = {"batters": batters, "pitchers": pitchers}
    weights = {
        "batters": {s: w / total for s, w in zip(batters, raw_weights)},
        "pitchers": {s: w / total for s, w in zip(pitchers, raw_weights)},
    }
    return sources, weights


def main():
    """Main CLI entry point."""
    args = parse_args()
    try:
        if args.batter_sources or args.pitcher_sources:
            proj_sources, proj_weights = _build_custom_projections_slot(args)
        else:
            proj_sources = DEFAULT_PROJECTIONS_SOURCES
            proj_weights = DEFAULT_PROJECTIONS_WEIGHTS

        sources = {
            "projections": proj_sources,
            "projs_updated": DEFAULT_UPDATES_SOURCES,
            "ros": DEFAULT_ROS_SOURCES,
        }
        weights = {
            "projections": proj_weights,
            "projs_updated": DEFAULT_UPDATES_WEIGHTS,
            "ros": DEFAULT_ROS_WEIGHTS,
        }

        extractor = PlayerRunner(
            year=args.year,
            threads=args.threads,
            batch_size=args.batch_size,
            sources=sources,
            weights=weights,
        )

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
