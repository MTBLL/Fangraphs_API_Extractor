"""
String utilities for handling special characters and formatting.
"""

import unicodedata
import re


def normalize_string(s: str) -> str:
    """
    Normalize Unicode string by removing diacritical marks (accents).
    
    This converts characters like 'é', 'ü', 'ñ' to 'e', 'u', 'n'.
    
    Args:
        s: Input string that may contain non-ASCII characters
        
    Returns:
        ASCII-only string with diacritical marks removed
    """
    # Normalize to decomposed form (separate base characters from accents)
    normalized = unicodedata.normalize('NFD', s)
    # Remove all diacritical marks
    ascii_only = re.sub(r'[\u0300-\u036f]', '', normalized)
    # Return ASCII string
    return ascii_only