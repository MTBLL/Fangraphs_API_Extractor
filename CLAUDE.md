# Claude Information for Fangraphs API Extractor

This document contains information for Claude to help with working on this project.

## Project Overview

The Fangraphs API Extractor is a Python package that:
1. Extracts baseball player data from the Fangraphs API
2. Parses the JSON responses into strongly-typed Pydantic models
3. Provides easy access to player stats and projections

## Core Architecture

The project follows a separation of concerns pattern:
- **CoreFangraphs**: Only handles API interactions and returns raw data
- **PlayerModels**: Handle data validation and representation (Pydantic models)
- **Managers**: Handle parsing logic between raw data and models
- **Runners**: Coordinate the overall workflow
- **Utilities**: Provide common functionality like logging and serialization

## Key Design Principles

1. **Separation of Concerns**: Each component has a specific responsibility
2. **Proper Logging**: All components use the Logger utility (required parameter)
3. **Type Safety**: Pydantic models ensure proper data validation
4. **Error Handling**: Null values and other edge cases are properly handled
5. **Testing**: All components have corresponding tests

## Commands to Run

### Testing
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=fangraphs_api_extractor

# Run specific test files
poetry run pytest tests/models/test_hitter.py
poetry run pytest tests/models/test_pitcher.py
```

### Debugging
```bash
# Run the debug extraction script
python debug/run_player_extractor.py
```

## Project Structure

- `fangraphs_api_extractor/`
  - `managers/`: Parse raw data into models
  - `models/`: Pydantic models for players and projections
  - `requests/`: API interaction
  - `runners/`: Coordinate workflow
  - `utils/`: Common utilities
- `tests/`: Test files and fixtures
- `debug/`: Debugging scripts

## Common Patterns

1. **Logger Usage**: All major components require a logger parameter
   ```python
   def some_function(data, logger: Logger):
       log = logger.logging
       log.info("Processing data...")
   ```

2. **Data Flow**:
   ```python
   # API → Parse → Serialize → Save
   data = fangraphs.get_projections_data(...)
   players = parse_players(data, logger)
   serialized = serialize_players(players, logger)
   write_json_file(serialized, output_path, logger)
   ```

3. **Validation**:
   ```python
   @field_validator('team', mode='before')
   @classmethod
   def handle_null_team(cls, v):
       """Convert None team values to 'FA' for free agents"""
       if v is None:
           return "FA"
       return v
   ```

## Null Value Handling

- `team`: `None` → `"FA"` (free agent)
- `team_id`: `None` → `-1`
- `xmlbam_id`: `None` → `-1`

## Checking Types and Logging

Always typecheck before committing:
```bash
poetry run mypy fangraphs_api_extractor/
```

## File Naming Conventions

- Model files: `base_player.py`, `hitter.py`, `pitcher.py`
- Test files: `test_<module>.py`

## Key URLs

- Fangraphs API base URL: https://www.fangraphs.com/api/
- Player projections endpoint: https://www.fangraphs.com/api/projections