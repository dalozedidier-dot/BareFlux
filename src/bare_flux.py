import subprocess
from pathlib import Path


def main() -> int:
    here = Path(__file__).resolve()
    root = here.parent.parent.parent
    script = root / "BareFlux" / "run_modules.sh"
    return subprocess.call(["bash", str(script)])


if __name__ == "__main__":
    raise SystemExit(main())
