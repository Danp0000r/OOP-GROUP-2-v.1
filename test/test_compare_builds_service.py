import os
import sys
import datetime
import unittest
from unittest.mock import MagicMock, patch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT_DIR)

from services.comparison.compare_builds_service import (
    parse_component_ids,
    compare_builds,
)


class CompareBuildsServiceTestCase(unittest.TestCase):

    def test_parse_component_ids_handles_list_string_and_invalid(self):
        # parse_component_ids should normalize valid JSON lists and return empty for invalid data.
        self.assertEqual(parse_component_ids([1, 2]), [1, 2])
        self.assertEqual(parse_component_ids("[1, 2]"), [1, 2])
        self.assertEqual(parse_component_ids("bad json"), [])
        self.assertEqual(parse_component_ids(None), [])

    def test_compare_builds_returns_expected_items(self):
        # Comparing builds should return structured item details and compatibility results.
        build_a = MagicMock()
        build_a.id = 10
        build_a.name = "Build A"
        build_a.created_at = datetime.datetime(2024, 1, 1)
        build_a.component_ids = "[1, 2]"
        build_a.compatibility_status = "compatible"

        comp1 = MagicMock()
        comp1.component_id = 1
        comp1.name = "Part 1"
        comp1.brand = "Brand1"
        comp1.category = "CPU"
        comp1.price = 100
        comp1.specs = {"speed": "3GHz"}
        comp1.performance_score = 50

        comp2 = MagicMock()
        comp2.component_id = 2
        comp2.name = "Part 2"
        comp2.brand = "Brand2"
        comp2.category = "RAM"
        comp2.price = 50
        comp2.specs = {"size": "16GB"}
        comp2.performance_score = 20

        build_query = MagicMock()
        build_query.filter.return_value.all.return_value = [build_a]

        component_query = MagicMock()
        component_query.filter.return_value.all.return_value = [comp1, comp2]

        fake_build = MagicMock()
        fake_build.query = build_query
        fake_component = MagicMock()
        fake_component.query = component_query

        with patch(
            "services.comparison.compare_builds_service.Build", new=fake_build
        ), patch(
            "services.comparison.compare_builds_service.Component", new=fake_component
        ), patch(
            "services.comparison.compare_builds_service.CompatibilityService.evaluate_build",
            return_value={"compatible": True},
        ) as mocked_eval:
            result = compare_builds([10], 1)

        self.assertEqual(len(result["items"]), 1)
        item = result["items"][0]
        self.assertEqual(item["id"], 10)
        self.assertEqual(item["name"], "Build A")
        self.assertEqual(item["part_count"], 2)
        self.assertEqual(item["total_price"], 150)
        self.assertEqual(item["compatibility_status"], "compatible")
        self.assertIn("compatibility_report", item)
        mocked_eval.assert_called_once()


if __name__ == "__main__":
    unittest.main()
