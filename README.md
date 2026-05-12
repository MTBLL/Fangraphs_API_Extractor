# Fangraphs API Extractor

[![codecov](https://codecov.io/gh/MTBLL/Fangraphs_API_Extractor/graph/badge.svg?token=Vk0FSuR25F)](https://codecov.io/gh/MTBLL/Fangraphs_API_Extractor)
[![Mypy Type Check](https://github.com/MTBLL/Fangraphs_API_Extractor/actions/workflows/mypy.yml/badge.svg)](https://github.com/MTBLL/Fangraphs_API_Extractor/actions/workflows/mypy.yml)

A Python package for extracting and parsing baseball player data from Fangraphs projections into strongly-typed Pydantic models.

## Features

- 🎯 Extract player data from Fangraphs projection systems (Steamer, ATC, ZIPS, etc.)
- 📊 Parse JSON responses into strongly-typed Pydantic models
- ⚾ Support for both hitters and pitchers with position-specific stats
- 🔄 Handle multiple projection sources for the same player
- 🎯 Store a single weighted projection per player (`player.projection`)
- 🏷️ Automatic URL slug generation from player names (handles accents/special characters)
- 🌐 Built-in stats API endpoint generation
- ✅ 93% test coverage with 97 comprehensive tests
- 🔒 Full type safety with mypy validation

## Installation

```bash
# Install with uv (recommended)
uv install

# Or install from the repository
pip install git+https://github.com/MTBLL/Fangraphs_API_Extractor.git
```

## Quick Start

```python
from fangraphs_api_extractor.runners import PlayerRunner

# Initialize the runner for 2026 season
runner = PlayerRunner(year=2026)

# Extract all players and save to file
players = runner.run(output_dir="./data")

# Access player information
for player in players[:5]:
    print(f"{player.name} ({player.team}) - {player.slug}")
    
    # Access projection
    proj = player.projection
    if proj and hasattr(proj, "hr"):  # Hitter
        print(f"  Projected: {proj.hr} HR, {proj.avg:.3f} AVG")
    elif proj and hasattr(proj, "era"):  # Pitcher
        print(f"  Projected: {proj.wins} W, {proj.era:.2f} ERA")
```

## Usage

### Extracting Player Data

```python
from fangraphs_api_extractor.runners import PlayerRunner

# Extract with sample size for testing
runner = PlayerRunner(year=2026)
players = runner.run(
    sample_size=50,  # Limit to 50 players for quick testing
    output_dir="./output"  # Saves to fangraph_pitchers_<year>_<timestamp>.json and fangraph_batters_<year>_<timestamp>.json
)

print(f"Extracted {len(players)} players")
```

### Working with Individual Players

```python
from fangraphs_api_extractor.handlers import PlayerFetchHandler
from fangraphs_api_extractor.requests.core_fangraphs import CoreFangraphs

# Setup API client
fangraphs = CoreFangraphs(year=2026)
handler = PlayerFetchHandler(fangraphs)

# Fetch hitters
hitters = handler.fetch_hitters()

# Access player properties
player = hitters[0]
print(f"Name: {player.name}")
print(f"Team: {player.team}")
print(f"URL Slug: {player.slug}")  # e.g., "aaron-judge"
print(f"Stats API: {player.stats_api}")  # Ready-to-use endpoint

# Access projection
proj = player.projection
if proj:
    print(f"HR: {proj.hr}, AVG: {proj.avg}, WAR: {proj.war}")
```

### Multiple Projection Systems

```python
from fangraphs_api_extractor.requests.core_fangraphs import CoreFangraphs
from fangraphs_api_extractor.managers import PlayersManager
from fangraphs_api_extractor.utils.weighted_average import merge_player_projections

fangraphs = CoreFangraphs(year=2026)

# Get Steamer projections
steamer_data = fangraphs.get_projections_data("bat", projections_system="steamer")
manager = PlayersManager("hitters")
steamer_players = manager.parse_players(steamer_data, projection_source="steamer")

# Get ATC projections for same players
atc_data = fangraphs.get_projections_data("bat", projections_system="atc")
atc_players = manager.parse_players(atc_data, projection_source="atc")

# Combine sources with weighted averaging
players_by_source = {"steamer": steamer_players, "atc": atc_players}
weights = {"steamer": 0.75, "atc": 0.25}
merged_players = merge_player_projections(players_by_source, weights)

player = merged_players[0]
proj = player.projection
print(f"{player.name}:")
print(f"  Weighted WAR: {proj.war}")
```

## Projection Systems

### Valid Sources

All valid projection system identifiers are defined in `ProjectionSource` (see `utils/constants.py`).
Passing any string not in this enum to the API will raise `InvalidProjectionsSystemError`.

#### Pre-season projections

Full-season forecasts; available before and during the season.

| Identifier | System |
|---|---|
| `steamer` | Steamer |
| `zips` | ZiPS |
| `zipsdc` | ZiPS + Depth Charts |
| `atc` | ATC |
| `fangraphsdc` | Fangraphs Depth Charts |
| `thebat` | THE BAT |
| `thebatx` | THE BAT X |
| `oopsy` | OOPSY |

#### Rest-of-season (RoS) projections

Updated mid-season; project only remaining games, not the full season.

| Identifier | System |
|---|---|
| `steamerr` | Steamer RoS |
| `rzips` | ZiPS RoS |
| `rzipsdc` | ZiPS + Depth Charts RoS |
| `rfangraphsdc` | Fangraphs Depth Charts RoS |
| `ratcdc` | ATC RoS |
| `rthebat` | THE BAT RoS |
| `rthebatx` | THE BAT X RoS |
| `roopsydc` | OOPSY RoS |

### Modes & Default Mixes

The app has two modes, both defined in `utils/constants.py`:

#### In-season (default)

`DEFAULT_ROS_SOURCES` / `DEFAULT_ROS_WEIGHTS` — used by the CLI with no flags and by
`PlayerRunner` with no `sources`/`weights` arguments. Intended for daily runs during the
regular season; rest-of-season projections are the only ones that change day to day.

| Position | Sources (in order) | Weights |
|---|---|---|
| Batters | `rthebatx`, `rfangraphsdc`, `ratcdc`, `steamerr` | 50%, 25%, 25%, 0%* |
| Pitchers | `roopsydc`, `rfangraphsdc`, `ratcdc`, `steamerr` | 50%, 25%, 25%, 0%* |

#### Pre-draft (opt-in via `--predraft`)

`DEFAULT_PREDRAFT_SOURCES` / `DEFAULT_PREDRAFT_WEIGHTS` — used before the draft / during
the offseason. Same structure as the RoS mix, but with pre-season source equivalents.

| Position | Sources (in order) | Weights |
|---|---|---|
| Batters | `thebatx`, `fangraphsdc`, `atc`, `steamer` | 50%, 25%, 25%, 0%* |
| Pitchers | `oopsy`, `fangraphsdc`, `atc`, `steamer` | 50%, 25%, 25%, 0%* |

\* The `steamer` / `steamerr` source at weight 0 still contributes — it provides only the
`qq` and `tt` percentile fields, which are not available from other systems. All other
Steamer fields are ignored when its weight is 0.

### Pitcher-specific notes

- **`thebatx`** has no pitcher data. The fetch handler automatically maps it to `thebat`
  for pitcher API calls; the source label remains `thebatx` throughout the rest of the pipeline.
- **`rthebatx`** has no pitcher data and is automatically mapped to `rthebat` the same way.
- **`oopsy`** and **`roopsydc`** are valid for both hitters and pitchers.

### Running from the CLI

```bash
# Default — rest-of-season mix (rthebatx/roopsydc 50%, rfangraphsdc 25%, ratcdc 25%, steamerr qq/tt only)
uv run python -m fangraphs_api_extractor

# Pre-draft mix (thebatx/oopsy 50%, fangraphsdc 25%, atc 25%, steamer qq/tt only)
uv run python -m fangraphs_api_extractor --predraft

# Custom sources — batters and pitchers must have the same number of sources
# because --weights is a single list applied positionally to both position groups
uv run python -m fangraphs_api_extractor \
  --batter-sources "rthebatx,rfangraphsdc,steamerr" \
  --pitcher-sources "roopsydc,rfangraphsdc,steamerr" \
  --weights "60,40,0"
# → batters:  rthebatx=60%, rfangraphsdc=40%, steamerr=0% (qq/tt only)
# → pitchers: roopsydc=60%, rfangraphsdc=40%, steamerr=0% (qq/tt only)

# Omitting --weights uses equal weights across all sources
uv run python -m fangraphs_api_extractor \
  --batter-sources "steamer,atc,zips" \
  --pitcher-sources "steamer,atc,zips"
# → each source gets 33.3%

# Other common flags
uv run python -m fangraphs_api_extractor \
  --year 2026 \
  --output-dir ./data \
  --sample-size 50       # limit for quick testing
```

> **CLI weight constraint:** `--weights` is a single comma-separated list that is zipped
> positionally against both `--batter-sources` and `--pitcher-sources`. This means:
> - Both position groups must have the **same number of sources**
> - Both position groups receive the **same weight ratios** (applied to different source names)

## Project Structure

```
fangraphs_api_extractor/
├── handlers/          # Data fetching and processing
│   └── player_fetch_handler.py
├── managers/          # Data parsing logic
│   └── players_manager.py
├── models/            # Pydantic models
│   ├── base_player.py
│   ├── hitter.py
│   └── pitcher.py
├── requests/          # API client
│   └── core_fangraphs.py
├── runners/           # High-level orchestration
│   └── player_runner.py
└── utils/             # Utilities (logging, serialization)
    ├── logger.py
    └── utils.py
```

## Key Features

### Smart Slug Generation

The package automatically generates URL-friendly slugs from player names:

```python
# Handles special characters and accents
player.name = "José Ramírez"
player.slug  # "jose-ramirez"

# Extracts from UPURL when available
player.upurl = "/players/bobby-witt-jr/25764/stats?position=SS"
player.slug  # "bobby-witt-jr"
```

### Free Agent Handling

```python
# Null team values automatically converted to 'FA'
player.team = None  # → "FA"
player.team_id = None  # → -1
```

### Stats API Endpoints

```python
# Automatic endpoint generation
player.upurl = "/players/aaron-judge/15640/stats?position=OF"
player.stats_api  # "/players/aaron-judge/15640/stats.json?position=OF"
```

## Development

### Setup

```bash
git clone https://github.com/MTBLL/Fangraphs_API_Extractor.git
cd Fangraphs_API_Extractor
uv install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=fangraphs_api_extractor --cov-report=term-missing

# Run specific test file
uv run pytest tests/models/test_hitter.py -v

# Type checking
uv run mypy fangraphs_api_extractor/
```

### Debugging

For debugging and testing data extraction:

```bash
# Run debug script (extracts sample data)
uv run python debug/run_player_extractor.py
```

This will fetch real data from Fangraphs and save it to `fangraph_pitchers_<year>_<timestamp>.json` and `fangraph_batters_<year>_<timestamp>.json` for inspection.

## Architecture

### Separation of Concerns

- **CoreFangraphs**: Handles only API interactions, returns raw data
- **PlayerFetchHandler**: Fetches and parses data into models
- **PlayersManager**: Parses various data formats into player models
- **PlayerRunner**: Orchestrates the complete extraction workflow
- **Models**: Pydantic models ensure data validation and type safety

### Type Safety

All components are fully typed and validated with mypy:
```bash
uv run mypy fangraphs_api_extractor/  # Success: no issues found
```

## License

[MIT License](LICENSE)
