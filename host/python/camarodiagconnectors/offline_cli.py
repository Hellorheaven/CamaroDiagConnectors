"""Offline-only backup, verify and targeted patch preview. No device IO."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Sequence

from .backup import backup_manifest, write_bundle, verify_bundle
from .memory import Geometry, Patch, Region, Technology, plan_patches


def _number(text: str) -> int:
    try:
        return int(text, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid integer: {text}") from exc


def _region(text: str) -> Region:
    try:
        start, end = text.split(":", 1)
        return Region(_number(start), _number(end))
    except (ValueError, argparse.ArgumentTypeError) as exc:
        raise argparse.ArgumentTypeError("Region must be START:END") from exc


def _patch(text: str) -> Patch:
    try:
        offset, hex_bytes = text.split(":", 1)
        return Patch(_number(offset), bytes.fromhex(hex_bytes))
    except (ValueError, argparse.ArgumentTypeError) as exc:
        raise argparse.ArgumentTypeError("Patch must be OFFSET:HEXBYTES") from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CamaroDiagConnectors OFFLINE tooling")
    commands = parser.add_subparsers(dest="action", required=True)

    backup = commands.add_parser("backup", help="Save a local original file + integrity manifest")
    backup.add_argument("--target", required=True)
    backup.add_argument("--capacity", type=_number, required=True)
    backup.add_argument("--offset", type=_number, default=0)
    backup.add_argument("--input", required=True, type=Path)
    backup.add_argument("--second-read", type=Path)
    backup.add_argument("--output-prefix", type=Path, required=True)

    verify = commands.add_parser("verify", help="Verify a local backup bundle")
    verify.add_argument("--prefix", required=True, type=Path)

    plan = commands.add_parser("plan", help="Dry-run changes; no device programming")
    plan.add_argument("--target", required=True)
    plan.add_argument("--technology", required=True, choices=[t.value for t in Technology])
    plan.add_argument("--page-size", required=True, type=_number)
    plan.add_argument("--erase-size", type=_number)
    plan.add_argument("--input", required=True, type=Path)
    plan.add_argument("--patch", required=True, action="append", type=_patch)
    plan.add_argument("--protected", action="append", type=_region, default=[])
    plan.add_argument("--proposed-output", type=Path)
    return parser


def run(argv: Sequence[str] | None = None) -> dict[str, object]:
    args = _parser().parse_args(argv)
    if args.action == "backup":
        image = args.input.read_bytes()
        second = args.second_read.read_bytes() if args.second_read else None
        manifest = backup_manifest(args.target, args.capacity, args.offset, image, second)
        write_bundle(args.output_prefix, image, manifest)
        return {"action": "backup", "manifest": asdict(manifest), "physical_read_verified": False}

    if args.action == "verify":
        manifest = verify_bundle(args.prefix)
        return {"action": "verify", "manifest": asdict(manifest), "physical_read_verified": False}

    original = args.input.read_bytes()
    geometry = Geometry(args.target, Technology(args.technology), len(original), args.page_size,
                        args.erase_size, tuple(args.protected))
    plan = plan_patches(geometry, original, args.patch)
    if args.proposed_output is not None:
        args.proposed_output.parent.mkdir(parents=True, exist_ok=True)
        with args.proposed_output.open("xb") as out:
            out.write(plan.proposed_image)
    return {
        "action": "plan",
        "chip": plan.chip,
        "changed_bytes": plan.changed_bytes,
        "before_sha256": plan.before_sha256,
        "after_sha256": plan.after_sha256,
        "write_authorized": False,
        "physical_read_verified": False,
        "operations": [
            {"start": o.region.start, "end_exclusive": o.region.end, "method": o.method,
             "changed_bytes": o.changed_bytes, "original_sha256": o.original_sha256,
             "proposed_sha256": o.proposed_sha256}
            for o in plan.operations
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    try:
        result = run()
    except (OSError, ValueError) as exc:
        parser.exit(status=2, message=f"OFFLINE ERROR: {exc}\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
