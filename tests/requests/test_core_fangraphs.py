"""Tests for CoreFangraphs API client."""

from unittest.mock import Mock, patch

import pytest

from fangraphs_api_extractor.requests.core_fangraphs import (
    CoreFangraphs,
    ResponseStatus,
)


@pytest.fixture
def core_fangraphs():
    """Create a CoreFangraphs instance."""
    return CoreFangraphs(year=2025)


def test_initialization():
    """Test CoreFangraphs initialization."""
    fg = CoreFangraphs(year=2025)

    assert fg.year == 2025
    assert fg.logger is not None
    assert fg.session is not None
    assert fg.max_workers > 0


def test_initialization_with_max_workers():
    """Test initialization with custom max_workers."""
    fg = CoreFangraphs(year=2025, max_workers=8)

    assert fg.max_workers == 8


def test_check_request_status_success(core_fangraphs):
    """Test status check for successful response."""
    # Should not raise any exception or log warnings
    core_fangraphs._check_request_status(ResponseStatus.SUCCESS.value, "/test")


def test_check_request_status_not_found(core_fangraphs):
    """Test status check for 404 response."""
    core_fangraphs._check_request_status(ResponseStatus.NOT_FOUND.value, "/test")
    # Should log warning (tested by checking it doesn't raise exception)


def test_check_request_status_rate_limited(core_fangraphs):
    """Test status check for rate limit response."""
    core_fangraphs._check_request_status(ResponseStatus.RATE_LIMITED.value, "/test")


def test_check_request_status_server_error(core_fangraphs):
    """Test status check for server error response."""
    core_fangraphs._check_request_status(ResponseStatus.SERVER_ERROR.value, "/test")


def test_check_request_status_service_unavailable(core_fangraphs):
    """Test status check for service unavailable response."""
    core_fangraphs._check_request_status(
        ResponseStatus.SERVICE_UNAVAILABLE.value, "/test"
    )


def test_check_request_status_unknown(core_fangraphs):
    """Test status check for unknown error code."""
    core_fangraphs._check_request_status(999, "/test")


@patch("fangraphs_api_extractor.requests.core_fangraphs.requests.get")
def test_get_request_success(mock_get, core_fangraphs):
    """Test successful GET request."""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_get.return_value = mock_response

    result = core_fangraphs._get(params={"test": "param"}, extend="/endpoint")

    assert result == {"data": "test"}
    mock_get.assert_called_once()


@patch("fangraphs_api_extractor.requests.core_fangraphs.requests.get")
def test_get_request_with_headers(mock_get, core_fangraphs):
    """Test GET request with custom headers."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_get.return_value = mock_response

    custom_headers = {"Custom-Header": "value"}
    result = core_fangraphs._get(headers=custom_headers)

    assert result == {"data": "test"}


def test_get_projections_data_invalid_position_group(core_fangraphs):
    """Test get_projections_data with invalid position group."""
    result = core_fangraphs.get_projections_data(
        position_group="invalid", position="all", projections_system="steamer"
    )

    assert result is None


def test_get_projections_data_invalid_batting_position(core_fangraphs):
    """Test get_projections_data with invalid batting position."""
    result = core_fangraphs.get_projections_data(
        position_group="bat", position="invalid_pos", projections_system="steamer"
    )

    assert result is None


def test_get_projections_data_invalid_pitcher_position(core_fangraphs):
    """Test get_projections_data with invalid pitcher position."""
    # Pitchers should only accept "all"
    result = core_fangraphs.get_projections_data(
        position_group="pit",
        position="sp",  # Invalid for pit group
        projections_system="steamer",
    )

    assert result is None


def test_get_projections_data_invalid_projections_system(core_fangraphs):
    """Test get_projections_data with invalid projection system."""
    result = core_fangraphs.get_projections_data(
        position_group="bat", position="all", projections_system="invalid_system"
    )

    assert result is None


@patch("fangraphs_api_extractor.requests.core_fangraphs.requests.get")
def test_get_projections_data_success_bat(mock_get, core_fangraphs):
    """Test successful get_projections_data for batters."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"players": [{"name": "Test Player"}]}
    mock_get.return_value = mock_response

    result = core_fangraphs.get_projections_data(
        position_group="bat", position="all", projections_system="steamer"
    )

    assert result == {"players": [{"name": "Test Player"}]}
    mock_get.assert_called_once()


@patch("fangraphs_api_extractor.requests.core_fangraphs.requests.get")
def test_get_projections_data_success_pit(mock_get, core_fangraphs):
    """Test successful get_projections_data for pitchers."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"pitchers": [{"name": "Test Pitcher"}]}
    mock_get.return_value = mock_response

    result = core_fangraphs.get_projections_data(
        position_group="pit", position="all", projections_system="steamer"
    )

    assert result == {"pitchers": [{"name": "Test Pitcher"}]}


@patch("fangraphs_api_extractor.requests.core_fangraphs.requests.get")
def test_get_projections_data_with_custom_params(mock_get, core_fangraphs):
    """Test get_projections_data with custom parameters."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_get.return_value = mock_response

    custom_params = {"custom": "value"}
    result = core_fangraphs.get_projections_data(
        position_group="bat", params=custom_params
    )

    assert result == {"data": "test"}


@patch("fangraphs_api_extractor.requests.core_fangraphs.requests.get")
def test_get_projections_data_exception(mock_get, core_fangraphs):
    """Test get_projections_data when request raises exception."""
    mock_get.side_effect = Exception("Network error")

    result = core_fangraphs.get_projections_data(
        position_group="bat", position="all", projections_system="steamer"
    )

    assert result is None


def test_response_status_enum():
    """Test ResponseStatus enum values."""
    assert ResponseStatus.SUCCESS.value == 200
    assert ResponseStatus.NOT_FOUND.value == 404
    assert ResponseStatus.RATE_LIMITED.value == 429
    assert ResponseStatus.SERVER_ERROR.value == 500
    assert ResponseStatus.SERVICE_UNAVAILABLE.value == 503
    assert ResponseStatus.UNKNOWN_ERROR.value == 0


@patch("fangraphs_api_extractor.requests.core_fangraphs.requests.get")
def test_get_projections_data_valid_batting_positions(mock_get, core_fangraphs):
    """Test get_projections_data with various valid batting positions."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_get.return_value = mock_response

    valid_positions = ["all", "c", "1b", "2b", "3b", "ss", "of", "dh"]

    for pos in valid_positions:
        result = core_fangraphs.get_projections_data(
            position_group="bat", position=pos, projections_system="steamer"
        )
        assert result == {"data": "test"}


@patch("fangraphs_api_extractor.requests.core_fangraphs.requests.get")
def test_get_projections_data_valid_projection_systems(mock_get, core_fangraphs):
    """Test get_projections_data with various valid projection systems."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_get.return_value = mock_response

    valid_systems = ["steamer", "zips", "zipsdc", "atc"]

    for system in valid_systems:
        result = core_fangraphs.get_projections_data(
            position_group="bat", position="all", projections_system=system
        )
        assert result == {"data": "test"}


@patch("fangraphs_api_extractor.requests.core_fangraphs.requests.get")
def test_get_projections_data_valid_position_groups(mock_get, core_fangraphs):
    """Test get_projections_data with all valid position groups."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_get.return_value = mock_response

    valid_groups = ["bat", "pit", "sta", "rel"]

    for group in valid_groups:
        result = core_fangraphs.get_projections_data(
            position_group=group, position="all", projections_system="steamer"
        )
        assert result == {"data": "test"}
