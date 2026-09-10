# ClaudeShift-CLI

> **Claude Code Model & Settings Switcher** — cross-platform (Windows, Linux, macOS). Port Python dari `Change-Config-CC` (Bash).

Manage Claude Code models, API endpoints & auth tokens via `~/.claude/settings.json` tanpa edit JSON manual.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔄 Model Switching | Ganti main model & semua varian (Opus, Sonnet, Haiku, Fable, Small/Fast) |
| 📏 Context Window | `model[500k]`, `model[1m]`, `model[2m]` |
| 🌐 Endpoint | Switch proxy / official / custom `ANTHROPIC_BASE_URL` |
| 🔑 Auth Token | Update `ANTHROPIC_AUTH_TOKEN` dengan mask |
| 💾 Backup/Restore | Auto-backup sebelum perubahan + manual backup/restore |
| 🧹 Clean Backups | Hapus `2,3,4` / `all` / `keep:5` |
| 🎨 Interactive Menu | `rich` + `questionary`, warna konsisten |
| ⚡ Direct Mode | `claudeshift "anthropic/claude-sonnet[1m]"` |
| 🚀 Update Check | Cek versi terbaru dari GitHub |

## 📦 Installation

```bash
# dari source (dev)
git clone https://github.com/Fauzan-Fz/ClaudeShift-CLI.git
cd ClaudeShift-CLI
pip install -e .

# atau isolated
pipx install .

# nanti setelah publish ke PyPI
pip install claudeshift
pipx install claudeshift
```

Python 3.9+ • Windows / Linux / macOS • settings file: `~/.claude/settings.json` (Windows: `%USERPROFILE%\.claude\settings.json` — sama, via `Path.home()`)

## 🚀 Usage

```bash
claudeshift                              # interactive menu
claude-shift                             # alias
change-cc                                # alias (kompatibel)

claudeshift "anthropic/claude-sonnet[1m]" # direct set ANTHROPIC_MODEL
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

Tool membaca & menulis `~/.claude/settings.json`:

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

Auto-backup dibuat di folder yang sama: `settings.json.backup.YYYYMMDD_HHMMSS`

## 🧪 Dev

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
claudeshift --help
claudeshift --list
claudeshift --version
```

## 📝 License

MIT — see [LICENSE](LICENSE)

## 🔗 Related

- Original Bash version: [Fauzan-Fz/Change-Config-CC](https://github.com/Fauzan-Fz/Change-Config-CC) (Linux-only, requires `jq`)
