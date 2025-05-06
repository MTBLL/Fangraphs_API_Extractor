# Fangraphs API Extractor
[![codecov](https://codecov.io/gh/MTBLL/Fangraphs_API_Extractor/graph/badge.svg?token=Vk0FSuR25F)](https://codecov.io/gh/MTBLL/Fangraphs_API_Extractor)
A Python package for extracting and parsing player data from Fangraphs projections into structured Pydantic models.

## Features

- Extract player data from Fangraphs projection systems (Steamer, ATC, THE BAT, etc.)
- Parse JSON responses into strongly-typed Pydantic models
- Support for both hitters and pitchers
- Handle multiple projection sources for the same player
- Pythonic access to player stats with proper naming conventions

## Installation

```bash
# Install from the current directory
poetry install

# Or if you're installing from a repo
pip install git+https://github.com/username/fangraphs-api-extractor.git
```

## Usage

### Basic Example

```python
from fangraphs_api_extractor.models.hitter import Hitter
from fangraphs_api_extractor.requests.core_fangraphs import CoreFangraphs
from fangraphs_api_extractor.utils.logger import Logger

# Create a logger
logger = Logger()

# Create FanGraphs API client
fangraphs = CoreFangraphs(logger=logger)

# Get data from Fangraphs API
hitter_data = fangraphs.get_projections_data(position_group="bat", position="all", projections_system="steamer")

# Parse the data into player models
from fangraphs_api_extractor.managers.players_manager import parse_players
players = parse_players(hitter_data, logger)
player = players[0]  # Get first player as example

# Access player information
print(f"Player: {player.name} ({player.team})")
print(f"Position: {player.min_position}")
print(f"Player slug: {player.slug}")  # Useful for URLs 
print(f"Stats API endpoint: {player.stats_api}")  # Ready-to-use API endpoint

# Access projection data
projection = player.projections["steamer"]
print(f"Projected HR: {projection.hr}")
print(f"Projected AVG/OBP/SLG: {projection.avg}/{projection.obp}/{projection.slg}")
print(f"Projected WAR: {projection.war}")
```

### Using the Player Manager

If you have data for multiple players from the Fangraphs API, you can parse them all at once:

```python
from fangraphs_api_extractor.managers.players_manager import parse_players
from fangraphs_api_extractor.requests.core_fangraphs import CoreFangraphs
from fangraphs_api_extractor.utils.logger import Logger

# Create a logger
logger = Logger()

# Create FanGraphs API client
fangraphs = CoreFangraphs(logger=logger)

# Get data for all hitters with Steamer projections
response_data = fangraphs.get_projections_data(position_group="bat", position="all", projections_system="steamer")

# Parse all players at once
players = parse_players(response_data, logger)

# Now you have a list of player models
print(f"Found {len(players)} players")

# You can filter or sort them as needed
power_hitters = [p for p in players if p.projections["steamer"].hr >= 30]
for player in power_hitters:
    print(f"{player.name}: {player.projections['steamer'].hr} HR")
```

### Adding Multiple Projections

```python
# Create a logger
logger = Logger()

# Create FanGraphs API client
fangraphs = CoreFangraphs(logger=logger)

# First get data for the first projection system
steamer_data = fangraphs.get_projections_data(
    position_group="pit", 
    params={"playerid": "33677"}, 
    projections_system="steamer"
)
players = parse_players(steamer_data, logger)
player = players[0]  # Assuming player was found

# Then get data for additional projection systems
atc_data = fangraphs.get_projections_data(
    position_group="pit", 
    params={"playerid": "33677"}, 
    projections_system="atc"
)
atc_players = parse_players(atc_data, logger)
atc_player = atc_players[0]  # Assuming player was found

# Add the new projection to the player
player.projections["atc"] = atc_player.projections["atc"]

# Compare projections
print(f"Steamer ERA: {player.projections['steamer'].era}")
print(f"ATC ERA: {player.projections['atc'].era}")
print(f"{player.name}'s Projection Comparison: Steamer: {player.projections['steamer'].war} WAR, ATC: {player.projections['atc'].war} WAR")
```

## Data Models

### Player Models

- `BasePlayer`: Base model for all players with common identification fields
  - Properties:
    - `slug`: Generates a URL-friendly version of the player name
    - `stats_api`: Generates a stats API endpoint for the player
  - Validators:
    - `handle_null_team`: Converts None team values to 'FA' for free agents
    - `handle_null_ids`: Converts None ID values to -1
- `Hitter`: Model for hitters
- `Pitcher`: Model for pitchers

### Projection Models

- Each player model contains projections from various systems in a dictionary format
- Projection data is included directly in player models
- Automatically converts decimal stat values to integers where appropriate (e.g., HR, H)
- Handles raw projection data from Fangraphs API
- Special processing for all statistical values based on type

### Manager Functions

- `parse_players()`: Parses multiple player data records from the Fangraphs API response
  - Takes the raw API response with nested data structure
  - Requires a logger parameter for proper logging
  - Returns a list of typed player models with their projections

### Core Components

- `CoreFangraphs`: Handles all direct API interactions with Fangraphs
  - Only responsible for fetching raw data, not parsing
  - Requires a logger parameter for proper logging
  - Main method: `get_projections_data()` for retrieving player projections

### Utilities

- `Logger`: Custom logging utility for consistent logging across the application
  - Required parameter for most functions
  - Provides consistent logging format and error handling
- Utility functions for serializing players and writing JSON files
  - All require a logger parameter

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/MTBLL/Fangraphs_API_Extractor.git
cd Fangraphs_API_Extractor

# Install dependencies
poetry install
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=fangraphs_api_extractor

# Run specific test file
poetry run pytest tests/models/test_hitter.py
```

### Debugging

For debugging and testing the data extraction:

```bash
# Run the debug extraction script (gets both hitters and pitchers)
python debug/run_player_extractor.py
```

This will:
1. Fetch both hitter and pitcher data from Fangraphs
2. Parse the data into player models
3. Serialize the data and save it to a JSON file (extracted_players.json)
4. Log details about the extraction process

## License

[MIT License](LICENSE)
