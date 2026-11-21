"""Read-only USB serial discovery CLI for the ESP32-S3 prototype."""

import argparse

from .protocol import DiscoveryClient


def main() -> None:
    parser = argparse.ArgumentParser(description="CamaroDiagConnectors USB discovery (no ECU writes)")
    parser.add_argument("--port", required=True, help="Serial port, e.g. COM5")
    parser.add_argument("command", choices=["ping", "caps", "status", "verify"])
    args = parser.parse_args()
    try:
        import serial  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SystemExit("Install pyserial: python -m pip install pyserial") from exc
    with serial.Serial(args.port, baudrate=115200, timeout=2, write_timeout=2) as port:
        client = DiscoveryClient(port)
        if args.command == "verify":
            client.verify_read_only()
            print("Verified prototype mode: all capabilities disabled")
        else:
            print(client.execute(args.command.upper()))


if __name__ == "__main__":
    main()
