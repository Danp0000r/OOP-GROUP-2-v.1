import os
import sys
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT_DIR)

from __init__ import create_app
from services.compatibility import CompatibilityService
from services.compatibility.component_loader import ComponentLoader
from services.compatibility.component_matcher import ComponentMatcher
from services.compatibility.performance_analyzer import PerformanceAnalyzer


class CompatibilityServiceTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_evaluate_build_returns_compatible_report(self):
        # Basic build should return a compatible report.
        report = CompatibilityService.evaluate_build(
            "Intel i5-12400F, RTX 4060, 750W 80+ Gold PSU"
        )
        self.assertIsInstance(report, dict, "report should be a dictionary")
        self.assertIn("status", report, "report needs a status")
        self.assertIn("detectedParts", report, "report needs detected parts")
        self.assertTrue(report["compatible"], "build should be compatible")
        self.assertEqual(report["status"], "compatible", "status should be compatible")

    def test_loader_preserves_performance_scores(self):
        # Loader should keep the performance scores from the DB.
        components = ComponentLoader.load()
        ryzen = next((c for c in components if c.get("name") == "Ryzen 7 5700X"), None)
        rx7700 = next((c for c in components if c.get("name") == "RX 7700 XT"), None)
        self.assertIsNotNone(ryzen, "Ryzen 7 5700X should be in components")
        self.assertIsNotNone(rx7700, "RX 7700 XT should be in components")
        self.assertEqual(ryzen.get("performance_score"), 80, "Ryzen score should be 80")
        self.assertEqual(rx7700.get("performance_score"), 75, "RX 7700 XT score should be 75")

    def test_get_component_prefers_exact_base_match(self):
        # Exact base product names should match the correct component.
        result = ComponentMatcher.get_component("RTX 4060")
        self.assertIsNotNone(result, "component matcher should find RTX 4060")
        self.assertEqual(result.get("name"), "RTX 4060", "should return exact RTX 4060")

    def test_unknown_components_do_not_block_analysis(self):
        # Unknown part should only give warning, not break known checks.
        report = CompatibilityService.evaluate_build(
            "Intel i5-12400F, Samsung 990 EVO Plus"
        )
        self.assertTrue(report["compatible"], "build should still be compatible with unknown part")
        self.assertEqual(report["status"], "warning", "status should be warning for unknown items")
        self.assertTrue(any(
            i["severity"] == "warning" and "Unknown component" in i["message"]
            for i in report["issues"]
        ), "warning should mention unknown component")
        self.assertTrue(any(part.get("source") == "unknown" for part in report["detectedParts"]), "unknown source should be marked")

    def test_socket_mismatch(self):
        # If CPU and motherboard sockets do not match, the build is bad.
        cpu = {
            "name": "Intel i5-12400F",
            "category": "CPU",
            "specs": {"socket": "LGA1700", "tdp": 65},
            "compatibility": {"motherboard_socket": "LGA1700"}
        }
        mb = {
            "name": "MSI B550 Tomahawk",
            "category": "Motherboard",
            "specs": {"socket_type": "AM4"},
            "compatibility": {"cpu_socket": "AM4"}
        }
        report = CompatibilityService.evaluate_build([cpu, mb])
        self.assertFalse(report["compatible"], "socket mismatch should be incompatible")
        self.assertEqual(report["status"], "incompatible", "status should show incompatible")
        self.assertTrue(any("Socket mismatch" in issue["message"] for issue in report["issues"]), "issue should mention socket mismatch")

    def test_empty_build(self):
        # Empty input should still return a report with no parts.
        report = CompatibilityService.evaluate_build("")
        self.assertIsInstance(report, dict, "empty build should produce a report")
        self.assertEqual(report["status"], "compatible", "empty build should be compatible")
        self.assertEqual(report["detectedParts"], [], "no parts should be detected")

    def test_ram_type_mismatch(self):
        # DDR4 RAM on a DDR5 board should be incompatible.
        cpu = {
            "name": "Intel i5-12400F",
            "category": "CPU",
            "specs": {"socket": "LGA1700", "tdp": 65},
            "compatibility": {"motherboard_socket": "LGA1700", "ram_type": ["DDR5"]}
        }
        mb = {
            "name": "ASUS B760M-A WIFI",
            "category": "Motherboard",
            "specs": {"socket_type": "LGA1700", "ram_type": "DDR5"},
            "compatibility": {"cpu_socket": "LGA1700", "ram_type": "DDR5"}
        }
        ram = {
            "name": "32GB DDR4 3600MHz",
            "category": "RAM",
            "specs": {"type": "DDR4", "capacity": 32},
            "compatibility": {"ram_type": "DDR4"}
        }
        report = CompatibilityService.evaluate_build([cpu, mb, ram])
        self.assertFalse(report["compatible"], "RAM mismatch should be incompatible")
        self.assertEqual(report["status"], "incompatible", "status should say incompatible")
        self.assertTrue(any("RAM type mismatch" in issue["message"] for issue in report["issues"]), "should report a RAM type mismatch")

    def test_insufficient_psu(self):
        # A high-end GPU with a weak PSU should fail.
        cpu = {
            "name": "Intel i9-14900K",
            "category": "CPU",
            "specs": {"socket": "LGA1700", "tdp": 125},
            "compatibility": {"motherboard_socket": "LGA1700"}
        }
        gpu = {
            "name": "RTX 4080",
            "category": "GPU",
            "specs": {"tdp": 320, "length_mm": 304},
            "compatibility": {}
        }
        psu = {
            "name": "550W 80+ Bronze PSU",
            "category": "PSU",
            "specs": {"wattage": 550}
        }
        report = CompatibilityService.evaluate_build([cpu, gpu, psu])
        self.assertFalse(report["compatible"], "weak PSU should not be compatible with high-end GPU")
        self.assertEqual(report["status"], "incompatible", "status should be incompatible for PSU failure")
        self.assertTrue(any("insufficient" in issue["message"].lower() for issue in report["issues"]), "should report insufficient wattage")

    def test_gpu_too_large_for_case(self):
        # GPU that is longer than the case limit should be incompatible.
        gpu = {
            "name": "RTX 4070",
            "category": "GPU",
            "specs": {"tdp": 200, "length_mm": 330}
        }
        case = {
            "name": "Compact Case",
            "category": "Case",
            "specs": {"gpu_length_limit": 300}
        }
        report = CompatibilityService.evaluate_build([gpu, case])
        self.assertFalse(report["compatible"], "large GPU should not fit the compact case")
        self.assertEqual(report["status"], "incompatible", "status should be incompatible for size mismatch")
        self.assertTrue(any("GPU" in issue["component"] and "case" in issue["message"].lower() for issue in report["issues"]), "should report GPU/case clearance problem")

    def test_resolution_for_midrange_gpu_is_conservative(self):
        self.assertEqual(
            PerformanceAnalyzer.resolution(58),
            "1080p Ultra / 1440p High (60+ fps)"
        )

    def test_new_components_available(self):
        components = ComponentLoader.load()
        rtx_4070 = next((c for c in components if c.get("name") == "RTX 4070"), None)
        ddr4_3600 = next((c for c in components if c.get("name") == "32GB DDR4 3600MHz"), None)
        self.assertIsNotNone(rtx_4070)
        self.assertIsNotNone(ddr4_3600)
        self.assertEqual(rtx_4070.get("performance_score"), 80)
        self.assertEqual(ddr4_3600.get("performance_score"), 75)
        self.assertEqual(rtx_4070.get("price"), 30995.0)
        self.assertEqual(ddr4_3600.get("price"), 5995.0)


if __name__ == "__main__":
    unittest.main()

