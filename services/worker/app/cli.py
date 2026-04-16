from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast

from .scanner import result_to_json, scan_legacycart


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cloud-migration-cockpit-worker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan a migration candidate directory")
    scan_parser.add_argument("root", type=Path, help="Path to the legacy system root")
    scan_parser.add_argument("--json", action="store_true", help="Emit JSON only")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "scan":
        result = scan_legacycart(args.root)
        payload = cast(str, result_to_json(result, as_dict=False))
        if args.json:
            sys.stdout.write(payload)
        else:
            sys.stdout.write(payload + "\n")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
