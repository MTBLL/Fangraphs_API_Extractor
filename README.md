# Fangraphs API Extractor

[![codecov](https://codecov.io/gh/MTBLL/Fangraphs_API_Extractor/graph/badge.svg?token=Vk0FSuR25F)](https://codecov.io/gh/MTBLL/Fangraphs_API_Extractor)
[![Mypy Type Check](https://github.com/MTBLL/Fangraphs_API_Extractor/actions/workflows/mypy.yml/badge.svg)](https://github.com/MTBLL/Fangraphs_API_Extractor/actions/workflows/mypy.yml)

A Python package for extracting and parsing baseball player data from Fangraphs projections into strongly-typed Pydantic models.

## Features

- 🎯 Extract player data from Fangraphs projection systems (Steamer, ATC, ZIPS, etc.)
- 📊 Parse JSON responses into strongly-typed Pydantic models
- ⚾ Support for both hitters and pitchers with position-specific stats
- 🔄 Handle multiple projection sources for the same player
- 🎯 Three weighted projection blobs per player: `player.projections` (pre-season full-year), `player.projs_updated` (in-season refit full-year), `player.ros` (rest-of-season)
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

# Each player carries three independent projection blobs:
#   - .projections: canonical pre-season full-year projection (also the only
#                   slot with qq/tt percentile fields)
#   - .projs_updated:     full-year projection refit with in-season data
#   - .ros:         rest-of-season projection
for player in players[:5]:
    print(f"{player.name} ({player.team}) - {player.slug}")
    for slot_name in ("projections", "projs_updated", "ros"):
        proj = getattr(player, slot_name)
        if proj and hasattr(proj, "war"):
            print(f"  {slot_name}: WAR={proj.war}")
```

## Output Schema

Each player record in the saved JSON has the shape:

```json
{
  "name": "Aaron Judge",
  "ascii_name": "aaron judge",
  "team": "NYY",
  "playerid": "15640",
  "xmlbam_id": 592450,
  "slug": "aaron-judge",
  "stats_api": "/players/aaron-judge/15640/stats.json?position=OF",
  "projections": { "HR": 39, "AVG": 0.291, "WAR": 7.495, "q10": 0.235, ..., "tt_q90": 8.91 },
  "projs_updated":     { "HR": 41, "AVG": 0.294, "WAR": 7.965, ... },
  "ros":         { "HR": 28, "AVG": 0.288, "WAR": 6.251, ... }
}
```

All three slots — `projections`, `projs_updated`, and `ros` — are always present as
objects. When a slot has no data (e.g., pre-draft, when Fangraphs hasn't yet
published the `projs_updated` or `ros` endpoints), the slot serializes as an **empty
object** `{}` — not `null` and not omitted — so downstream consumers can rely
on the shape.

**Percentile fields:** Only `projections` carries `q10`–`q90` and `tt_q10`–
`tt_q90`. Empirically only the pre-season `steamer` endpoint emits these
fields, so the steamer-at-weight-0 trick (where Steamer's weight is 0 for all
other fields but full weight for qq/tt) is what makes the `projections` slot
the canonical place for percentiles.

All float values are rounded to **3 decimal places** using half-away-from-zero
rounding (so `0.0005 → 0.001`).

## Usage

### Extracting Player Data

```python
from fangraphs_api_extractor.runners import PlayerRunner

# Extract with sample size for testing
runner = PlayerRunner(year=2026)
players = runner.run(
    sample_size=50,
    output_dir="./output",
)
print(f"Extracted {len(players)} players")
```

### Working with Individual Players

```python
from fangraphs_api_extractor.handlers import PlayerFetchHandler
from fangraphs_api_extractor.requests.core_fangraphs import CoreFangraphs

fangraphs = CoreFangraphs(year=2026)
handler = PlayerFetchHandler(fangraphs)

# Fetch hitters from a single source (returns PlayerModel instances with
# the source-specific projection attached to .projections)
hitters = handler.fetch_hitters(projection_source="uzips")

player = hitters[0]
print(f"Name: {player.name}")
print(f"Team: {player.team}")
print(f"URL Slug: {player.slug}")
print(f"HR: {player.projections.hr}, AVG: {player.projections.avg}")
```

## Projection Systems

### Valid Sources

All valid projection system identifiers are defined in `ProjectionSource` (see
`utils/constants.py`). Passing any string not in this enum to the API will raise
`InvalidProjectionsSystemError`.

#### Pre-season projections

Full-season forecasts; not updated mid-season.

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

#### Updated projections

Full-season forecasts refit with in-season data — only available during the
season. Currently only Steamer and ZiPS publish updated variants.

| Identifier | System |
|---|---|
| `uzips` | Updated ZiPS |
| `steameru` | Updated Steamer |

#### Rest-of-season (RoS) projections

Project only remaining games (162 − games played); updated mid-season.

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

### Default Mixes per Slot

Every run performs three independent fetches — one per slot. There is no
separate "mode" flag: the same defaults work year-round because slots that
have no data (e.g. `projs_updated` and `ros` pre-draft) gracefully serialize as `{}`.

All three defaults live in `utils/constants.py`.

#### `projections` slot — `DEFAULT_PROJECTIONS_*`

Canonical pre-season full-year mix. Also the **only slot that exposes qq/tt
percentile fields** (via the steamer-at-weight-0 trick).

| Position | Sources (in order) | Weights |
|---|---|---|
| Batters | `thebatx`, `fangraphsdc`, `atc`, `steamer` | 50%, 25%, 25%, 0%* |
| Pitchers | `oopsy`, `fangraphsdc`, `atc`, `steamer` | 50%, 25%, 25%, 0%* |

\* `steamer` at weight 0 still contributes the `q10`–`q90` and `tt_q10`–`tt_q90`
percentile fields. All other Steamer fields are filtered out. Empirically only
pre-season `steamer` emits these percentiles — neither `steamerr` nor
`steameru` does — so this trick only benefits the `projections` slot.

#### `projs_updated` slot — `DEFAULT_UPDATES_*`

In-season-refit full-year mix. Equal-weight average across the two updated
sources Fangraphs publishes. Empty pre-draft.

| Position | Sources (in order) | Weights |
|---|---|---|
| Batters | `uzips`, `steameru` | 50%, 50% |
| Pitchers | `uzips`, `steameru` | 50%, 50% |

#### `ros` slot — `DEFAULT_ROS_*`

Rest-of-season mix. Empty pre-draft.

| Position | Sources (in order) | Weights |
|---|---|---|
| Batters | `rthebatx`, `rfangraphsdc`, `ratcdc` | 50%, 25%, 25% |
| Pitchers | `roopsydc`, `rfangraphsdc`, `ratcdc` | 50%, 25%, 25% |

### Pitcher-specific notes

- **`thebatx`** has no pitcher data. The fetch handler automatically maps it to
  `thebat` for pitcher API calls; the source label remains `thebatx` through
  the rest of the pipeline.
- **`rthebatx`** has no pitcher data and is automatically mapped to `rthebat`.
- **`oopsy`** and **`roopsydc`** are valid for both hitters and pitchers.

### Running from the CLI

```bash
# Default — all three slots fetched with their default mixes.
# projections: thebatx/oopsy 50%, fangraphsdc 25%, atc 25%, steamer qq/tt only
# updates:     uzips 50% / steameru 50%   (empty {} pre-draft)
# ros:         rthebatx/roopsydc 50%, rfangraphsdc 25%, ratcdc 25%   (empty {} pre-draft)
uv run python -m fangraphs_api_extractor

# Custom projections sources — overrides ONLY the projections slot.
# The updates and ros slots continue to use their defaults.
uv run python -m fangraphs_api_extractor \
  --batter-sources "thebatx,fangraphsdc,steamer" \
  --pitcher-sources "oopsy,fangraphsdc,steamer" \
  --weights "75,25,0"

# Common flags
uv run python -m fangraphs_api_extractor \
  --year 2026 \
  --output-dir ./data \
  --sample-size 50
```

> **There is no separate pre-draft flag.** The same default invocation works
> year-round — pre-draft, the `updates` and `ros` fetches return empty and
> those slots serialize as `{}`. During the season they're populated.
>
> **CLI override scope:** `--batter-sources`, `--pitcher-sources`, and `--weights`
> override **only the `projections` slot**. For per-slot customization on
> `updates` or `ros`, use the Python API and pass a nested
> `sources={"projections": {...}, "updates": {...}, "ros": {...}}` dict.
>
> `--weights` is a single comma-separated list zipped positionally against both
> `--batter-sources` and `--pitcher-sources`, so both position groups must have
> the same number of sources and receive the same weight ratios.

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
