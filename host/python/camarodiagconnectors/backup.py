"""Immutable offline backup bundles and integrity metadata.

Nothing here proves the source came from an actual memory chip or ECU.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from pathlib import Path


@dataclass(frozen=True)
class Manifest:
    schema: int
    target: str
    declared_capacity: int
    region_offset: int
    region_length: int
    image_sha256: str
    secondary_read_matched: bool | None
    complete_coverage: bool
    source: str
    physical_origin_verified: bool = False
    restoration_verified: bool = False


def backup_manifest(
    target: str,
    capacity: int,
    offset: int,
    image: bytes,
    secondary_read: bytes | None = None,
    *,
    source: str = "offline-file",
) -> Manifest:
    if not target.strip() or capacity <= 0 or offset < 0 or not isinstance(image, bytes):
        raise ValueError("Invalid target or region")
    if not image or offset + len(image) > capacity or not source.strip():
        raise ValueError("Empty, out-of-range, or unidentifiable backup")
    if secondary_read is not None and image != secondary_read:
        raise ValueError("Secondary read disagrees")
    return Manifest(
        schema=1,
        target=target,
        declared_capacity=capacity,
        region_offset=offset,
        region_length=len(image),
        image_sha256=sha256(image).hexdigest(),
        secondary_read_matched=(True if secondary_read is not None else None),
        complete_coverage=(offset == 0 and len(image) == capacity),
        source=source,
    )


def write_bundle(prefix: Path, image: bytes, manifest: Manifest) -> None:
    """Create backup .bin/.json files exclusively, never overwrite."""
    if sha256(image).hexdigest() != manifest.image_sha256 or len(image) != manifest.region_length:
        raise ValueError("Image does not match manifest")
    binary = prefix.with_suffix(".bin")
    metadata = prefix.with_suffix(".json")
    if binary.exists() or metadata.exists():
        raise FileExistsError("Original backup files must not be overwritten")
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary_created = False
    metadata_created = False
    try:
        with binary.open("xb") as out:
            binary_created = True
            out.write(image)
        with metadata.open("x", encoding="utf-8") as out:
            metadata_created = True
            json.dump(asdict(manifest), out, indent=2, sort_keys=True)
            out.write("\n")
    except BaseException:
        if metadata_created:
            metadata.unlink(missing_ok=True)
        if binary_created:
            binary.unlink(missing_ok=True)
        raise


def verify_bundle(prefix: Path) -> Manifest:
    metadata = json.loads(prefix.with_suffix(".json").read_text(encoding="utf-8"))
    manifest = Manifest(**metadata)
    image = prefix.with_suffix(".bin").read_bytes()
    if manifest.schema != 1 or len(image) != manifest.region_length:
        raise ValueError("Invalid schema or image length")
    if not manifest.target.strip() or not manifest.source.strip() or not image:
        raise ValueError("Missing backup metadata")
    if sha256(image).hexdigest() != manifest.image_sha256:
        raise ValueError("Backup integrity failure")
    if manifest.declared_capacity <= 0 or manifest.region_offset < 0 or (
        manifest.region_offset + manifest.region_length > manifest.declared_capacity
    ):
        raise ValueError("Invalid memory coverage")
    expected_complete = manifest.region_offset == 0 and len(image) == manifest.declared_capacity
    if manifest.complete_coverage != expected_complete:
        raise ValueError("Contradictory complete-coverage flag")
    if manifest.physical_origin_verified or manifest.restoration_verified:
        raise ValueError("Offline bundle cannot certify physical origin or restoration")
    return manifest
