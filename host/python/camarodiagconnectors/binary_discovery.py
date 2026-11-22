"""Binary USB discovery for isolated development firmware only.

CRC and sequencing detect accidental errors; neither authenticates a device.
No vehicle, memory, or programming operation is exposed.
"""
from .framing import Frame, Op, encode_frame, decode_frame, MAX_PAYLOAD
from .protocol import parse_caps, parse_status

class BinaryDiscoveryClient:
    def __init__(self, transport):
        self._transport = transport
        self._next = 0
        self._closed = False

    @property
    def closed(self):
        return self._closed

    def _read_exact(self, count):
        data = bytearray()
        while len(data) < count:
            chunk = self._transport.read(count - len(data))
            if not chunk or len(chunk) > count - len(data):
                raise IOError("Incomplete or overlong binary reply")
            data.extend(chunk)
        return bytes(data)

    def execute(self, op):
        if self._closed:
            raise IOError("Discovery session closed; reset device before reconnecting")
        try:
            if not isinstance(op, Op):
                raise ValueError("Unsupported discovery operation")
            wire = encode_frame(Frame(op, self._next, b""))
            if self._transport.write(wire) != len(wire):
                raise IOError("Short binary request write")
            header = self._read_exact(8)
            if header[:3] != b"CD\x01":
                raise IOError("Unsupported binary header")
            size = int.from_bytes(header[6:8], "little")
            # Public discovery replies are small and never empty.
            if not 0 < size <= min(MAX_PAYLOAD, 244):
                raise IOError("Unexpected discovery reply length")
            frame = decode_frame(header + self._read_exact(size + 4))
            if frame.op != op or frame.sequence != self._next:
                raise IOError("Unexpected reply correlation")
            text = frame.payload.decode("ascii")
            if not all(32 <= ord(c) <= 126 for c in text):
                raise ValueError("Non-printable discovery payload")
            if op == Op.PING:
                if text != "PONG CamaroDiagConnectors 0.1.0":
                    raise ValueError("Unexpected prototype identity")
            elif op == Op.CAPABILITIES:
                if any(vars(parse_caps(text)).values()):
                    raise ValueError("Unsafe capability claim")
            elif op == Op.STATUS:
                parse_status(text)
            if self._next == 65535:
                self._closed = True
            else:
                self._next += 1
            return text
        except BaseException:
            self._closed = True
            raise

    def verify_read_only(self):
        return tuple(self.execute(op) for op in (Op.PING, Op.CAPABILITIES, Op.STATUS))
