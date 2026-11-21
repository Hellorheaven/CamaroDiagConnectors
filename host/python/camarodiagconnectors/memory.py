"""Conservative offline EEPROM/NOR patch planner.

This tool NEVER writes to devices. Exact chip identity, electrical supply,
verified backups, bus access, driver, and readback are separate prerequisites.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Sequence


class Technology(str, Enum):
    I2C_EEPROM = "i2c_eeprom"
    SPI_EEPROM = "spi_eeprom"
    MICROWIRE_EEPROM = "microwire_eeprom"
    SPI_NOR = "spi_nor"


@dataclass(frozen=True, order=True)
class Region:
    start: int
    end: int  # exclusive

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise ValueError("Region must be nonempty and nonnegative")

    def overlaps(self, other: Region) -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class Geometry:
    name: str
    technology: Technology
    capacity: int
    page_size: int
    erase_size: int | None = None
    protected: tuple[Region, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.technology, Technology):
            raise ValueError("Unsupported memory technology")
        if (type(self.capacity) is not int or type(self.page_size) is not int
                or (self.erase_size is not None and type(self.erase_size) is not int)):
            raise ValueError("Memory dimensions must be integers, not booleans")
        if not self.name.strip() or self.capacity <= 0 or self.page_size <= 0:
            raise ValueError("Invalid chip name/capacity/page size")
        if self.page_size > self.capacity or self.capacity % self.page_size:
            raise ValueError("Chip capacity must consist of whole pages")
        if self.technology == Technology.SPI_NOR:
            if (self.erase_size is None or self.erase_size <= 0
                    or self.erase_size % self.page_size
                    or self.capacity % self.erase_size):
                raise ValueError("NOR erase sectors must be aligned")
        elif self.erase_size is not None:
            raise ValueError("Erase size only applies to NOR")
        for i, region in enumerate(self.protected):
            if not isinstance(region, Region):
                raise ValueError("Protected regions must be Region instances")
            if region.end > self.capacity:
                raise ValueError("Protected region is out of bounds")
            if any(region.overlaps(other) for other in self.protected[:i]):
                raise ValueError("Protected regions overlap")


@dataclass(frozen=True)
class Patch:
    offset: int
    data: bytes

    def __post_init__(self) -> None:
        if self.offset < 0 or not isinstance(self.data, bytes) or not self.data:
            raise ValueError("Patch needs a valid offset and nonempty bytes")

    @property
    def region(self) -> Region:
        return Region(self.offset, self.offset + len(self.data))


@dataclass(frozen=True)
class Operation:
    region: Region
    method: str
    changed_bytes: int
    original_sha256: str
    proposed_sha256: str


@dataclass(frozen=True)
class Plan:
    chip: str
    before_sha256: str
    after_sha256: str
    changed_bytes: int
    operations: tuple[Operation, ...]
    proposed_image: bytes
    write_authorized: bool = False


def plan_patches(geometry: Geometry, original: bytes, patches: Sequence[Patch]) -> Plan:
    """Plan affected pages/sectors, preserving neighboring bytes.

    NOR always uses read-modify-erase-rewrite for the entire affected erase
    sector even if some bit transitions may allow programming without erase.
    """
    if not isinstance(original, bytes) or len(original) != geometry.capacity:
        raise ValueError("Require a complete original offline image")
    if not patches:
        raise ValueError("At least one patch is required")
    ordered = sorted(patches, key=lambda patch: patch.offset)
    for i, patch in enumerate(ordered):
        if patch.region.end > geometry.capacity:
            raise ValueError("Patch exceeds chip bounds")
        if i and ordered[i - 1].region.overlaps(patch.region):
            raise ValueError("Patches overlap")
        if any(patch.region.overlaps(region) for region in geometry.protected):
            raise ValueError("Patch touches protected memory")
    new = bytearray(original)
    for patch in ordered:
        new[patch.offset:patch.region.end] = patch.data
    changed = [i for i, (old, current) in enumerate(zip(original, new)) if old != current]
    unit = geometry.erase_size if geometry.technology == Technology.SPI_NOR else geometry.page_size
    assert unit is not None
    touched = sorted({(i // unit) * unit for i in changed})
    operations: list[Operation] = []
    for base in touched:
        region = Region(base, base + unit)
        if any(region.overlaps(protected) for protected in geometry.protected):
            raise ValueError("Physical unit overlaps a protected neighbor")
        before = original[region.start:region.end]
        after = bytes(new[region.start:region.end])
        operations.append(Operation(
            region=region,
            method=("sector-read-erase-rewrite" if geometry.technology == Technology.SPI_NOR
                    else "page-update"),
            changed_bytes=sum(a != b for a, b in zip(before, after)),
            original_sha256=sha256(before).hexdigest(),
            proposed_sha256=sha256(after).hexdigest(),
        ))
    return Plan(
        chip=geometry.name,
        before_sha256=sha256(original).hexdigest(),
        after_sha256=sha256(new).hexdigest(),
        changed_bytes=len(changed),
        operations=tuple(operations),
        proposed_image=bytes(new),
    )
