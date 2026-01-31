from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict
from jsonschema import Draft202012Validator

def _load_schema(schema_path: Path) -> Dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))

def validate_config(cfg: Dict[str, Any], schema_path: Path) -> None:
    Draft202012Validator(_load_schema(schema_path)).validate(cfg)

def validate_report(rep: Dict[str, Any], schema_path: Path) -> None:
    Draft202012Validator(_load_schema(schema_path)).validate(rep)
