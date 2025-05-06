# Fangraphs API Extractor Tests

This directory contains tests for the Fangraphs API Extractor.

## Running Tests

To run all tests:

```bash
poetry run pytest
```

To run with coverage report:

```bash
poetry run pytest --cov=fangraphs_api_extractor
```

To run a specific test file:

```bash
poetry run pytest tests/models/test_hitter.py
```

## Test Fixtures

The `fixtures` directory contains sample data used for tests:

- `hitter_steamer.json`: Sample data for a hitter from the Steamer projection system
- `pitcher_steamer.json`: Sample data for a pitcher from the Steamer projection system

These fixtures can be used to test the parsing of player data and the creation of player models.