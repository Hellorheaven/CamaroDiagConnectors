import json
import os
from dataclasses import replace
import tempfile
import unittest
from pathlib import Path

from camarodiagconnectors.backup import backup_manifest, write_bundle, verify_bundle


class BackupTests(unittest.TestCase):
    def test_opened_descriptor_must_be_regular(self):
        from camarodiagconnectors.backup import _open_regular_nofollow
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                _open_regular_nofollow(Path(directory))

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "O_NOFOLLOW unavailable")
    def test_open_rejects_symlink_even_if_path_was_prechecked(self):
        from camarodiagconnectors.backup import _open_regular_nofollow
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.bin"
            link = root / "alias.bin"
            original.write_bytes(b"test")
            link.symlink_to(original)
            with self.assertRaises(OSError):
                _open_regular_nofollow(link)

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

    def test_dangling_symlink_components_rejected_without_side_effects(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prefix = root / "backup"
            for suffix in (".bin", ".json"):
                with self.subTest(suffix=suffix):
                    link = prefix.with_suffix(suffix)
                    link.symlink_to(root / "missing-target")
                    with self.assertRaises(FileExistsError):
                        write_bundle(prefix, b"abcd", m)
                    self.assertTrue(link.is_symlink())
                    self.assertFalse(prefix.with_suffix(
                        ".json" if suffix == ".bin" else ".bin"
                    ).exists())
                    link.unlink()

    def test_forged_export_manifest_rejected_without_creating_files(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        variants = (
            replace(m, physical_origin_verified=True),
            replace(m, restoration_verified=True),
            replace(m, complete_coverage=False),
            replace(m, secondary_read_matched=False),
            replace(m, secondary_read_matched=1),
            replace(m, schema=2),
            replace(m, declared_capacity=True),
        )
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            for forged in variants:
                with self.subTest(manifest=forged):
                    with self.assertRaises(ValueError):
                        write_bundle(prefix, b"abcd", forged)
                    self.assertFalse(prefix.with_suffix(".bin").exists())
                    self.assertFalse(prefix.with_suffix(".json").exists())

    def test_duplicate_json_fields_rejected(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            write_bundle(prefix, b"abcd", m)
            path = prefix.with_suffix(".json")
            original = path.read_text(encoding="utf-8")
            path.write_text(original.replace(
                '"schema": 1,', '"schema": 1, "schema": 1,'
            ), encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_bundle(prefix)

    def test_oversized_manifest_rejected(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            write_bundle(prefix, b"abcd", m)
            prefix.with_suffix(".json").write_text(
                " " * (64 * 1024 + 1), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                verify_bundle(prefix)

    def test_non_object_manifest_rejected(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            write_bundle(prefix, b"abcd", m)
            prefix.with_suffix(".json").write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_bundle(prefix)

    def test_declared_length_mismatch_rejected_before_binary_read(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            write_bundle(prefix, b"abcd", m)
            prefix.with_suffix(".bin").write_bytes(b"abcd" * 4096)
            with self.assertRaisesRegex(ValueError, "Image size disagrees"):
                verify_bundle(prefix)

    def test_symlink_manifest_rejected(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            write_bundle(prefix, b"abcd", m)
            original = prefix.with_suffix(".json")
            replacement = Path(directory) / "manifest-copy.json"
            original.rename(replacement)
            original.symlink_to(replacement)
            with self.assertRaisesRegex(ValueError, "regular files"):
                verify_bundle(prefix)

    def test_symlink_image_rejected(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            write_bundle(prefix, b"abcd", m)
            original = prefix.with_suffix(".bin")
            replacement = Path(directory) / "image-copy.bin"
            original.rename(replacement)
            original.symlink_to(replacement)
            with self.assertRaisesRegex(ValueError, "regular files"):
                verify_bundle(prefix)

    def test_malformed_sha256_rejected(self):
        m = backup_manifest("chip", 4, 0, b"abcd")
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "backup"
            write_bundle(prefix, b"abcd", m)
            path = prefix.with_suffix(".json")
            original = json.loads(path.read_text(encoding="utf-8"))
            for bad in ("", "0" * 63, "G" * 64, "A" * 64, "0" * 65, 123):
                with self.subTest(digest=bad):
                    changed = dict(original)
                    changed["image_sha256"] = bad
                    path.write_text(json.dumps(changed), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        verify_bundle(prefix)

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
