import os
import sys
import unittest
from unittest.mock import MagicMock, patch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT_DIR)

import services.cache
from services.comparison.compare_parts_service import compare_components


class ComparePartsServiceTestCase(unittest.TestCase):

    def setUp(self):
        services.cache._cache_store.clear()

    def test_compare_components_returns_empty_result_when_no_components(self):
        # When no components are found, comparison should return an empty result set.
        query = MagicMock()
        query.filter.return_value.all.return_value = []
        fake_component = MagicMock()
        fake_component.query = query

        with patch(
            "services.comparison.compare_parts_service.Component", new=fake_component
        ):
            result = compare_components([1, 2])

        self.assertEqual(result["items"], [])
        self.assertEqual(result["all_keys"], [])
        self.assertFalse(result["same_type"])
        self.assertIn("Component Comparison", result["export_text"])

    def test_compare_components_formats_output_and_same_type(self):
        # Component comparison should format output and detect same-type parts.
        part1 = MagicMock()
        part1.component_id = 1
        part1.to_dict.return_value = {
            "category": "RAM",
            "name": "RAM-A",
            "brand": "BrandA",
            "price": 50,
            "specs": {"speed": "3200MHz"},
        }

        part2 = MagicMock()
        part2.component_id = 2
        part2.to_dict.return_value = {
            "category": "RAM",
            "name": "RAM-B",
            "brand": "BrandB",
            "price": 60,
            "specs": {"speed": "3600MHz"},
        }

        query = MagicMock()
        query.filter.return_value.all.return_value = [part1, part2]
        fake_component = MagicMock()
        fake_component.query = query

        with patch(
            "services.comparison.compare_parts_service.Component", new=fake_component
        ):
            result = compare_components([1, 2])

        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["all_keys"], ["speed"])
        self.assertTrue(result["same_type"])
        self.assertIn("RAM 1: RAM-A", result["export_text"])
        self.assertIn("RAM 2: RAM-B", result["export_text"])


if __name__ == "__main__":
    unittest.main()
