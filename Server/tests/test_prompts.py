"""Tests for the prompts module."""

import pytest

from src.prompts import PROMPTS, get_prompt


class TestPrompts:
    """Tests for prompts configuration."""

    def test_prompts_is_dict(self):
        """Test that PROMPTS is a dictionary."""
        assert isinstance(PROMPTS, dict)

    def test_prompts_not_empty(self):
        """Test that PROMPTS is not empty."""
        assert len(PROMPTS) > 0

    def test_wineglass_prompt_exists(self):
        """Test wineglass prompt exists."""
        assert "wineglass" in PROMPTS

    def test_magnet_prompt_exists(self):
        """Test magnet prompt exists."""
        assert "magnet" in PROMPTS

    def test_dna_prompt_exists(self):
        """Test DNA prompt exists."""
        assert "dna" in PROMPTS


class TestGetPrompt:
    """Tests for get_prompt function."""

    def test_get_existing_prompt(self):
        """Test getting an existing prompt."""
        prompt = get_prompt("wineglass")
        assert prompt is not None
        assert len(prompt) > 0

    def test_get_nonexistent_prompt(self):
        """Test getting a nonexistent prompt returns error message."""
        prompt = get_prompt("nonexistent_prompt_xyz")
        assert "Unknown prompt" in prompt

    def test_get_prompt_returns_string(self):
        """Test that get_prompt returns a string for existing prompts."""
        prompt = get_prompt("wineglass")
        assert isinstance(prompt, str)
