import unittest
from camarodiagconnectors.binary_discovery import BinaryDiscoveryClient
from camarodiagconnectors.framing import Frame, Op, encode_frame, decode_frame

CAPS=b"CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled"
REPLIES={Op.PING:b"PONG CamaroDiagConnectors 0.1.0",Op.CAPABILITIES:CAPS,Op.STATUS:b"STATUS mode=prototype write=disabled"}

class SimulatedSerial:
    def __init__(self, transform=lambda wire:wire):
        self.reply=b""
        self.sent=[]
        self.transform=transform
    def write(self, data):
        f=decode_frame(data)
        assert f.payload==b""
        self.sent.append(f)
        self.reply=self.transform(encode_frame(Frame(f.op,f.sequence,REPLIES[f.op])))
        return len(data)
    def read(self, count):
        length=min(count,3)
        chunk,self.reply=self.reply[:length],self.reply[length:]
        return chunk

class BinaryDiscoveryTests(unittest.TestCase):
    def test_fragmented_roundtrip(self):
        serial=SimulatedSerial()
        client=BinaryDiscoveryClient(serial)
        self.assertEqual(client.verify_read_only(),tuple(v.decode() for v in REPLIES.values()))
        self.assertEqual([f.sequence for f in serial.sent],[0,1,2])
        self.assertTrue(client.closed)
        with self.assertRaises(IOError):
            client.execute(Op.PING)
        self.assertEqual(len(serial.sent), 3)
    def assert_fails_closed(self, transform):
        serial=SimulatedSerial(transform)
        client=BinaryDiscoveryClient(serial)
        with self.assertRaises((ValueError,IOError)):
            client.execute(Op.PING)
        self.assertTrue(client.closed)
        with self.assertRaises(IOError):
            client.execute(Op.PING)
        self.assertEqual(len(serial.sent),1)
    def test_corrupt_crc(self):
        self.assert_fails_closed(lambda b:b[:-1]+bytes([b[-1]^1]))
    def test_truncated(self):
        self.assert_fails_closed(lambda b:b[:-3])
    def test_wrong_sequence(self):
        self.assert_fails_closed(lambda b:encode_frame(Frame(Op.PING,1,REPLIES[Op.PING])))
    def test_wrong_op(self):
        self.assert_fails_closed(lambda b:encode_frame(Frame(Op.STATUS,0,REPLIES[Op.STATUS])))
    def test_wrong_identity(self):
        self.assert_fails_closed(lambda b:encode_frame(Frame(Op.PING,0,b"PONG counterfeit")))
    def test_empty_reply(self):
        self.assert_fails_closed(lambda b:b"")
    def test_enabled_or_reordered_capability(self):
        for caps in (CAPS.replace(b"hs_can=disabled",b"hs_can=enabled"),
                     CAPS.replace(b"hs_can=disabled sw_can=disabled",b"sw_can=disabled hs_can=disabled")):
            def transform(wire):
                f=decode_frame(wire)
                return encode_frame(Frame(f.op,f.sequence,caps)) if f.op==Op.CAPABILITIES else wire
            serial=SimulatedSerial(transform)
            client=BinaryDiscoveryClient(serial)
            client.execute(Op.PING)
            with self.assertRaises(ValueError):
                client.execute(Op.CAPABILITIES)
            self.assertTrue(client.closed)
            self.assertEqual(len(serial.sent),2)
    def test_wrong_order_never_transmits(self):
        serial=SimulatedSerial()
        client=BinaryDiscoveryClient(serial)
        with self.assertRaises(ValueError):
            client.execute(Op.STATUS)
        self.assertTrue(client.closed)
        self.assertEqual(serial.sent,[])
    def test_slow_drip_cannot_reset_response_deadline(self):
        serial = SimulatedSerial()
        ticks = iter(i * 0.5 for i in range(100))
        client = BinaryDiscoveryClient(serial, clock=lambda: next(ticks))
        with self.assertRaises(TimeoutError):
            client.verify_read_only()
        self.assertTrue(client.closed)
        self.assertEqual(len(serial.sent), 1)
        with self.assertRaises(IOError):
            client.execute(Op.PING)

    def test_write_short(self):
        class Short(SimulatedSerial):
            def write(self,data): return len(data)-1
        client=BinaryDiscoveryClient(Short())
        with self.assertRaises(IOError):
            client.execute(Op.PING)
        self.assertTrue(client.closed)

if __name__=="__main__":
    unittest.main()
