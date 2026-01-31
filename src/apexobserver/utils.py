from __future__ import annotations
import hashlib
from pathlib import Path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_hashes_sha256(root_dir: Path) -> Path:
    lines = []
    for p in sorted(root_dir.rglob("*")):
        if p.is_file() and p.name != "hashes.sha256":
            lines.append(f"{sha256_file(p)}  {p.relative_to(root_dir).as_posix()}")
    out = root_dir / "hashes.sha256"
    out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return out
