"""Read-only USB serial discovery CLI for the ESP32-S3 prototype."""

import argparse

from .protocol import DiscoveryClient
from .binary_discovery import BinaryDiscoveryClient


def main() -> None:
    parser = argparse.ArgumentParser(description="CamaroDiagConnectors USB discovery (no ECU writes)")
    parser.add_argument("--port", required=True, help="Serial port, e.g. COM5")
    parser.add_argument("command", choices=["ping", "caps", "status", "verify"])
    parser.add_argument("--binary", action="store_true", help="Explicit binary prototype firmware mode; verify only")
    args = parser.parse_args()
    if args.binary and args.command != "verify":
        parser.error("Binary prototype requires verify; reset the board before each new session")
    try:
        import serial  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SystemExit("Install pyserial: python -m pip install pyserial") from exc
    with serial.Serial(args.port, baudrate=115200, timeout=2, write_timeout=2) as port:
        if args.binary:
            for response in BinaryDiscoveryClient(port).verify_read_only():
                print(response)
            print("Binary prototype verified (not cryptographically authenticated)")
            return
        client = DiscoveryClient(port)
        if args.command == "verify":
            client.verify_read_only()
            print("Verified prototype mode: all capabilities disabled")
        else:
            print(client.execute(args.command.upper()))


if __name__ == "__main__":
    main()
