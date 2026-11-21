"""Strict, fail-closed read-only USB discovery protocol."""

from dataclasses import dataclass
from typing import Protocol

_ALLOWED_COMMANDS = frozenset({"PING", "CAPS", "STATUS"})


class SerialLike(Protocol):
    def write(self, data: bytes) -> int: ...
    def readline(self) -> bytes: ...


@dataclass(frozen=True)
class Capabilities:
    hs_can: bool
    sw_can: bool
    eeprom_read: bool
    eeprom_write: bool
    ecu_flash: bool
    j2534: bool


def parse_caps(response: str) -> Capabilities:
    if response != response.strip() or "  " in response or "\t" in response:
        raise ValueError("Noncanonical response whitespace")
    parts = response.split(" ")
    expected = {"hs_can", "sw_can", "eeprom_read", "eeprom_write", "ecu_flash", "j2534"}
    if not parts or parts[0] != "CAPS":
        raise ValueError("Invalid capability response")
    fields: dict[str, str] = {}
    for token in parts[1:]:
        key, sep, val = token.partition("=")
        if not sep or key not in expected or key in fields or val not in {"enabled", "disabled"}:
            raise ValueError("Malformed capability field")
        fields[key] = val
    if fields.keys() != expected:
        raise ValueError("Missing capability fields")
    return Capabilities(**{key: fields[key] == "enabled" for key in expected})


@dataclass(frozen=True)
class DeviceStatus:
    mode: str
    write_enabled: bool


def parse_status(response: str) -> DeviceStatus:
    """Fail closed on unsupported firmware modes or enabled write access."""
    if response != response.strip() or "  " in response or "\t" in response:
        raise ValueError("Noncanonical response whitespace")
    parts = response.split(" ")
    if not parts or parts[0] != "STATUS":
        raise ValueError("Invalid status response")
    fields: dict[str, str] = {}
    for token in parts[1:]:
        key, sep, value = token.partition("=")
        if not sep or key not in {"mode", "write"} or key in fields:
            raise ValueError("Malformed status field")
        fields[key] = value
    if fields != {"mode": "prototype", "write": "disabled"}:
        raise ValueError("Device is not in the expected read-only prototype mode")
    return DeviceStatus(mode="prototype", write_enabled=False)


class DiscoveryClient:
    """Only PING, CAPS and STATUS. No memory or CAN access."""

    def __init__(self, transport: SerialLike) -> None:
        self._transport = transport

    def execute(self, command: str) -> str:
        if command not in _ALLOWED_COMMANDS:
            raise ValueError("Command forbidden in read-only prototype")
        outgoing = (command + "\n").encode("ascii")
        if self._transport.write(outgoing) != len(outgoing):
            raise IOError("Short command write")
        reply = self._transport.readline()
        if not reply or len(reply) > 256:
            raise IOError("Missing or oversize reply")
        # A reply must be one complete line; reject partial frames and injected replies.
        if not reply.endswith(b"\n") or b"\n" in reply[:-1] or b"\r" in reply[:-2]:
            raise IOError("Malformed serial reply framing")
        # Permit printable ASCII and only the optional terminal CRLF delimiter.
        payload = reply[:-2] if reply.endswith(b"\r\n") else reply[:-1]
        if any(byte < 0x20 or byte > 0x7e for byte in payload):
            raise IOError("Control or non-ASCII byte in serial reply")
        try:
            response = payload.decode("ascii")
        except UnicodeDecodeError as exc:
            raise IOError("Non ASCII reply") from exc
        if response.startswith("ERR "):
            raise IOError(response)
        prefix = {"PING": "PONG ", "CAPS": "CAPS ", "STATUS": "STATUS "}[command]
        if not response.startswith(prefix):
            raise IOError("Unexpected device reply")
        if command == "PING" and response != "PONG CamaroDiagConnectors 0.1.0":
            raise IOError("Unsupported device identity or firmware version")
        return response

    def capabilities(self) -> Capabilities:
        return parse_caps(self.execute("CAPS"))

    def status(self) -> DeviceStatus:
        return parse_status(self.execute("STATUS"))

    def verify_read_only(self) -> None:
        """Reject any device advertising CAN, memory, flash, J2534 or writes."""
        self.execute("PING")
        if any(vars(self.capabilities()).values()):
            raise ValueError("Unexpected enabled device capability")
        self.status()
