"""Tests for Logger utility."""

import logging
from io import StringIO


from fangraphs_api_extractor.utils.logger import Logger


def test_logger_initialization():
    """Test basic logger initialization."""
    logger = Logger("test_logger")

    assert logger.logging is not None
    assert logger.logging.name == "test_logger"
    assert logger.logging.level == logging.INFO


def test_logger_initialization_with_debug():
    """Test logger initialization with debug mode."""
    logger = Logger("test_debug_logger", debug=True)

    assert logger.logging is not None
    assert logger.logging.level == logging.DEBUG


def test_logger_reinitialization():
    """Test that reinitializing a logger doesn't add duplicate handlers."""
    logger1 = Logger("reuse_logger")
    initial_handler_count = len(logger1.logging.handlers)

    # Reinitialize with same name
    logger2 = Logger("reuse_logger")

    # Should not add additional handlers
    assert len(logger2.logging.handlers) == initial_handler_count


def test_log_request_basic():
    """Test log_request function with basic parameters."""
    # Create logger with debug mode so log_request actually logs
    logger = Logger("test_log_request", debug=True)

    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger.logging.addHandler(handler)

    endpoint = "https://api.example.com/endpoint"
    response = {"status": "success", "data": [1, 2, 3]}
    params = {"param1": "value1"}
    headers = {"Authorization": "Bearer token"}

    # Call log_request
    logger.log_request(endpoint, response, params, headers)

    # Verify log output
    log_output = log_capture.getvalue()
    assert endpoint in log_output
    assert "param1" in log_output
    assert "Authorization" in log_output
    assert '"status": "success"' in log_output


def test_log_request_without_optional_params():
    """Test log_request with only required parameters."""
    logger = Logger("test_log_request_minimal", debug=True)

    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger.logging.addHandler(handler)

    endpoint = "https://api.example.com/minimal"
    response = {"data": "test"}

    # Call log_request without params and headers
    logger.log_request(endpoint, response)

    # Verify log output
    log_output = log_capture.getvalue()
    assert endpoint in log_output
    assert "None" in log_output  # params and headers should be None
    assert '"data": "test"' in log_output


def test_log_request_not_logged_without_debug():
    """Test that log_request doesn't log when not in debug mode."""
    logger = Logger("test_no_debug", debug=False)

    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger.logging.addHandler(handler)

    endpoint = "https://api.example.com/endpoint"
    response = {"status": "success"}

    # Call log_request
    logger.log_request(endpoint, response)

    # Verify nothing is logged (INFO level doesn't capture DEBUG logs)
    log_output = log_capture.getvalue()
    # The log should be empty or not contain the endpoint since it's DEBUG level
    # and logger is at INFO level
    assert endpoint not in log_output or log_output == ""


def test_log_request_with_complex_response():
    """Test log_request with a complex nested response."""
    logger = Logger("test_complex", debug=True)

    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger.logging.addHandler(handler)

    endpoint = "https://api.example.com/complex"
    response = {
        "players": [
            {"name": "Player 1", "stats": {"hr": 30, "avg": 0.300}},
            {"name": "Player 2", "stats": {"hr": 25, "avg": 0.280}},
        ],
        "metadata": {"count": 2, "page": 1},
    }

    # Call log_request
    logger.log_request(endpoint, response)

    # Verify complex response is serialized
    log_output = log_capture.getvalue()
    assert "Player 1" in log_output
    assert "Player 2" in log_output
    assert "metadata" in log_output


def test_logger_level_change_on_reinitialization():
    """Test that reinitializing changes the log level."""
    # Create logger with INFO level
    logger1 = Logger("level_test", debug=False)
    assert logger1.logging.handlers[0].level == logging.INFO

    # Reinitialize with DEBUG level
    logger2 = Logger("level_test", debug=True)
    assert logger2.logging.handlers[0].level == logging.DEBUG
