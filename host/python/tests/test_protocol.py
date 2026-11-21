import unittest

from camarodiagconnectors.protocol import Capabilities, DiscoveryClient, parse_caps, parse_status, DeviceStatus


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

    def test_ping_rejects_unknown_identity_or_version(self):
        for reply in (
            b"PONG OtherDevice 0.1.0\n",
            b"PONG CamaroDiagConnectors 0.2.0\n",
            b"PONG CamaroDiagConnectors 0.1.0 EXTRA\n",
            b"PONG CamaroDiagConnectors 0.1.0  \n",
        ):
            with self.subTest(reply=reply), self.assertRaises(IOError):
                DiscoveryClient(MockSerial(reply)).execute("PING")

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

    def test_reject_noncanonical_response_whitespace(self):
        valid_caps = "CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled"
        valid_status = "STATUS mode=prototype write=disabled"
        for parser, valid in ((parse_caps, valid_caps), (parse_status, valid_status)):
            for invalid in (" " + valid, valid + " ", valid.replace(" ", "  ", 1), valid.replace(" ", "\t", 1)):
                with self.subTest(parser=parser.__name__, invalid=invalid), self.assertRaises(ValueError):
                    parser(invalid)

    def test_wrong_reply_prefix(self):
        with self.assertRaises(IOError):
            DiscoveryClient(MockSerial(b"CAPS invalid\n")).execute("PING")

    def test_error_reply(self):
        with self.assertRaises(IOError):
            DiscoveryClient(MockSerial(b"ERR UNSUPPORTED\n")).execute("PING")

    def test_invalid_encoding(self):
        with self.assertRaises(IOError):
            DiscoveryClient(MockSerial(b"\xff\xfe\n")).execute("PING")

    def test_reject_partial_or_injected_reply(self):
        for reply in (
            b"PONG CamaroDiagConnectors 0.1.0",
            b"PONG CamaroDiagConnectors 0.1.0\nSTATUS mode=prototype write=disabled\n",
            b"PONG CamaroDiagConnectors 0.1.0\rEXTRA\n",
            b"PONG CamaroDiagConnectors\x00 0.1.0\n",
        ):
            with self.subTest(reply=reply), self.assertRaises(IOError):
                DiscoveryClient(MockSerial(reply)).execute("PING")

    def test_reject_ascii_control_bytes_and_del(self):
        for reply in (
            b"PONG CamaroDiagConnectors\t0.1.0\n",
            b"PONG CamaroDiagConnectors\x1b0.1.0\n",
            b"PONG CamaroDiagConnectors\x7f0.1.0\n",
            b"PONG CamaroDiagConnectors\x00\n",
        ):
            with self.subTest(reply=reply), self.assertRaises(IOError):
                DiscoveryClient(MockSerial(reply)).execute("PING")

    def test_empty_response(self):
        with self.assertRaises(IOError):
            DiscoveryClient(MockSerial(b"")).execute("PING")

    def test_status_read_only(self):
        self.assertEqual(parse_status("STATUS mode=prototype write=disabled"), DeviceStatus("prototype", False))

    def test_status_rejects_unsafe_or_malformed(self):
        for response in (
            "STATUS mode=prototype write=enabled",
            "STATUS mode=vehicle write=disabled",
            "STATUS mode=prototype write=disabled extra=1",
            "STATUS mode=prototype mode=prototype write=disabled",
            "STATUS mode=prototype",
            "STATUS write=disabled",
            "CAPS mode=prototype write=disabled",
        ):
            with self.subTest(response=response), self.assertRaises(ValueError):
                parse_status(response)

    def test_verify_read_only_accepts_disabled_device(self):
        class MockSequence:
            def __init__(self):
                self.replies = iter((
                    b"PONG CamaroDiagConnectors 0.1.0\n",
                    b"CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled\n",
                    b"STATUS mode=prototype write=disabled\n",
                ))
                self.commands = []
            def write(self, data):
                self.commands.append(data)
                return len(data)
            def readline(self):
                return next(self.replies)
        serial = MockSequence()
        DiscoveryClient(serial).verify_read_only()
        self.assertEqual(serial.commands, [b"PING\n", b"CAPS\n", b"STATUS\n"])

    def test_verify_read_only_rejects_enabled_capability_before_status(self):
        class Sequence:
            def __init__(self):
                self.replies = iter((
                    b"PONG CamaroDiagConnectors 0.1.0\n",
                    b"CAPS hs_can=enabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled\n",
                ))
                self.commands = []
            def write(self, data):
                self.commands.append(data)
                return len(data)
            def readline(self):
                return next(self.replies)
        transport = Sequence()
        with self.assertRaises(ValueError):
            DiscoveryClient(transport).verify_read_only()
        self.assertEqual(transport.commands, [b"PING\n", b"CAPS\n"])

    def test_verify_read_only_rejects_unknown_device_before_capabilities(self):
        transport = MockSerial(b"PONG UnknownDevice 0.1.0\n")
        with self.assertRaises(IOError):
            DiscoveryClient(transport).verify_read_only()
        self.assertEqual(bytes(transport.outgoing), b"PING\n")


    def test_short_serial_write_fails_before_read(self):
        class ShortWrite:
            def __init__(self):
                self.read_called = False
            def write(self, data):
                return len(data) - 1
            def readline(self):
                self.read_called = True
                return b"PONG CamaroDiagConnectors 0.1.0\n"
        transport = ShortWrite()
        with self.assertRaises(IOError):
            DiscoveryClient(transport).execute("PING")
        self.assertFalse(transport.read_called)

    def test_reject_oversized_serial_reply(self):
        transport = MockSerial(b"PONG " + b"A" * 252 + b"\n")
        with self.assertRaises(IOError):
            DiscoveryClient(transport).execute("PING")

    def test_verify_read_only_rejects_unsafe_status(self):
        class Sequence:
            def __init__(self):
                self.replies = iter((
                    b"PONG CamaroDiagConnectors 0.1.0\n",
                    b"CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled\n",
                    b"STATUS mode=prototype write=enabled\n",
                ))
                self.commands = []
            def write(self, data):
                self.commands.append(data)
                return len(data)
            def readline(self):
                return next(self.replies)
        transport = Sequence()
        with self.assertRaises(ValueError):
            DiscoveryClient(transport).verify_read_only()
        self.assertEqual(transport.commands, [b"PING\n", b"CAPS\n", b"STATUS\n"])

if __name__ == "__main__":
    unittest.main()
