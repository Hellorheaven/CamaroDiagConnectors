import unittest

from camarodiagconnectors.memory import Geometry, Patch, Region, Technology, plan_patches


class MemoryPlanTests(unittest.TestCase):
    def setUp(self):
        self.eeprom = Geometry("24LC32", Technology.I2C_EEPROM, 128, 16)
        self.nor = Geometry("test-NOR", Technology.SPI_NOR, 128, 8, 32)
        self.image = bytes([0xAA] * 128)

    def test_reject_unsupported_technology(self):
        with self.assertRaisesRegex(ValueError, "Unsupported memory technology"):
            Geometry("unknown", "spi_nor", 128, 8, 32)

    def test_reject_boolean_geometry_dimensions(self):
        for capacity, page_size, erase_size in (
            (True, 1, None),
            (128, True, None),
            (128, 8, True),
        ):
            with self.subTest(capacity=capacity, page_size=page_size, erase_size=erase_size):
                technology = Technology.SPI_NOR if erase_size is not None else Technology.I2C_EEPROM
                with self.assertRaisesRegex(ValueError, "dimensions must be integers"):
                    Geometry("invalid", technology, capacity, page_size, erase_size)

    def test_reject_invalid_protected_region(self):
        with self.assertRaisesRegex(ValueError, "Protected regions"):
            Geometry("invalid", Technology.I2C_EEPROM, 128, 8, protected=((0, 8),))

    def test_single_byte_eeprom_updates_only_one_page(self):
        plan = plan_patches(self.eeprom, self.image, [Patch(4, b"\xbb")])
        self.assertEqual(plan.changed_bytes, 1)
        self.assertEqual([(o.region.start, o.region.end) for o in plan.operations], [(0, 16)])
        self.assertEqual(plan.proposed_image[5:], self.image[5:])
        self.assertFalse(plan.write_authorized)

    def test_two_patches_in_same_page(self):
        plan = plan_patches(self.eeprom, self.image, [Patch(0, b"\x00"), Patch(15, b"\x00")])
        self.assertEqual(len(plan.operations), 1)
        self.assertEqual(plan.changed_bytes, 2)

    def test_two_pages(self):
        plan = plan_patches(self.eeprom, self.image, [Patch(15, b"\x00\x00")])
        self.assertEqual(len(plan.operations), 2)

    def test_identical_patch_is_noop(self):
        plan = plan_patches(self.eeprom, self.image, [Patch(7, b"\xaa")])
        self.assertEqual(plan.operations, ())
        self.assertEqual(plan.changed_bytes, 0)

    def test_nor_reports_erase_sector_not_only_patch_byte(self):
        plan = plan_patches(self.nor, self.image, [Patch(5, b"\x00")])
        self.assertEqual(plan.operations[0].region, Region(0, 32))
        self.assertEqual(plan.operations[0].method, "sector-read-erase-rewrite")
        self.assertEqual(plan.proposed_image[6:], self.image[6:])

    def test_nor_two_sectors(self):
        plan = plan_patches(self.nor, self.image, [Patch(31, b"\x00\x00")])
        self.assertEqual(len(plan.operations), 2)

    def test_refuse_protected_changed_address(self):
        g = Geometry("locked", Technology.I2C_EEPROM, 128, 16, protected=(Region(8, 9),))
        with self.assertRaises(ValueError):
            plan_patches(g, self.image, [Patch(8, b"\x00")])

    def test_refuse_protected_neighbor_on_same_page(self):
        g = Geometry("locked", Technology.I2C_EEPROM, 128, 16, protected=(Region(8, 9),))
        with self.assertRaises(ValueError):
            plan_patches(g, self.image, [Patch(1, b"\x00")])

    def test_refuse_protected_neighbor_same_erase_sector(self):
        g = Geometry("locked", Technology.SPI_NOR, 128, 8, 32, protected=(Region(20, 22),))
        with self.assertRaises(ValueError):
            plan_patches(g, self.image, [Patch(1, b"\x00")])

    def test_refuse_out_of_bounds(self):
        with self.assertRaises(ValueError):
            plan_patches(self.eeprom, self.image, [Patch(127, b"\x00\x11")])

    def test_refuse_overlap(self):
        with self.assertRaises(ValueError):
            plan_patches(self.eeprom, self.image, [Patch(3, b"\x00\x01"), Patch(4, b"\x02")])

    def test_refuse_missing_original_bytes(self):
        with self.assertRaises(ValueError):
            plan_patches(self.eeprom, b"\x00", [Patch(0, b"\x01")])

    def test_refuse_invalid_geometry(self):
        with self.assertRaises(ValueError):
            Geometry("NOR", Technology.SPI_NOR, 128, 8, 20)

    def test_refuse_overlapping_protected(self):
        with self.assertRaises(ValueError):
            Geometry("chip", Technology.I2C_EEPROM, 128, 16, protected=(Region(1, 9), Region(8, 12)))


if __name__ == "__main__":
    unittest.main()
