"""Self-update from GitHub."""
from __future__ import annotations

import urllib.request
import re

from . import __version__
from .config import REPO_RAW_URL

def fetch_remote_version() -> tuple[str | None, str | None]:
    """Return (remote_version, raw_text) or (None, None) on failure."""
    url = f"{REPO_RAW_URL}/pyproject.toml"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            text = r.read().decode("utf-8", errors="ignore")
        m = re.search(r'version\s*=\s*"([^"]+)"', text)
        if m:
            return m.group(1), text
        return None, text
    except Exception:
        return None, None

def check_update() -> dict:
    remote, _ = fetch_remote_version()
    return {"current": __version__, "remote": remote, "has_update": remote is not None and remote != __version__}
