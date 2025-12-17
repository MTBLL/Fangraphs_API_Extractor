"""Tests for player slug extraction from UPURL."""

from fangraphs_api_extractor.models import HitterModel


def test_slug_extraction_from_upurl():
    """Test that slug is correctly extracted from UPURL."""
    data = {
        "Team": "NYY",
        "playerid": "15640",
        "PlayerName": "Aaron Judge",
        "xMLBAMID": 592450,
        "teamid": 9,
        "minpos": "OF",
        "UPURL": "/players/aaron-judge/15640/stats?position=OF",
        # Minimal hitter stats
        "AB": 500,
        "PA": 550,
        "RBI": 100,
    }

    player = HitterModel.model_validate(data)

    assert player.slug == "aaron-judge"
    assert player.upurl == "/players/aaron-judge/15640/stats?position=OF"


def test_slug_extraction_with_suffix():
    """Test slug extraction for player names with Jr/Sr suffixes."""
    data = {
        "Team": "KCR",
        "playerid": "25764",
        "PlayerName": "Bobby Witt Jr.",
        "xMLBAMID": 677951,
        "teamid": 7,
        "minpos": "SS",
        "UPURL": "/players/bobby-witt-jr/25764/stats?position=SS",
        # Minimal hitter stats
        "AB": 500,
        "PA": 550,
        "RBI": 100,
    }

    player = HitterModel.model_validate(data)

    assert player.slug == "bobby-witt-jr"


def test_slug_fallback_without_upurl():
    """Test that slug falls back to name-based generation when UPURL is missing."""
    data = {
        "Team": "NYY",
        "playerid": "15640",
        "PlayerName": "Aaron Judge",
        "xMLBAMID": 592450,
        "teamid": 9,
        # No UPURL provided
        # Minimal hitter stats
        "AB": 500,
        "PA": 550,
        "RBI": 100,
    }

    player = HitterModel.model_validate(data)

    # Should fall back to generating from name
    assert player.slug == "aaron-judge"


def test_slug_fallback_with_accents():
    """Test slug fallback handles non-ASCII characters."""
    data = {
        "Team": "CLE",
        "playerid": "12916",
        "PlayerName": "José Ramírez",
        "xMLBAMID": 608070,
        "teamid": 5,
        # No UPURL provided
        # Minimal hitter stats
        "AB": 500,
        "PA": 550,
        "RBI": 100,
    }

    player = HitterModel.model_validate(data)

    # Should normalize accents
    assert player.slug == "jose-ramirez"


def test_stats_api_uses_slug():
    """Test that stats_api property correctly uses the extracted slug."""
    data = {
        "Team": "NYY",
        "playerid": "15640",
        "PlayerName": "Aaron Judge",
        "xMLBAMID": 592450,
        "teamid": 9,
        "minpos": "OF",
        "UPURL": "/players/aaron-judge/15640/stats?position=OF",
        # Minimal hitter stats
        "AB": 500,
        "PA": 550,
        "RBI": 100,
    }

    player = HitterModel.model_validate(data)

    # stats_api should transform the UPURL
    assert player.stats_api == "/players/aaron-judge/15640/stats.json?position=OF"
