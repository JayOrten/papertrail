from __future__ import annotations

import tomllib
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "papertrail"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    return tomllib.loads(CONFIG_FILE.read_text())


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    for key, value in config.items():
        if isinstance(value, str):
            lines.append(f'{key} = "{value}"')
        else:
            lines.append(f"{key} = {value}")
    CONFIG_FILE.write_text("\n".join(lines) + "\n")


def get_profile_repo_path() -> Path:
    config = load_config()
    path = config.get("profile_repo_path")
    if not path:
        raise SystemExit(
            "No profile repo configured. Run `papertrail init` first."
        )
    return Path(path)


def get_papers_path() -> Path:
    return get_profile_repo_path() / "data" / "papers.json"
