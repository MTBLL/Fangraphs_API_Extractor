#!/usr/bin/env python
"""
Debug runner script for the Fangraphs API Extractor.
This script runs the player extractor and saves the output to JSON files.
It mimics the main entry point but with additional debug output.
"""

import sys
from pathlib import Path

from fangraphs_api_extractor.runners import PlayerRunner

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Debug entry point."""
    print("===== RUNNING PLAYER EXTRACTOR WITH REAL API DATA =====")
    print("Fetching both hitter and pitcher projections...")

    try:
        # Initialize the extractor
        extractor = PlayerRunner(
            year=2025,
            threads=None,  # Use default (4x CPU cores)
            batch_size=100,
        )

        # Run the extraction with sample size for debugging
        players = extractor.run(
            sample_size=20,  # Limit to 20 players for testing
            output_dir=str(project_root),  # Save to project root
        )

        if not players:
            print("Extraction failed - no players returned")
            sys.exit(1)

        print(f"\nExtraction complete! {len(players)} players extracted")

        # Print some information about players as a sanity check
        # Find a pitcher to check stats_api property
        pitchers = [
            p
            for p in players
            if getattr(p, "projection", None) is not None
            and hasattr(p.projection, "era")
        ]

        if pitchers:
            pitcher = pitchers[0]
            print("\n--- Sample pitcher information ---")
            print(f"Name: {pitcher.name}")
            print(f"Team: {pitcher.team}")
            print(f"Player ID: {pitcher.playerid}")
            print(f"Stats API: {pitcher.stats_api}")
            # Show some key stats from the projection
            if pitcher.projection:
                proj = pitcher.projection
                print(
                    f"Projection: {getattr(proj, 'wins', 'N/A')} W, {getattr(proj, 'era', 'N/A')} ERA"
                )

        # Find a hitter to check
        hitters = [
            p
            for p in players
            if getattr(p, "projection", None) is not None
            and hasattr(p.projection, "hr")
        ]

        if hitters:
            hitter = hitters[0]
            print("\n--- Sample hitter information ---")
            print(f"Name: {hitter.name}")
            print(f"Team: {hitter.team}")
            print(f"Player ID: {hitter.playerid}")
            print(f"Stats API: {hitter.stats_api}")
            # Show some key stats from the projection
            if hitter.projection:
                proj = hitter.projection
                print(
                    f"Projection: {getattr(proj, 'hr', 'N/A')} HR, {getattr(proj, 'avg', 'N/A')} AVG"
                )

        sys.exit(0)

    except Exception as e:
        print(f"\nError during extraction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
