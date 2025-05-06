#!/usr/bin/env python
"""
Debug runner script for the Fangraphs API Extractor.
This script runs the player extractor and saves the output to a JSON file.
It uses the players.py runner to fetch both hitter and pitcher data.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fangraphs_api_extractor.runners.players import main

if __name__ == "__main__":
    # Set the output file to be in the project root
    output_file = os.path.join(project_root, "extracted_players.json")

    # Run the player extractor with real API data and save to the specified file
    print("===== RUNNING PLAYER EXTRACTOR WITH REAL API DATA =====")
    print("Fetching both hitter and pitcher projections...")
    players = main(
        use_test_data=False,  # Use real API data
        output_file=output_file,
        sample_size=20,  # Limit to 20 players for testing
    )

    print(
        f"Extraction complete! {len(players)} players extracted and saved to {output_file}"
    )

    # Print some information about players as a sanity check
    if players and len(players) > 0:
        # Find a pitcher to check stats_api property
        pitchers = [
            p
            for p in players
            if any(hasattr(proj, "era") for proj in p.projections.values())
        ]

        if pitchers:
            pitcher = pitchers[0]
            print("\nSample pitcher information:")
            print(f"Name: {pitcher.name}")
            print(f"Team: {pitcher.team}")
            print(f"Player ID: {pitcher.playerid}")
            print(f"Stats API: {pitcher.stats_api}")

            # Show available projection systems
            print(f"Available projection systems: {list(pitcher.projections.keys())}")

            # Show some key stats from the first projection system
            if pitcher.projections:
                proj_name = list(pitcher.projections.keys())[0]
                proj = pitcher.projections[proj_name]
                print(f"Projection ({proj_name}): {proj.wins} W, {proj.era} ERA")

        # Find a hitter to check
        hitters = [
            p
            for p in players
            if any(hasattr(proj, "hr") for proj in p.projections.values())
        ]

        if hitters:
            hitter = hitters[0]
            print("\nSample hitter information:")
            print(f"Name: {hitter.name}")
            print(f"Team: {hitter.team}")
            print(f"Player ID: {hitter.playerid}")
            print(f"Stats API: {hitter.stats_api}")

            # Show available projection systems
            print(f"Available projection systems: {list(hitter.projections.keys())}")

            # Show some key stats from the first projection system
            if hitter.projections:
                proj_name = list(hitter.projections.keys())[0]
                proj = hitter.projections[proj_name]
                print(f"Projection ({proj_name}): {proj.hr} HR, {proj.avg} AVG")

    print(
        f"Extraction complete! {len(players)} players extracted and saved to {output_file}"
    )

    # Print some information about the first player as a sanity check
    if players and len(players) > 0:
        first_player = players[0]
        print("\nSample player information:")
        print(f"Name: {first_player.name}")
        print(f"Team: {first_player.team}")
        print(f"Player ID: {first_player.playerid}")
        print(f"Stats API: {first_player.stats_api}")

        # Show available projection systems
        print(f"Available projection systems: {list(first_player.projections.keys())}")

        # Show some key stats from the first projection system
        if first_player.projections:
            proj_name = list(first_player.projections.keys())[0]
            proj = first_player.projections[proj_name]

            # For a hitter
            if hasattr(proj, "hr") and hasattr(proj, "avg"):
                print(f"Projection ({proj_name}): {proj.hr} HR, {proj.avg} AVG")
            # For a pitcher
            elif hasattr(proj, "era") and hasattr(proj, "wins"):
                print(f"Projection ({proj_name}): {proj.wins} W, {proj.era} ERA")
