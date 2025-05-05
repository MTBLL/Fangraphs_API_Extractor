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
from fangraphs_api_extractor.models import PlayerModel
from fangraphs_api_extractor.requests import get_projection_data

# Get data from Fangraphs API
hitter_data = get_projection_data(player_id="25878", projection_system="steamer")

# Parse the data into a player model
player = PlayerModel.parse_player(hitter_data, projection_source="steamer")

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
from fangraphs_api_extractor.requests import get_all_projections

# Get data for all hitters with Steamer projections
response_data = get_all_projections(projection_system="steamer", position="all")

# Parse all players at once
players = parse_players(response_data)

# Now you have a list of player models
print(f"Found {len(players)} players")

# You can filter or sort them as needed
power_hitters = [p for p in players if p.projections["steamer"].hr >= 30]
for player in power_hitters:
    print(f"{player.name}: {player.projections['steamer'].hr} HR")
```

### Adding Multiple Projections

```python
# First get data for the first projection system
steamer_data = get_projection_data(player_id="33677", projection_system="steamer")
player = PlayerModel.parse_player(steamer_data, projection_source="steamer")

# Then get data for additional projection systems
atc_data = get_projection_data(player_id="33677", projection_system="atc")
atc_projection = PlayerModel.parse_player(atc_data, projection_source="atc")

# Add the new projection to the player
player.projections["atc"] = atc_projection.projections["atc"]

# Compare projections
print(f"Steamer ERA: {player.projections['steamer'].era}")
print(f"ATC ERA: {player.projections['atc'].era}")
print(f"{player.name}'s Projection Comparison: Steamer: {player.projections['steamer'].war} WAR, ATC: {player.projections['atc'].war} WAR")
```

## Data Models

### Player Models

- `PlayerModel`: Base model for all players with common identification fields
  - Properties:
    - `slug`: Generates a URL-friendly version of the player name
    - `stats_api`: Generates a stats API endpoint for the player
- `HitterModel`: Model for hitters
- `PitcherModel`: Model for pitchers

### Projection Models

- `BaseProjectionModel`: Common fields across all projection systems
- `HitterProjectionModel`: Base model for hitter projections
  - Automatically converts decimal stat values to integers where appropriate (e.g., HR, H)
  - Handles raw projection data from Fangraphs API
- `PitcherProjectionModel`: Base model for pitcher projections
- System-specific models:
  - `HitterSteamerProjectionModel`, `PitcherSteamerProjectionModel`
  - `HitterATCProjectionModel`, `PitcherATCProjectionModel`
  - `HitterTHEBATProjectionModel`, `PitcherTHEBATProjectionModel`

### Manager Functions

- `parse_players()`: Parses multiple player data records from the Fangraphs API response
  - Takes the raw API response with nested data structure
  - Returns a list of typed player models with their projections

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/username/fangraphs-api-extractor.git
cd fangraphs-api-extractor

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

## License

[MIT License](LICENSE)
