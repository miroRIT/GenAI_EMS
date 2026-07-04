#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from emergencypulse.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the EmergencyPulse OpenAPI schema.")
    parser.add_argument(
        "--output",
        default="docs/openapi.json",
        help="Destination file for the exported OpenAPI JSON schema.",
    )
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote OpenAPI schema to {output}")


if __name__ == "__main__":
    main()
