"""ClaudeShift CLI — cross-platform port of change-cc Bash tool."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import questionary
from questionary import Style as QStyle

from . import __version__
from .config import CONTEXT_PRESETS, SETTINGS_FILE, STANDARD_MODELS
from .settings import (
    build_model_with_context,
    current_config_snapshot,
    ensure_settings_file,
    extract_model_context,
    get_all_model_variants,
    get_env_value,
    get_value,
    update_env,
    update_field,
)
from .backups import (
    BACKUP_PREFIX,
    clean_backups_by_indices,
    clean_keep_n,
    parse_clean_selection,
    scan_backups,
    restore_backup,
)
from .updater import check_update

console = Console()

Q_STYLE = QStyle([
    ("qmark", "fg:cyan bold"),
    ("question", "fg:cyan bold"),
    ("answer", "fg:green bold"),
    ("pointer", "fg:yellow bold"),
    ("highlighted", "fg:yellow bold"),
    ("selected", "fg:green"),
])

def show_current_config() -> None:
    snap = current_config_snapshot()
    model_variants = get_all_model_variants()

    table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("🌐 Base URL", snap["base_url"] or "(not set)")
    table.add_row("🔑 Auth Token", snap["auth_token_masked"])
    table.add_row("🤖 Main model (.model)", snap["model_field"] or "(not set)")
    table.add_row("⚡ Effort Level", snap["effort_level"] or "(not set)")
    table.add_row("🎨 Theme", snap["theme"] or "(not set)")
    table.add_row("", "")
    for key, label, val in model_variants:
        table.add_row(f"  {label}", f"[dim]{key}[/dim] = {val or '(not set)'}")

    console.print(Panel(table, title=f"Current Claude Code Configuration  (v{__version__})", border_style="cyan", padding=(0, 1)))
    console.print(f"[dim]Settings: {SETTINGS_FILE}[/dim]\n")

def show_version() -> None:
    console.print(f"[cyan]ClaudeShift[/cyan] v[bold]{__version__}[/bold]  [dim]({SETTINGS_FILE})[/dim]")

def change_endpoint() -> None:
    console.print("\n[bold cyan]═══ Change Endpoint URL (ANTHROPIC_BASE_URL) ═══[/bold cyan]\n")
    current = get_env_value("ANTHROPIC_BASE_URL")
    console.print(f"[dim]Current:[/dim] {current or '(not set)'}\n")
    choice = questionary.select(
        "Select endpoint:",
        choices=[
            questionary.Choice(f"Keep current: {current}" if current else "Keep current: (not set)", value="keep"),
            questionary.Choice("https://api.anthropic.com (official)", value="https://api.anthropic.com"),
            questionary.Choice("Custom URL", value="custom"),
            questionary.Choice("Back", value="back"),
        ],
        style=Q_STYLE,
    ).ask()
    if choice is None or choice in ("keep", "back"):
        console.print("[dim]Cancelled.[/dim]")
        return
    if choice == "custom":
        custom = questionary.text("Enter custom URL:", style=Q_STYLE).ask()
        if not custom or not custom.strip():
            console.print("[yellow]No input — cancelled.[/yellow]")
            return
        choice = custom.strip()
    update_env("ANTHROPIC_BASE_URL", choice)
    console.print(f"[green]✓ Updated ANTHROPIC_BASE_URL → {choice}[/green]")

def change_auth_token() -> None:
    console.print("\n[bold cyan]═══ Change API Key (ANTHROPIC_AUTH_TOKEN) ═══[/bold cyan]\n")
    from .settings import mask_token

    current = get_env_value("ANTHROPIC_AUTH_TOKEN") or get_env_value("ANTHROPIC_API_KEY")
    console.print(f"[dim]Current:[/dim] {mask_token(current)}\n")
    token = questionary.password("Enter new auth token (leave empty to cancel):").ask()
    if token is None or not token.strip():
        console.print("[dim]Cancelled.[/dim]")
        return
    token = token.strip()
    update_env("ANTHROPIC_AUTH_TOKEN", token)
    console.print(f"[green]✓ Auth token updated → {mask_token(token)}[/green]")

def _pick_variant(prompt: str = "Select model variant:") -> tuple[str, str, str] | None:
    variants = get_all_model_variants()
    choices = []
    for key, label, val in variants:
        disp = val or "(not set)"
        choices.append(questionary.Choice(f"{label} ({key}) = {disp}", value=(key, label, val)))
    choices.append(questionary.Choice("Back", value=None))
    result = questionary.select(prompt, choices=choices, style=Q_STYLE).ask()
    return result

def _pick_context(current_model: str, current_ctx: str) -> tuple[str | None, str | None]:
    """Return (new_model_value or None for cancel, action)."""
    presets = CONTEXT_PRESETS
    choices: list[questionary.Choice] = []
    for p in presets:
        marker = " ← current" if p == current_ctx else ""
        choices.append(questionary.Choice(f"[{p:>6}] {marker}", value=p))
    choices.extend([
        questionary.Choice("Custom context (e.g. 500k, 1m)", value="__custom__"),
        questionary.Choice("Remove context (use model default)", value="__remove__"),
        questionary.Choice("Change model name (keep current context)", value="__rename__"),
        questionary.Choice("Back", value="__back__"),
    ])
    console.print(f"[dim]Model:[/dim] {current_model or '(not set)'}  [dim]Context:[/dim] {current_ctx or '(none)'}\n")
    picked = questionary.select("Select context:", choices=choices, style=Q_STYLE).ask()
    return picked, current_model

def change_model_context() -> None:
    while True:
        console.print("\n[bold cyan]═══ Change Model Variant Context ═══[/bold cyan]\n")
        picked = _pick_variant("Select variant to change context:")
        if picked is None:
            return
        key, label, val = picked
        model, ctx = extract_model_context(val)
        console.print(f"\n[bold]Variant:[/bold] {label} ({key})")
        console.print(f"[dim]Current value:[/dim] {val or '(not set)'}  → model=[cyan]{model}[/cyan] ctx=[cyan]{ctx or '(none)'}[/cyan]\n")

        presets = CONTEXT_PRESETS
        choices: list[questionary.Choice] = []
        for p in presets:
            marker = " ← current" if p == ctx else ""
            choices.append(questionary.Choice(f"[{p:>6}]{marker}", value=p))
        choices.extend([
            questionary.Choice("Custom context (e.g. 500k, 1m)", value="__custom__"),
            questionary.Choice("Remove context (use model default)", value="__remove__"),
            questionary.Choice("Change model name (keep current context)", value="__rename__"),
            questionary.Choice("Back to variant selection", value="__back__"),
        ])
        sel = questionary.select("Select context option:", choices=choices, style=Q_STYLE).ask()
        if sel is None or sel == "__back__":
            continue

        new_value: str | None = None
        model_to_use = model

        if sel in presets:
            if not model_to_use:
                model_to_use = questionary.text("No model name set — enter model name:", style=Q_STYLE).ask()
                if not model_to_use or not model_to_use.strip():
                    console.print("[yellow]No model name — skipping.[/yellow]")
                    continue
                model_to_use = model_to_use.strip()
            new_value = f"{model_to_use}[{sel}]"
        elif sel == "__custom__":
            custom = questionary.text("Enter custom context (e.g. 500k, 1m, 200k):", style=Q_STYLE).ask()
            if not custom or not custom.strip():
                console.print("[yellow]No input — skipping.[/yellow]")
                continue
            custom = custom.strip()
                        from .settings import parse_tokens

            if parse_tokens(custom) is None:
                console.print(f"[red]Invalid context '{custom}' — use like 500k, 1m[/red]")
                continue
            if not model_to_use:
                model_to_use = questionary.text("Enter model name:", style=Q_STYLE).ask()
                if not model_to_use or not model_to_use.strip():
                    console.print("[yellow]Cancelled.[/yellow]")
                    continue
                model_to_use = model_to_use.strip()
            new_value = f"{model_to_use}[{custom}]"
        elif sel == "__remove__":
            if not model_to_use:
                console.print("[yellow]No model set — nothing to remove.[/yellow]")
                continue
            new_value = model_to_use
        elif sel == "__rename__":
            new_model = questionary.text(f"Enter new model name (current: {model_to_use or '(none)'}):", default=model_to_use, style=Q_STYLE).ask()
            if not new_model or not new_model.strip():
                console.print("[yellow]Cancelled.[/yellow]")
                continue
            new_model = new_model.strip()
            if ctx:
                new_value = f"{new_model}[{ctx}]"
            else:
                new_value = new_model

        if new_value is not None:
            update_env(key, new_value)
            console.print(f"[green]✓ {label} ({key}) → {new_value}[/green]")
                        cont = questionary.confirm("Change another variant?", default=False, style=Q_STYLE).ask()
            if not cont:
                return

def change_model_variants() -> None:
    while True:
        console.print("\n[bold cyan]═══ Change Model Variants (full model name) ═══[/bold cyan]\n")
        picked = _pick_variant("Select variant to change model name:")
        if picked is None:
            return
        key, label, val = picked
        model, ctx = extract_model_context(val)
        console.print(f"[dim]Current:[/dim] {val or '(not set)'}  → model=[cyan]{model}[/cyan] ctx=[cyan]{ctx or '(none)'}[/cyan]\n")
        new_model = questionary.text(f"Enter new model for {label} ({key}):", default=model, style=Q_STYLE).ask()
        if new_model is None:
            return
        new_model = new_model.strip()
        if not new_model:
            console.print("[yellow]Empty — cancelled.[/yellow]")
            continue
        # keep existing context suffix if present
        if ctx:
            new_value = f"{new_model}[{ctx}]"
        else:
            new_value = new_model
        update_env(key, new_value)
        console.print(f"[green]✓ {label} ({key}) → {new_value}[/green]")
        cont = questionary.confirm("Change another variant?", default=False, style=Q_STYLE).ask()
        if not cont:
            return

def change_main_model() -> None:
    console.print("\n[bold cyan]═══ Change Main Model (top-level 'model' field) ═══[/bold cyan]\n")
    current = get_value("model")
    console.print(f"[dim]Current 'model':[/dim] {current or '(not set)'}\n")
    choice = questionary.select(
        "Select main model:",
        choices=[
            questionary.Choice("sonnet", value="sonnet"),
            questionary.Choice("opus", value="opus"),
            questionary.Choice("haiku", value="haiku"),
            questionary.Choice("Custom model name", value="__custom__"),
            questionary.Choice("Cancel", value="__cancel__"),
        ],
        style=Q_STYLE,
    ).ask()
    if choice is None or choice == "__cancel__":
        console.print("[dim]Cancelled.[/dim]")
        return
    if choice == "__custom__":
        custom = questionary.text("Enter custom model string:", style=Q_STYLE).ask()
        if not custom or not custom.strip():
            console.print("[yellow]Cancelled.[/yellow]")
            return
        choice = custom.strip()
    update_field("model", choice)
    console.print(f"[green]✓ Main model → {choice}[/green]")

def _format_backup_name(p: Path) -> str:
    # settings.json.backup.YYYYMMDD_HHMMSS
    name = p.name.replace(BACKUP_PREFIX, "")
    return name

def backup_menu() -> None:
    while True:
        console.clear()
        console.print(Panel("[bold]BACKUP MENU[/bold]", border_style="cyan"))
        backups = scan_backups()
        if not backups:
            console.print("[yellow]No backups found in ~/.claude/[/yellow]\n")
        else:
            console.print(f"[dim]Found {len(backups)} backup(s):[/dim]")
            for p in backups:
                console.print(f"  • {_format_backup_name(p)}")
            console.print()

        choice = questionary.select(
            "Backup actions:",
            choices=[
                questionary.Choice("1) Make Backup (save current settings)", value="make"),
                questionary.Choice("2) Restore Backup", value="restore"),
                questionary.Choice("3) Clean / Delete Old Backups", value="clean"),
                questionary.Choice("0) Back to Main Menu", value="back"),
            ],
            style=Q_STYLE,
        ).ask()
        if choice is None or choice == "back":
            return
        if choice == "make":
            from .settings import create_backup

            dest = create_backup()
            if dest:
                console.print(f"[green]✓ Backup created: {dest.name}[/green]")
            else:
                console.print("[red]No settings file to backup.[/red]")
            questionary.text("Press Enter to continue").ask()
        elif choice == "restore":
            _restore_flow(backups)
            questionary.text("Press Enter to continue").ask()
        elif choice == "clean":
            _clean_flow(backups)
            questionary.text("Press Enter to continue").ask()

def _restore_flow(backups: list[Path]) -> None:
    if not backups:
        console.print("[yellow]No backups to restore.[/yellow]")
        return
    choices = [questionary.Choice(f"{i+1}) {_format_backup_name(p)}", value=p) for i, p in enumerate(backups)]
    choices.append(questionary.Choice("Custom path", value="__custom__"))
    choices.append(questionary.Choice("Cancel", value=None))
    picked = questionary.select("Select backup to restore:", choices=choices, style=Q_STYLE).ask()
    if picked is None:
        console.print("[dim]Cancelled.[/dim]")
        return
    if picked == "__custom__":
        custom = questionary.text("Enter full path to backup file:", style=Q_STYLE).ask()
        if not custom or not custom.strip():
            console.print("[yellow]Cancelled.[/yellow]")
            return
        picked = Path(custom.strip()).expanduser()
    if not Path(picked).exists():
        console.print(f"[red]File not found: {picked}[/red]")
        return
    ok = restore_backup(Path(picked))
    if ok:
        console.print(f"[green]✓ Restored from {Path(picked).name}[/green]")
    else:
        console.print("[red]Restore failed.[/red]")

def _clean_flow(backups: list[Path]) -> None:
    if not backups:
        console.print("[yellow]No backups to clean.[/yellow]")
        return
    console.print("[dim]Backups (newest first):[/dim]")
    for i, p in enumerate(backups, 1):
        console.print(f"  {i}) {_format_backup_name(p)}")
    console.print("\n[dim]Enter: 2,3,4  or  all  or  keep:N  (e.g. keep:5 keeps newest 5)[/dim]")
    raw = questionary.text("What to delete? (or 'cancel'):", style=Q_STYLE).ask()
    if raw is None or raw.strip().lower() in ("", "cancel", "0"):
        console.print("[dim]Cancelled.[/dim]")
        return
    raw = raw.strip()
    try:
        parsed = parse_clean_selection(raw, len(backups))
    except ValueError as e:
        console.print(f"[red]Invalid input: {e}[/red]")
        return

    if isinstance(parsed, str):
        if parsed == "all":
            confirm = questionary.confirm(f"Delete ALL {len(backups)} backups? This cannot be undone.", default=False, style=Q_STYLE).ask()
            if not confirm:
                console.print("[dim]Cancelled.[/dim]")
                return
            for p in backups:
                p.unlink(missing_ok=True)
            console.print(f"[green]✓ Deleted {len(backups)} backups.[/green]")
        elif parsed.startswith("keep:"):
            keep = int(parsed.split(":")[1])
            if keep >= len(backups):
                console.print(f"[yellow]You have {len(backups)} backups — keeping {keep} means nothing to delete.[/yellow]")
                return
            deleted = clean_keep_n(backups, keep)
            console.print(f"[green]✓ Deleted {len(deleted)} backups, kept newest {keep}.[/green]")
    else:
                confirm = questionary.confirm(f"Delete {len(parsed)} backup(s) at {parsed}? ", default=False, style=Q_STYLE).ask()
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            return
        deleted = clean_backups_by_indices(backups, parsed)
        console.print(f"[green]✓ Deleted {len(deleted)} backup(s).[/green]")

def do_update_check() -> None:
    console.print("\n[bold cyan]═══ Update Check (from GitHub) ═══[/bold cyan]\n")
    console.print(f"[dim]Current version: v{__version__}[/dim]")
    console.print("[dim]Checking GitHub...[/dim]")
    info = check_update()
    remote = info.get("remote")
    if remote is None:
        console.print("[yellow]Could not fetch remote version (network or repo not yet published).[/yellow]")
        console.print("[dim]Try: pip install --upgrade claudeshift[/dim]")
        return
    console.print(f"[dim]Remote version: v{remote}[/dim]")
    if info.get("has_update"):
        console.print(f"[yellow]Update available: v{__version__} → v{remote}[/yellow]")
        console.print("[dim]Run: pip install --upgrade claudeshift  or  pipx upgrade claudeshift[/dim]")
    else:
        console.print("[green]✓ Already up to date.[/green]")

def interactive_menu() -> None:
    while True:
        console.clear()
        show_current_config()
        console.print(Panel("CLAUDESHIFT MENU  (v" + __version__ + ")", border_style="cyan"))

        choice = questionary.select(
            "What do you want to do?",
            choices=[
                questionary.Choice("1) Change Endpoint URL (ANTHROPIC_BASE_URL)", value="1"),
                questionary.Choice("2) Change Model Context (model[500k], model[1m])", value="2"),
                questionary.Choice("3) Change Model Variants (Default, Opus, Sonnet, Haiku...)", value="3"),
                questionary.Choice("4) Change Main Model field (.model)", value="4"),
                questionary.Choice("5) Change API Key (ANTHROPIC_AUTH_TOKEN)", value="5"),
                questionary.Choice("6) Backup Menu (make / restore / clean)", value="6"),
                questionary.Choice("7) Update Check (from GitHub)", value="7"),
                questionary.Choice("0) Exit", value="0"),
            ],
            style=Q_STYLE,
        ).ask()

        if choice is None or choice == "0":
            console.print("[dim]Goodbye! 👋[/dim]")
            break
        elif choice == "1":
            change_endpoint()
            questionary.text("Press Enter to continue").ask()
        elif choice == "2":
            change_model_context()
        elif choice == "3":
            change_model_variants()
        elif choice == "4":
            change_main_model()
            questionary.text("Press Enter to continue").ask()
        elif choice == "5":
            change_auth_token()
            questionary.text("Press Enter to continue").ask()
        elif choice == "6":
            backup_menu()
        elif choice == "7":
            do_update_check()
            questionary.text("Press Enter to continue").ask()

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="claudeshift",
        description="Claude Code Model & Settings Switcher — cross-platform (Windows, Linux, macOS)",
        add_help=False,
    )
    p.add_argument("model", nargs="?", help='Direct model set, e.g. "anthropic/claude-sonnet[1m]"')
    p.add_argument("-h", "--help", action="store_true", help="Show help")
    p.add_argument("-v", "--version", action="store_true", help="Show version")
    p.add_argument("-l", "--list", action="store_true", help="Show current configuration")
    p.add_argument("-U", "--update", action="store_true", help="Check for updates from GitHub")
    p.add_argument("--install", action="store_true", help="Install hint (pip/pipx)")
    p.add_argument("--uninstall", action="store_true", help="Uninstall hint")
    return p

def print_help(parser: argparse.ArgumentParser) -> None:
    console.print(Panel.fit("[bold cyan]ClaudeShift[/bold cyan] — Claude Code Model & Settings Switcher", border_style="cyan"))
    console.print(f"[dim]Settings file:[/dim] {SETTINGS_FILE}\n")
    console.print("[bold]Usage:[/bold] claudeshift [OPTIONS] [MODEL]\n")
    console.print("[bold]Options:[/bold]")
    console.print("  [cyan]-h, --help[/cyan]       Show this help")
    console.print("  [cyan]-v, --version[/cyan]    Show version")
    console.print("  [cyan]-l, --list[/cyan]       Show current configuration")
    console.print("  [cyan]-U, --update[/cyan]     Check for updates from GitHub")
    console.print("  [cyan]--install[/cyan]       Install hint")
    console.print("  [cyan]--uninstall[/cyan]     Uninstall hint\n")
    console.print("[bold]Examples:[/bold]")
    console.print("  claudeshift                              [dim]# Interactive menu[/dim]")
    console.print('  claudeshift "anthropic/claude-sonnet[1m]" [dim]# Set default model directly[/dim]')
    console.print("  claudeshift -v                           [dim]# Show version[/dim]")
    console.print("  claudeshift --list                       [dim]# Show current config[/dim]\n")
    console.print("[bold]Features:[/bold]")
    console.print("  • Endpoint URL, Auth Token, Main model, Model variants & context")
    console.print("  • Backup / restore / clean (multi-select, all, keep:N)")
    console.print("  • Cross-platform: Windows, Linux, macOS  • Direct CLI + Interactive menu")

def main(argv: list[str] | None = None) -> None:
    ensure_settings_file()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.help:
        print_help(parser)
        return
    if args.version:
        show_version()
        return
    if args.list:
        show_current_config()
        return
    if args.update:
        do_update_check()
        return
    if args.install:
        console.print("[dim]Already installed via pip/pipx.[/dim]")
        console.print("  pip install -e .   [dim]# dev[/dim]")
        console.print("  pipx install .     [dim]# isolated[/dim]")
        return
    if args.uninstall:
        console.print("[dim]To uninstall:[/dim] pip uninstall claudeshift  /  pipx uninstall claudeshift")
        return

    # direct model mode: claudeshift "anthropic/claude-sonnet[1m]"
    if args.model:
        raw = args.model.strip()
        # treat as help/version flags that slipped as positional? already handled
        model, ctx = extract_model_context(raw)
        if not model:
            console.print(f"[red]Invalid model: {raw}[/red]")
            sys.exit(1)
                if ctx:
            from .settings import parse_tokens

            if parse_tokens(ctx) is None:
                console.print(f"[red]Invalid context '{ctx}' in '{raw}'[/red]")
                sys.exit(1)
        update_env("ANTHROPIC_MODEL", raw)
        console.print(f"[green]✓ Default model → {raw}[/green]")
        return

        try:
        interactive_menu()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Bye! 👋[/dim]")
