"""Tests for the instructions module."""

import pytest

from src.instructions import SYSTEM_INSTRUCTIONS


class TestSystemInstructions:
    """Tests for system instructions."""

    def test_instructions_not_empty(self):
        """Test that instructions are not empty."""
        assert SYSTEM_INSTRUCTIONS is not None
        assert len(SYSTEM_INSTRUCTIONS) > 0

    def test_instructions_is_string(self):
        """Test that instructions is a string."""
        assert isinstance(SYSTEM_INSTRUCTIONS, str)

    def test_instructions_contains_key_elements(self):
        """Test that instructions contain key elements."""
        # Should mention Fusion 360
        assert "Fusion" in SYSTEM_INSTRUCTIONS or "fusion" in SYSTEM_INSTRUCTIONS.lower()

    def test_instructions_mentions_units(self):
        """Test that instructions mention units."""
        assert "mm" in SYSTEM_INSTRUCTIONS or "cm" in SYSTEM_INSTRUCTIONS
