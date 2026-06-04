# Fangraphs API Extractor — Claude Code Context

ETL package that pulls player projections from the Fangraphs API, parses them
into typed Pydantic models, merges multiple sources via weighted average, and
writes a normalized JSON output. Daily-cron'd during the regular season.

- **Package name:** `fangraphs-api-extractor` (v0.5.0)
- **Python:** 3.13+, managed with `uv`
- **Install dev deps (once):** `uv sync --extra dev`
- **Run tests:** `uv run pytest tests/ -q`
- **Run CLI:** `uv run python -m fangraphs_api_extractor [--year 2026 --output-dir ./data --sample-size N]`
- **Type check:** `uv run mypy fangraphs_api_extractor/`

## Architecture

The data flow is one-directional:

```
CoreFangraphs (requests/)        # raw HTTP + Fangraphs API surface
   ↓
PlayerFetchHandler (handlers/)   # fetch + parse one source at a time
   ↓
PlayersManager (managers/)       # parse a list of raw rows into PlayerModels
   ↓
PlayerModel (models/)            # Pydantic models, three projection slots
   ↓
merge_player_projections (utils/weighted_average.py)
   ↓
serialize_players (utils/utils.py)  # JSON output with 3-decimal float rounding
   ↓
save_extraction_results          # writes fangraph_{batters,pitchers}_<year>_<ts>.json
```

`PlayerRunner` (`runners/player_runner.py`) orchestrates the full flow. The
`__main__.py` CLI is a thin wrapper that builds `sources` / `weights` dicts and
calls `PlayerRunner.run()`.

**Cloudflare:** Fangraphs fronts `/api/projections` with a managed JS challenge.
`CoreFangraphs` solves it via a FlareSolverr sidecar when `FLARESOLVERR_URL` is
set (adopts the `cf_clearance` cookie + the solver's User-Agent on the session).
Without it, pulls 403 while the challenge is active. Full story and the
dead-ends tried: [`docs/the-wall-goes-up.md`](docs/the-wall-goes-up.md).

## Three-slot projection schema

Each player carries **three independent projection blobs**, each merged from a
different set of Fangraphs endpoints:

| Slot (PlayerModel attr) | What it represents | When empty |
|---|---|---|
| `projections` | Canonical pre-season full-year mix. **Only slot with qq/tt percentile fields** (`q10`–`q90`, `tt_q10`–`tt_q90`). | Never |
| `projs_updated` | Full-year refit with in-season data. Equal-weight uzips + steameru. | Pre-draft (endpoints not yet published) |
| `ros` | Rest-of-season (162 − games played). | Pre-draft (endpoints not yet published) |

JSON serialization:
- Each slot is **always** an object — empty slots serialize as `{}`, never `null`.
- Every float is rounded to **3 decimal places** with `ROUND_HALF_UP` (so `0.0005 → 0.001`, not banker's). See `round_floats` in `utils/utils.py`.
- Output filenames: `fangraph_{batters,pitchers}_<year>_<YYYYMMDD_HHMMSS>.json`.

## Default mixes (live in `utils/constants.py`)

The runner always performs three independent fetch+merge passes. The same
defaults work year-round — pre-draft, `projs_updated` and `ros` fetches return
empty and the slots serialize as `{}`. There is no separate "mode" flag.

**`projections` slot — `DEFAULT_PROJECTIONS_*`** (canonical, carries qq/tt):

| Position | Sources | Weights |
|---|---|---|
| Batters  | `thebatx`, `fangraphsdc`, `atc`, `steamer` | 50, 25, 25, 0* |
| Pitchers | `oopsy`,   `fangraphsdc`, `atc`, `steamer` | 50, 25, 25, 0* |

\* `steamer` at weight 0 still contributes `q10`–`q90` and `tt_q10`–`tt_q90`.
All other Steamer fields are filtered out — special handling in
`weighted_average.py`. Empirically only pre-season `steamer` emits these
percentiles; neither `steamerr` nor `steameru` does.

**`projs_updated` slot — `DEFAULT_UPDATES_*`:**

| Position | Sources | Weights |
|---|---|---|
| Batters  | `uzips`, `steameru` | 50, 50 |
| Pitchers | `uzips`, `steameru` | 50, 50 |

**`ros` slot — `DEFAULT_ROS_*`:**

| Position | Sources | Weights |
|---|---|---|
| Batters  | `rthebatx`, `rfangraphsdc`, `ratcdc` | 50, 25, 25 |
| Pitchers | `roopsydc`, `rfangraphsdc`, `ratcdc` | 50, 25, 25 |

## Sources and the `ProjectionSource` enum

`utils/constants.py::ProjectionSource` is the single source of truth for valid
identifiers. `PROJECTION_SYSTEMS = [s.value for s in ProjectionSource]` — they
cannot drift. `core_fangraphs.py:153` guards `get_projections_data` against
unknown source strings (raises `InvalidProjectionsSystemError`).

- **Pre-season** (`PRESEASON_PROJECTION_SYSTEMS`): `steamer`, `zips`, `zipsdc`, `atc`, `fangraphsdc`, `thebat`, `thebatx`, `oopsy`
- **Updated** (`UPDATED_PROJECTION_SYSTEMS`): `uzips`, `steameru`
- **Rest-of-season** (`ROS_PROJECTION_SYSTEMS`): `steamerr`, `rzips`, `rzipsdc`, `rfangraphsdc`, `ratcdc`, `rthebat`, `rthebatx`, `roopsydc`

### Quirks the fetch handler hides

- `thebatx` has no pitcher data — `PlayerFetchHandler.fetch_pitchers` maps it to `thebat` for the API call but keeps the source label `thebatx` through the rest of the pipeline.
- `rthebatx` has no pitcher data — same auto-map to `rthebat`.
- `oopsy` and `roopsydc` are valid for both hitters and pitchers.

### Empirical surprises worth knowing

- The `steameru` and `steamerr` endpoints **don't emit qq/tt percentile fields**, even though Steamer does. The steamer-at-weight-0 trick is unique to `steamer` in `DEFAULT_PROJECTIONS_*`.
- `uzips` returns ~485 batters / ~574 pitchers (regulars). `steameru` returns ~4,300 / ~5,400 (full population). RoS sources behave similarly: `rthebatx`/`rfangraphsdc`/`ratcdc` are regulars-only (~629), `steamerr` is broad. Coverage gaps matter when picking weights.
- Fangraphs is behind Cloudflare. The package's `requests.Session()` accumulates cookies across calls so subsequent fetches succeed; a one-shot curl gets challenge-page-blocked. For one-off curl debugging: copy cookies from a browser session.

## Merge logic (`utils/weighted_average.py`)

- `merge_player_projections(players_by_source, weights, target_slot="projections")` — aggregates per-source projections by `playerid`, computes a weighted average for each numeric field, and writes the merged model into `target_slot` on the player.
- The runner calls it three times (once per slot) with `target_slot` set accordingly.
- Special case: when a source's weight is 0 **and** the source is in `steamer_family = {"steamer"}`, only its qq/tt percentile fields contribute. All other fields are filtered out. This is what powers the steamer-at-weight-0 trick for percentiles.

## Tests

- **Framework:** pytest (declared in `[project.optional-dependencies].dev`, also runnable via `--with pytest`).
- **Fixtures:** `tests/fixtures/` holds captured-from-API JSON used by `test_player_runner` and others. They're frozen (year 2025) — don't bump those, only bump user-facing defaults.
- **Mocking the runner:** the runner makes 3 fetch calls per invocation. The test helper `_mock_triple_fetch` deepcopies its inputs so each cycle operates on independent PlayerModel instances (production fetches create fresh ones; without deepcopy, the second/third merge wipes state on the same objects the first one wrote).

## CLI shape

```bash
uv run python -m fangraphs_api_extractor \
  --year 2026 \
  --output-dir ./data \
  --sample-size 50

# Custom projections slot (does NOT affect projs_updated / ros slots — those keep their defaults)
uv run python -m fangraphs_api_extractor \
  --batter-sources "thebatx,fangraphsdc,steamer" \
  --pitcher-sources "oopsy,fangraphsdc,steamer" \
  --weights "75,25,0"
```

- `--batter-sources`, `--pitcher-sources`, `--weights` override **only** the `projections` slot.
- `--weights` is a single positional list applied to both `--batter-sources` and `--pitcher-sources`, so both must have the same length. For asymmetric per-position weights, use the Python API.
- There is **no `--predraft` flag** anymore. The same invocation works year-round; empty slots just serialize as `{}`.

## File map

```
fangraphs_api_extractor/
├── __main__.py              # CLI entry point
├── handlers/
│   └── player_fetch_handler.py
├── managers/
│   └── players_manager.py
├── models/
│   ├── base_player.py       # PlayerModel + projections/projs_updated/ros slots, parse_player factory
│   ├── hitter.py
│   └── pitcher.py
├── requests/
│   └── core_fangraphs.py    # HTTP, Cloudflare-aware session, source-string guard
├── runners/
│   └── player_runner.py     # Three-pass fetch/merge orchestration
└── utils/
    ├── constants.py         # ProjectionSource enum + DEFAULT_*_SOURCES/WEIGHTS
    ├── weighted_average.py  # merge_player_projections + steamer-at-zero special case
    └── utils.py             # serialize_players + round_floats + save_extraction_results
```

## Branch state

Active feature branch: `feature/fangraphs-ros-default-and-source-guards`.
First commit on the branch (`d84f261`) covered the initial RoS default + source-guards refactor. The three-slot redesign (this iteration) is uncommitted on top of that. Confirm before committing.
