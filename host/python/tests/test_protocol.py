import unittest

from camarodiagconnectors.protocol import Capabilities, DiscoveryClient, parse_caps


class MockSerial:
    def __init__(self, reply: bytes):
        self.reply = reply
        self.outgoing = bytearray()

    def write(self, data: bytes) -> int:
        self.outgoing.extend(data)
        return len(data)

    def readline(self) -> bytes:
        return self.reply


class DiscoveryTests(unittest.TestCase):
    def test_ping(self):
        transport = MockSerial(b"PONG CamaroDiagConnectors 0.1.0\r\n")
        self.assertEqual(DiscoveryClient(transport).execute("PING"), "PONG CamaroDiagConnectors 0.1.0")
        self.assertEqual(bytes(transport.outgoing), b"PING\n")

    def test_caps_are_all_disabled(self):
        transport = MockSerial(b"CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled\n")
        self.assertEqual(DiscoveryClient(transport).capabilities(), Capabilities(False, False, False, False, False, False))

    def test_unrecognized_command_rejected_without_io(self):
        transport = MockSerial(b"ERR UNSUPPORTED\n")
        with self.assertRaises(ValueError):
            DiscoveryClient(transport).execute("EEPROM_WRITE")
        self.assertEqual(bytes(transport.outgoing), b"")

    def test_reject_incomplete_capabilities(self):
        with self.assertRaises(ValueError):
            parse_caps("CAPS hs_can=enabled")

    def test_reject_unknown_capabilities(self):
        with self.assertRaises(ValueError):
            parse_caps("CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled secret=enabled")

    def test_reject_malformed_capabilities(self):
        with self.assertRaises(ValueError):
            parse_caps("CAPS hs_can=maybe sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled")

    def test_wrong_reply_prefix(self):
        with self.assertRaises(IOError):
            DiscoveryClient(MockSerial(b"CAPS invalid\n")).execute("PING")

    def test_error_reply(self):
        with self.assertRaises(IOError):
            DiscoveryClient(MockSerial(b"ERR UNSUPPORTED\n")).execute("PING")

    def test_invalid_encoding(self):
        with self.assertRaises(IOError):
            DiscoveryClient(MockSerial(b"\xff\xfe\n")).execute("PING")

    def test_empty_response(self):
        with self.assertRaises(IOError):
            DiscoveryClient(MockSerial(b"")).execute("PING")


if __name__ == "__main__":
    unittest.main()
