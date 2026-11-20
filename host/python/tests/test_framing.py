import unittest

from camarodiagconnectors.framing import Frame, Op, encode_frame, decode_frame, MAX_PAYLOAD


class FramingTests(unittest.TestCase):
    def test_roundtrip(self):
        original = Frame(Op.STATUS, 65535, b"hello\x00world")
        self.assertEqual(decode_frame(encode_frame(original)), original)

    def test_no_write_opcodes_defined(self):
        self.assertEqual(set(Op), {Op.PING, Op.CAPABILITIES, Op.STATUS})

    def test_corrupt_crc(self):
        raw = bytearray(encode_frame(Frame(Op.PING, 1, b"data")))
        raw[-5] ^= 1
        with self.assertRaises(ValueError):
            decode_frame(bytes(raw))

    def test_invalid_magic(self):
        raw = bytearray(encode_frame(Frame(Op.PING, 1, b"")))
        raw[0] = 0
        with self.assertRaises(ValueError):
            decode_frame(bytes(raw))

    def test_truncated(self):
        raw = encode_frame(Frame(Op.PING, 1, b""))
        with self.assertRaises(ValueError):
            decode_frame(raw[:-1])

    def test_extra_data(self):
        raw = encode_frame(Frame(Op.PING, 1, b""))
        with self.assertRaises(ValueError):
            decode_frame(raw + b"x")

    def test_oversize(self):
        with self.assertRaises(ValueError):
            encode_frame(Frame(Op.PING, 1, b"x" * (MAX_PAYLOAD + 1)))

    def test_sequence_out_of_range(self):
        with self.assertRaises(ValueError):
            encode_frame(Frame(Op.PING, 65536, b""))

    def test_unknown_opcode_rejected(self):
        with self.assertRaises(ValueError):
            encode_frame(Frame(33, 1, b""))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
