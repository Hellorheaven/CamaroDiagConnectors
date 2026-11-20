import tempfile
import unittest
from pathlib import Path

from camarodiagconnectors.offline_cli import run, _patch, _region


class OfflineCliTests(unittest.TestCase):
    def test_offline_backup_and_verify(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            origin = root / "original.bin"
            origin.write_bytes(b"ABCD")
            result = run(["backup", "--target", "chip", "--capacity", "4", "--input",
                          str(origin), "--output-prefix", str(root / "dump")])
            self.assertEqual(result["action"], "backup")
            self.assertFalse(result["physical_read_verified"])
            verified = run(["verify", "--prefix", str(root / "dump")])
            self.assertTrue(verified["manifest"]["complete_coverage"])

    def test_second_read_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "o.bin"
            independent = root / "i.bin"
            original.write_bytes(b"ABCD")
            independent.write_bytes(b"ABCE")
            with self.assertRaises(ValueError):
                run(["backup", "--target", "chip", "--capacity", "4",
                     "--input", str(original), "--second-read", str(independent),
                     "--output-prefix", str(root / "out")])

    def test_offline_patch_preview_preserves_original(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "original.bin"
            source.write_bytes(b"\xff" * 64)
            result = run(["plan", "--target", "test_nor", "--technology", "spi_nor",
                          "--page-size", "8", "--erase-size", "32", "--input", str(source),
                          "--patch", "2:00", "--proposed-output", str(root / "new.bin")])
            self.assertEqual(result["operations"][0]["end_exclusive"], 32)
            self.assertEqual(result["changed_bytes"], 1)
            self.assertFalse(result["write_authorized"])
            self.assertEqual((root / "new.bin").read_bytes(), b"\xff\xff\x00" + b"\xff" * 61)
            self.assertEqual(source.read_bytes(), b"\xff" * 64)

    def test_cannot_overwrite_existing_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "o.bin"
            candidate = root / "candidate.bin"
            source.write_bytes(b"\xff" * 32)
            candidate.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                run(["plan", "--target", "chip", "--technology", "i2c_eeprom",
                     "--page-size", "8", "--input", str(source), "--patch", "0:00",
                     "--proposed-output", str(candidate)])
            self.assertEqual(candidate.read_bytes(), b"keep")

    def test_protected_sector_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "o.bin"
            source.write_bytes(b"\xff" * 64)
            with self.assertRaises(ValueError):
                run(["plan", "--target", "chip", "--technology", "spi_nor",
                     "--page-size", "8", "--erase-size", "32", "--input", str(source),
                     "--patch", "0:00", "--protected", "0x10:0x11"])

    def test_patch_and_region_parser(self):
        self.assertEqual(_patch("0x10:aa55").offset, 16)
        self.assertEqual(_patch("16:aa 55").data, b"\xaa\x55")
        self.assertEqual((_region("0x10:20").start, _region("0x10:20").end), (16, 20))


if __name__ == "__main__":
    unittest.main()
