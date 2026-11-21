"""Immutable offline backup bundles and integrity metadata.

Nothing here proves the source came from an actual memory chip or ECU.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import hmac
import os
import stat
import re
from pathlib import Path


def _open_regular_nofollow(path: Path):
    """Open a regular file without following a final-component symlink."""
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("Backup components must be regular files")
        return os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise


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
    if (type(manifest.schema) is not int or type(manifest.declared_capacity) is not int
        or type(manifest.region_offset) is not int or type(manifest.region_length) is not int
        or type(manifest.complete_coverage) is not bool
        or type(manifest.physical_origin_verified) is not bool
        or type(manifest.restoration_verified) is not bool
        or type(manifest.target) is not str or type(manifest.source) is not str
        or type(manifest.image_sha256) is not str):
        raise ValueError("Invalid backup metadata types")
    if type(manifest.secondary_read_matched) not in (bool, type(None)):
        raise ValueError("Invalid secondary read status")
    expected = backup_manifest(
        manifest.target, manifest.declared_capacity, manifest.region_offset, image,
        image if manifest.secondary_read_matched is True else None,
        source=manifest.source,
    )
    if manifest != expected:
        raise ValueError("Untrusted or inconsistent backup metadata")
    binary = prefix.with_suffix(".bin")
    metadata = prefix.with_suffix(".json")
    # Path.exists() follows symlinks and misses dangling links; reject those too.
    if os.path.lexists(binary) or os.path.lexists(metadata):
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


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate manifest field: {key}")
        result[key] = value
    return result


def verify_bundle(prefix: Path) -> Manifest:
    metadata_path = prefix.with_suffix(".json")
    binary_path = prefix.with_suffix(".bin")
    # Offline bundles must not follow links into arbitrary host files or devices.
    for path in (metadata_path, binary_path):
        mode = path.lstat().st_mode
        if not stat.S_ISREG(mode):
            raise ValueError("Backup components must be regular files")
    with _open_regular_nofollow(metadata_path) as stream:
        raw = stream.read(64 * 1024 + 1)
    if len(raw) > 64 * 1024:
        raise ValueError("Manifest exceeds 64 KiB")
    metadata = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
    )
    if type(metadata) is not dict:
        raise ValueError("Manifest must be a JSON object")
    try:
        manifest = Manifest(**metadata)
    except TypeError as exc:
        raise ValueError("Invalid manifest fields") from exc
    if (type(manifest.schema) is not int or type(manifest.declared_capacity) is not int
        or type(manifest.region_offset) is not int or type(manifest.region_length) is not int
        or type(manifest.complete_coverage) is not bool
        or type(manifest.physical_origin_verified) is not bool
        or type(manifest.restoration_verified) is not bool
        or (manifest.secondary_read_matched is not None and manifest.secondary_read_matched is not True)
        or type(manifest.target) is not str or type(manifest.source) is not str
        or type(manifest.image_sha256) is not str):
        raise ValueError("Invalid backup metadata types or unsupported readback claim")
    if not re.fullmatch(r"[0-9a-f]{64}", manifest.image_sha256):
        raise ValueError("Invalid SHA-256 digest format")
    if manifest.schema != 1 or manifest.region_length <= 0:
        raise ValueError("Invalid schema or image length")
    if not manifest.target.strip() or not manifest.source.strip():
        raise ValueError("Missing backup metadata")
    if manifest.declared_capacity <= 0 or manifest.region_offset < 0 or (
        manifest.region_offset + manifest.region_length > manifest.declared_capacity
    ):
        raise ValueError("Invalid memory coverage")
    expected_complete = manifest.region_offset == 0 and manifest.region_length == manifest.declared_capacity
    if manifest.complete_coverage != expected_complete:
        raise ValueError("Contradictory complete-coverage flag")
    if manifest.physical_origin_verified or manifest.restoration_verified:
        raise ValueError("Offline bundle cannot certify physical origin or restoration")
    digest = sha256()
    with _open_regular_nofollow(binary_path) as stream:
        remaining = manifest.region_length
        if os.fstat(stream.fileno()).st_size != remaining:
            raise ValueError("Image size disagrees with manifest")
        while remaining:
            chunk = stream.read(min(remaining, 1024 * 1024))
            if not chunk:
                raise ValueError("Image size disagrees with manifest")
            digest.update(chunk)
            remaining -= len(chunk)
        if stream.read(1):
            raise ValueError("Image size disagrees with manifest")
    if not hmac.compare_digest(digest.hexdigest(), manifest.image_sha256):
        raise ValueError("Backup integrity failure")
    return manifest
