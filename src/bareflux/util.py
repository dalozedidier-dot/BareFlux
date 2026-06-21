import json
from pathlib import Path


def load_json_file(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise SystemExit(f"Config not found: {path}") from e
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON in config: {path}: {e}") from e
