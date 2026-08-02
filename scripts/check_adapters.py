import tempfile
from pathlib import Path

from athena.integrations import generate_adapters


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        outputs = generate_adapters(Path(directory))
        if len(outputs) != 6 or not all(path.is_file() for path in outputs):
            raise SystemExit("Adapter generation failed")
        for path in outputs:
            if len(path.read_text(encoding="utf-8").splitlines()) > 35:
                raise SystemExit(f"Adapter is no longer token-frugal: {path.name}")
    print("Validated generated adapters")


if __name__ == "__main__":
    main()
