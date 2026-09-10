"""Path & constants — cross-platform.

Settings file is always at ~/.claude/settings.json on Linux/macOS/Windows
(Windows: C:\\Users\\<you>\\.claude\\settings.json).
"""
from __future__ import annotations

import os
from pathlib import Path

__version__ = "1.0.0"
REPO = "Fauzan-Fz/ClaudeShift-CLI"
REPO_RAW_URL = f"https://raw.githubusercontent.com/{REPO}/main"

# Claude settings file — same on all OS
SETTINGS_FILE: Path = Path.home() / ".claude" / "settings.json"
CLAUDE_DIR: Path = SETTINGS_FILE.parent

# Standard fixed model variants — guaranteed order everywhere
# (matches Bash STANDARD_MODELS)
STANDARD_MODELS: list[tuple[str, str]] = [
    ("ANTHROPIC_MODEL", "Default Model"),
    ("ANTHROPIC_SMALL_FAST_MODEL", "Small/Fast Model"),
    ("ANTHROPIC_DEFAULT_OPUS_MODEL", "Opus Model"),
    ("ANTHROPIC_DEFAULT_SONNET_MODEL", "Sonnet Model"),
    ("ANTHROPIC_DEFAULT_HAIKU_MODEL", "Haiku Model"),
    ("ANTHROPIC_DEFAULT_FABLE_MODEL", "Fable Model"),
]

# Context presets for model[ctx] syntax
CONTEXT_PRESETS: list[str] = [
    "4k", "8k", "16k", "32k", "64k", "128k", "200k", "500k", "1m", "2m",
]

# Default settings content (created if settings.json missing)
DEFAULT_SETTINGS: dict = {
    "env": {
        "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
        "ANTHROPIC_MODEL": "anthropic/claude-sonnet",
        "ANTHROPIC_SMALL_FAST_MODEL": "anthropic/claude-haiku",
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "anthropic/claude-opus",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "anthropic/claude-sonnet",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "anthropic/claude-haiku",
        "ANTHROPIC_AUTH_TOKEN": "",
    },
    "model": "haiku",
    "effortLevel": "high",
    "theme": "dark",
}
