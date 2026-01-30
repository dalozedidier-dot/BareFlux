import hashlib
from pathlib import Path
from typing import Iterable, Tuple


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def write_hashes_file(run_dir: Path, rel_paths: Iterable[Path], out_name: str = "hashes.sha256") -> Path:
    """Write sha256 for each rel_path (relative to run_dir). Does not hash the hashes file itself."""
    out_path = run_dir / out_name
    lines = []
    for rel in rel_paths:
        abs_path = run_dir / rel
        digest = sha256_file(abs_path)
        lines.append(f"{digest}  {rel.as_posix()}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path
