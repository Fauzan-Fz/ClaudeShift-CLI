# ClaudeShift-CLI

> **Claude Code Model & Settings Switcher** — Windows, Linux, macOS. Python port of [`Change-Config-CC`](https://github.com/Fauzan-Fz/Change-Config-CC) (Bash).

Manage Claude Code models, API endpoints, and auth tokens in `~/.claude/settings.json` without editing JSON by hand.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔄 Model Switching | Switch main model and all variants (Opus, Sonnet, Haiku, Fable, Small/Fast) |
| 📏 Context Window | Set per-model context: `model[500k]`, `model[1m]`, `model[2m]` |
| 🌐 Endpoint | Switch between local proxy, official Anthropic API, or custom `ANTHROPIC_BASE_URL` |
| 🔑 Auth Token | Update `ANTHROPIC_AUTH_TOKEN` securely (masked display) |
| 💾 Backup / Restore | Auto-backup before every change + manual backup and restore |
| 🧹 Clean Backups | Delete with multi-select `2,3,4`, `all`, or `keep:5` |
| 🎨 Interactive Menu | Color-coded `rich` + `questionary` prompts, consistent layout |
| ⚡ Direct Mode | `claudeshift "anthropic/claude-sonnet[1m]"` for quick updates |
| 🚀 Update Check | Check for the latest version from GitHub |

## 📦 Installation

```bash
git clone https://github.com/Fauzan-Fz/ClaudeShift-CLI.git
cd ClaudeShift-CLI
pip install -e .

# isolated install (recommended)
pipx install .
```

**Requirements:** Python 3.9+ · Windows / Linux / macOS

**Settings file:** `~/.claude/settings.json` on all platforms (Windows resolves to `%USERPROFILE%\.claude\settings.json` via `Path.home()`).

## 🚀 Usage

```bash
claudeshift                              # interactive menu
claude-shift                             # alias
change-cc                                # alias (compatible with Change-Config-CC)

claudeshift "anthropic/claude-sonnet[1m]" # directly set ANTHROPIC_MODEL
claudeshift -v / --version
claudeshift -l / --list
claudeshift -U / --update
claudeshift -h / --help
```

### Interactive Menu

```
1) Change Endpoint URL (ANTHROPIC_BASE_URL)
2) Change Model Context (model[500k], model[1m])
3) Change Model Variants (Default, Opus, Sonnet, Haiku...)
4) Change Main Model field (.model)
5) Change API Key (ANTHROPIC_AUTH_TOKEN)
6) Backup Menu (make / restore / clean)
7) Update Check (from GitHub)
0) Exit
```

## 🔧 Settings File

ClaudeShift reads and writes `~/.claude/settings.json`:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
    "ANTHROPIC_MODEL": "anthropic/claude-sonnet[1m]",
    "ANTHROPIC_SMALL_FAST_MODEL": "anthropic/claude-haiku",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "anthropic/claude-opus",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "anthropic/claude-sonnet",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "anthropic/claude-haiku",
    "ANTHROPIC_AUTH_TOKEN": "..."
  },
  "model": "haiku",
  "effortLevel": "high"
}
```

Auto-backups are saved alongside it as `settings.json.backup.YYYYMMDD_HHMMSS`.

## 🧪 Development

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
claudeshift --help
claudeshift --list
claudeshift --version
```

## 📝 License

MIT — see [LICENSE](LICENSE)

## 🔗 Related

- Original Bash version (Linux-only, requires `jq`): [Fauzan-Fz/Change-Config-CC](https://github.com/Fauzan-Fz/Change-Config-CC)
