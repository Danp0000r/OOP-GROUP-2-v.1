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
    def test_evaluate_build_returns_compatible_report(self):
        report = CompatibilityService.evaluate_build(
            "Intel i5-12400F, RTX 4060, 750W 80+ Gold PSU"
        )
        self.assertIsInstance(report, dict)
        self.assertIn("status", report)
        self.assertIn("detectedParts", report)
        self.assertTrue(report["compatible"])
        self.assertEqual(report["status"], "compatible")

    def test_loader_preserves_performance_scores(self):
        components = ComponentLoader.load()
        ryzen = next((c for c in components if c.get("name") == "Ryzen 7 5700X"), None)
        rx7700 = next((c for c in components if c.get("name") == "RX 7700 XT"), None)
        self.assertIsNotNone(ryzen)
        self.assertIsNotNone(rx7700)
        self.assertEqual(ryzen.get("performance_score"), 80)
        self.assertEqual(rx7700.get("performance_score"), 75)

    def test_get_component_prefers_exact_base_match(self):
        result = ComponentMatcher.get_component("RTX 4060")
        self.assertIsNotNone(result)
        self.assertEqual(result.get("name"), "RTX 4060")

    def test_unknown_components_do_not_block_analysis(self):
        report = CompatibilityService.evaluate_build(
            "Intel i5-12400F, Samsung 990 EVO Plus"
        )
        self.assertTrue(report["compatible"])
        self.assertEqual(report["status"], "warning")
        self.assertTrue(any(
            i["severity"] == "warning" and "Unknown component" in i["message"]
            for i in report["issues"]
        ))
        self.assertTrue(any(part.get("source") == "unknown" for part in report["detectedParts"]))

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
        self.assertEqual(rtx_4070.get("price"), 32495)
        self.assertEqual(ddr4_3600.get("price"), 6495)


def print_report(report):
    print("\nCOMPATIBILITY SUMMARY")
    print("=" * 50)
    print(f"Status: {report['status'].upper()}  |  Compatible: {report['compatible']}")

    tier = report.get('buildTier')
    if tier:
        print(f"Build Tier: {tier}")
        reason = report.get('tierReason')
        if reason:
            print(f"  → {reason}")

    print(f"Total Price: {report.get('totalBuildPriceFormatted', 'Price unavailable')}")
    print(f"Summary: {report['summary']}")

    # Safe access with defaults
    wattage = report.get('wattageEstimate')
    psu_rec = report.get('recommendedPsuWattage')
    if wattage is not None:
        print(f"Estimated Wattage: {wattage}W")
    if psu_rec is not None:
        print(f"Recommended PSU: {psu_rec}W")
    print()

    print("Detected Parts:")
    for part in report.get("detectedParts", []):
        name = part.get('name')
        ptype = part.get('type')
        source = part.get('source', 'unknown')
        verified = part.get('verified', False)
        price_str = part.get('priceFormatted', 'N/A')

        label = f"[{ptype}] {name} ({source})"
        if verified:
            label += " [✔ Verified]"
        else:
            label += " [⚠ Not Verified]"
        print(f" - {label}  Price: {price_str}")

    if report.get("issues"):
        print("\nIssues:")
        for issue in report.get("issues", []):
            print(f" - {issue.get('severity').upper()} [{issue.get('component')}] {issue.get('message')}")

    if report.get("passedChecks"):
        print("\nPassed Compatibility Checks:")
        for note in report["passedChecks"]:
            print(f" - {note}")

    if report.get("recommendations"):
        print("\nRecommendations:")
        for rec in report["recommendations"]:
            print(f" - {rec}")

    perf = report.get("performanceSummary")
    if perf:
        print(f"\n📊 Performance Summary: {perf}")

    # ✅ Updated: Uses balance category instead of fake percentages
    bot = report.get("bottleneckAnalysis")
    if bot:
        print("\nBottleneck Analysis:")
        print(f" - Balance: {bot.get('balance', 'N/A')}")
        print(f" - CPU Performance Score: {bot.get('cpuPerformanceScore', 'N/A')}")
        print(f" - GPU Performance Score: {bot.get('gpuPerformanceScore', 'N/A')}")
        print(f" - Note: {bot.get('description', '')}")

    if report.get("gamingResolution"):
        print(f"\nEstimated Gaming Resolution: {report['gamingResolution']}")

    # ✅ Updated: Adds settings disclaimer
    fps = report.get("estimatedFps")
    if fps:
        print("\nEstimated FPS (1080p / 1440p / 4K):")
        print("  (Assumes High settings, DLSS/FSR enabled where available)")
        for game, data in fps.items():
            print(f" - {game}: {data.get('1080p', '?')} / {data.get('1440p', '?')} / {data.get('4K', '?')} FPS")

    if report.get("upgradeSuggestions"):
        print("\nUpgrade Suggestions:")
        for sug in report["upgradeSuggestions"]:
            print(f" - {sug}")

    if report.get("valueRating"):
        print(f"\n💡 Value Rating: {report['valueRating']}")
    if report.get("airflowWarning"):
        print(f"\nAirflow Warning: {report['airflowWarning']}")
    if report.get("futureHeadroom"):
        print(f"\nFuture Upgrade Headroom: {report['futureHeadroom']}")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        default_parts = "Intel i5-12400F, ASUS B760M-A WIFI, 32GB DDR5 6000MHz, RTX 4060, 750W 80+ Gold PSU, Montech Air 100 ARGB"

        if len(sys.argv) > 1:
            parts = " ".join(sys.argv[1:])
        else:
            print("Enter PC components (or press Enter for default):")
            user_input = input().strip()
            parts = user_input if user_input else default_parts

        print(f"\nEvaluating build: {parts}")
        report = CompatibilityService.evaluate_build(parts)
        print_report(report)

    input("\nPress Enter to exit...")