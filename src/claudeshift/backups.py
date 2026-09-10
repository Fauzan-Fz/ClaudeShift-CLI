"""Backup helpers — scan / restore / clean."""
from __future__ import annotations

import re
from pathlib import Path

from .config import CLAUDE_DIR, SETTINGS_FILE

BACKUP_PREFIX = "settings.json.backup."

def scan_backups() -> list[Path]:
    if not CLAUDE_DIR.exists():
        return []
    files = sorted(CLAUDE_DIR.glob(f"{BACKUP_PREFIX}*"), key=lambda p: p.name)
    # newest first (name contains timestamp YYYYMMDD_HHMMSS so lexicographic works)
    return sorted(files, reverse=True)

def make_backup() -> Path | None:
    from .settings import create_backup

    return create_backup()

def restore_backup(src: Path) -> bool:
    if not src.exists():
        return False
    # backup current before restore
    from .settings import create_backup

    if SETTINGS_FILE.exists():
        create_backup()
    import shutil

    shutil.copy2(src, SETTINGS_FILE)
    return True

# clean helpers - kept testable for CLI

def parse_clean_selection(raw: str, total: int) -> list[int] | str:
    """
    Parse user input for clean_backups.
    Returns list of 1-based indices, or 'all', or 'keep:N' string.
    Raises ValueError on invalid input.
    """
    raw = raw.strip().lower()
    if raw == "all":
        return "all"
    m = re.fullmatch(r"keep:(\d+)", raw)
    if m:
        return f"keep:{int(m.group(1))}"
    if re.fullmatch(r"[0-9,\s]+", raw):
        nums = [int(x) for x in re.split(r"[\s,]+", raw) if x.strip()]
        if not nums:
            raise ValueError("No numbers given.")
        for n in nums:
            if n < 1 or n > total:
                raise ValueError(f"Index {n} out of range 1..{total}.")
        return sorted(set(nums))
    raise ValueError("Use 2,3,4  or  all  or  keep:N")

def clean_backups_by_indices(backups: list[Path], indices: list[int]) -> list[Path]:
    """Delete backups at 1-based indices. Returns list of deleted paths."""
    deleted: list[Path] = []
    # indices refers to display order (newest-first as from scan_backups)
    for idx in sorted(indices, reverse=True):
        p = backups[idx - 1]
        p.unlink(missing_ok=True)
        deleted.append(p)
    return deleted

def clean_keep_n(backups: list[Path], keep: int) -> list[Path]:
    """Keep newest `keep`, delete the rest. Returns deleted."""
    if keep >= len(backups):
        return []
    to_delete = backups[keep:]  # backups is newest-first
    for p in to_delete:
        p.unlink(missing_ok=True)
    return to_delete
