"""settings.json helpers — cross-platform, no jq needed."""
from __future__ import annotations

import datetime
import json
import re
import shutil
from pathlib import Path
from typing import Any

from .config import CLAUDE_DIR, DEFAULT_SETTINGS, SETTINGS_FILE, STANDARD_MODELS

def _load() -> dict[str, Any]:
    if not SETTINGS_FILE.exists():
        return {}
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save(data: dict[str, Any]) -> None:
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(SETTINGS_FILE)

def ensure_settings_file() -> None:
    """Create ~/.claude/settings.json with defaults if missing."""
    if not CLAUDE_DIR.exists():
        CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_FILE.exists():
        _save(DEFAULT_SETTINGS)

def get_value(key: str) -> str:
    return str(_load().get(key, "") or "")

def get_env_value(key: str) -> str:
    env = _load().get("env", {})
    if isinstance(env, dict):
        return str(env.get(key, "") or "")
    return ""

def update_field(field: str, value: str) -> None:
    create_backup()
    data = _load()
    data[field] = value
    _save(data)

def update_env(key: str, value: str) -> None:
    create_backup()
    data = _load()
    if "env" not in data or not isinstance(data["env"], dict):
        data["env"] = {}
    data["env"][key] = value
    _save(data)

def create_backup() -> Path | None:
    if not SETTINGS_FILE.exists():
        return None
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = CLAUDE_DIR / f"settings.json.backup.{ts}"
    # avoid collision if called twice in same second
    if dest.exists():
        dest = CLAUDE_DIR / f"settings.json.backup.{ts}.{datetime.datetime.now().microsecond}"
    shutil.copy2(SETTINGS_FILE, dest)
    return dest

def get_all_model_variants() -> list[tuple[str, str, str]]:
    """Return [(key, label, value)] in STANDARD_MODELS order."""
    data = _load()
    env = data.get("env", {}) if isinstance(data.get("env"), dict) else {}
    out: list[tuple[str, str, str]] = []
    for key, label in STANDARD_MODELS:
        val = str(env.get(key, "") or "")
        out.append((key, label, val))
    return out

def mask_token(token: str) -> str:
    if not token:
        return "(not set)"
    if len(token) > 3:
        return token[:3] + "x" * (len(token) - 3)
    return "***"

def format_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n // 1_000_000}m"
    if n >= 1000:
        return f"{n // 1000}k"
    return str(n)

def parse_tokens(s: str) -> int | None:
    m = re.fullmatch(r"([0-9]+)([kKmM])?", s.strip())
    if not m:
        return None
    num = int(m.group(1))
    suf = (m.group(2) or "").lower()
    if suf == "k":
        return num * 1000
    if suf == "m":
        return num * 1_000_000
    return num

def extract_model_context(value: str) -> tuple[str, str]:
    """'model[500k]' -> ('model','500k'), 'model' -> ('model','')."""
    m = re.fullmatch(r"(.+)\[([0-9]+[kKmM]?)\]", value.strip())
    if m:
        return m.group(1), m.group(2)
    return value, ""

def build_model_with_context(model: str, context: str | None) -> str:
    """Apply context suffix; if context is None/'' strip it."""
    base, _ = extract_model_context(model)
    if context:
        return f"{base}[{context}]"
    return base

def current_config_snapshot() -> dict[str, str]:
    data = _load()
    env = data.get("env", {}) if isinstance(data.get("env"), dict) else {}
    tok = str(env.get("ANTHROPIC_AUTH_TOKEN", "") or env.get("ANTHROPIC_API_KEY", "") or "")
    return {
        "base_url": str(env.get("ANTHROPIC_BASE_URL", "") or ""),
        "auth_token": tok,
        "auth_token_masked": mask_token(tok),
        "model_field": str(data.get("model", "") or ""),
        "effort_level": str(data.get("effortLevel", "") or ""),
        "theme": str(data.get("theme", "") or ""),
    }
