"""Proposed binary framing for OFFLINE simulation ONLY.

The current ESP32-S3 firmware speaks ASCII discovery, not this frame format.
No write operation is defined. Not a functional J2534 protocol.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import struct
import zlib

MAGIC = b"CD"
VERSION = 1
MAX_PAYLOAD = 4096
_HEADER = struct.Struct("<2sBBHH")
_TRAILER = struct.Struct("<I")


class Op(IntEnum):
    PING = 1
    CAPABILITIES = 2
    STATUS = 3


@dataclass(frozen=True)
class Frame:
    op: Op
    sequence: int
    payload: bytes


def encode_frame(frame: Frame) -> bytes:
    if not isinstance(frame.op, Op) or not 0 <= frame.sequence <= 0xFFFF:
        raise ValueError("Invalid opcode or sequence")
    if not isinstance(frame.payload, bytes) or len(frame.payload) > MAX_PAYLOAD:
        raise ValueError("Oversize or non-byte payload")
    blob = _HEADER.pack(MAGIC, VERSION, int(frame.op), frame.sequence, len(frame.payload)) + frame.payload
    return blob + _TRAILER.pack(zlib.crc32(blob) & 0xFFFFFFFF)


def decode_frame(data: bytes) -> Frame:
    if len(data) < _HEADER.size + _TRAILER.size:
        raise ValueError("Truncated frame")
    magic, version, command, sequence, length = _HEADER.unpack_from(data)
    if magic != MAGIC or version != VERSION or length > MAX_PAYLOAD:
        raise ValueError("Invalid frame header")
    if len(data) != _HEADER.size + length + _TRAILER.size:
        raise ValueError("Frame length mismatch")
    expected_crc = _TRAILER.unpack_from(data, _HEADER.size + length)[0]
    if zlib.crc32(data[:-_TRAILER.size]) & 0xFFFFFFFF != expected_crc:
        raise ValueError("Frame CRC mismatch")
    try:
        op = Op(command)
    except ValueError as exc:
        raise ValueError("Unsupported operation") from exc
    return Frame(op, sequence, data[_HEADER.size:_HEADER.size + length])
