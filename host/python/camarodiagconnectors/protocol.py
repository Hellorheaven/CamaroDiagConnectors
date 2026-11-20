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
    parts = response.strip().split()
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
    parts = response.strip().split()
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
        try:
            response = reply.decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise IOError("Non ASCII reply") from exc
        if response.startswith("ERR "):
            raise IOError(response)
        prefix = {"PING": "PONG ", "CAPS": "CAPS ", "STATUS": "STATUS "}[command]
        if not response.startswith(prefix):
            raise IOError("Unexpected device reply")
        return response

    def capabilities(self) -> Capabilities:
        return parse_caps(self.execute("CAPS"))

    def status(self) -> DeviceStatus:
        return parse_status(self.execute("STATUS"))

    def verify_read_only(self) -> None:
        """Reject any device advertising CAN, memory, flash, J2534 or writes."""
        if any(vars(self.capabilities()).values()):
            raise ValueError("Unexpected enabled device capability")
        self.status()
