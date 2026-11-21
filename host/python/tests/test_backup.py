import json
import tempfile
import unittest
from pathlib import Path

from camarodiagconnectors.backup import backup_manifest, write_bundle, verify_bundle


class BackupTests(unittest.TestCase):
    def test_complete_with_second_read(self):
        m = backup_manifest("test-chip", 4, 0, b"abcd", b"abcd")
        self.assertTrue(m.complete_coverage)
        self.assertTrue(m.secondary_read_matched)
        self.assertFalse(m.physical_origin_verified)
        self.assertFalse(m.restoration_verified)

    def test_partial(self):
        m = backup_manifest("test-chip", 16, 4, b"1234")
        self.assertFalse(m.complete_coverage)
        self.assertIsNone(m.secondary_read_matched)

    def test_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            backup_manifest("test-chip", 4, 0, b"1234", b"4321")

    def test_out_of_range_rejected(self):
        with self.assertRaises(ValueError):
            backup_manifest("test-chip", 4, 3, b"1234")

    def test_save_verify_and_never_overwrite(self):
        m = backup_manifest("chip", 8, 0, b"abcdefgh", b"abcdefgh")
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            write_bundle(prefix, b"abcdefgh", m)
            self.assertEqual(verify_bundle(prefix), m)
            with self.assertRaises(FileExistsError):
                write_bundle(prefix, b"abcdefgh", m)

    def test_corruption_detected(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            write_bundle(prefix, b"abcd", m)
            prefix.with_suffix(".bin").write_bytes(b"abce")
            with self.assertRaises(ValueError):
                verify_bundle(prefix)

    def test_incorrect_manifest_rejected_before_writing(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            with self.assertRaises(ValueError):
                write_bundle(prefix, b"abce", m)
            self.assertFalse(prefix.with_suffix(".bin").exists())

    def test_modified_complete_flag_rejected(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            write_bundle(prefix, b"abcd", m)
            path = prefix.with_suffix(".json")
            data = json.loads(path.read_text())
            data["complete_coverage"] = False
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                verify_bundle(prefix)

    def test_malformed_manifest_types_rejected(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            write_bundle(prefix, b"abcd", m)
            path = prefix.with_suffix(".json")
            original = json.loads(path.read_text())
            for field, value in (
                ("declared_capacity", True),
                ("region_offset", "0"),
                ("complete_coverage", 1),
                ("target", 7),
                ("secondary_read_matched", False),
                ("physical_origin_verified", "false"),
            ):
                with self.subTest(field=field):
                    data = dict(original)
                    data[field] = value
                    path.write_text(json.dumps(data))
                    with self.assertRaises(ValueError):
                        verify_bundle(prefix)

    def test_claim_of_physical_origin_rejected(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            write_bundle(prefix, b"abcd", m)
            path = prefix.with_suffix(".json")
            data = json.loads(path.read_text())
            data["physical_origin_verified"] = True
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                verify_bundle(prefix)


if __name__ == "__main__":
    unittest.main()
