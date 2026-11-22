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
        self.assertFalse(client.closed)
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
    def test_enabled_capability(self):
        serial=SimulatedSerial(lambda b:encode_frame(Frame(Op.CAPABILITIES,0,CAPS.replace(b"hs_can=disabled",b"hs_can=enabled"))))
        client=BinaryDiscoveryClient(serial)
        with self.assertRaises(ValueError):
            client.execute(Op.CAPABILITIES)
        self.assertTrue(client.closed)
    def test_write_short(self):
        class Short(SimulatedSerial):
            def write(self,data): return len(data)-1
        client=BinaryDiscoveryClient(Short())
        with self.assertRaises(IOError):
            client.execute(Op.PING)
        self.assertTrue(client.closed)

if __name__=="__main__":
    unittest.main()
