from services.cache import memoize
from services.compatibility.component_matcher import ComponentMatcher
from services.compatibility.compatibility_checker import CompatibilityChecker
from services.compatibility.performance_analyzer import PerformanceAnalyzer
from services.compatibility.utils import Utils


class CompatibilityService:

    @staticmethod
    @memoize(timeout=300)
    def evaluate_build(parts_input):
        # ── 1. Detect components ────────────────────────────────
        # Accept either: a free-form string/list of names, or a list of component dicts
        if (
            isinstance(parts_input, list)
            and parts_input
            and isinstance(parts_input[0], dict)
        ):
            # Already-provided component dicts (e.g. from DB) — use directly
            detected = [
                {
                    "input": p.get("name") or str(p),
                    "component": p,
                    "source": p.get("source", "provided"),
                    "verified": p.get("verified", True),
                }
                for p in parts_input
            ]
        else:
            detected = ComponentMatcher.detect_components(parts_input)

        # ── 2. Detect unknown parts ─────────────────────────────
        unknown = [i["input"] for i in detected if i["component"] is None]
        unknown_issues = []
        if unknown:
            unknown_issues = [
                {
                    "severity": "warning",
                    "component": u,
                    "message": f"Unknown component: {u}. Analysis is based on known parts only.",
                }
                for u in unknown
            ]

        # ── 3. Group by category ────────────────────────────────
        groups = {}
        for item in detected:
            comp = item["component"]
            if not comp:
                continue
            cat = comp.get("category", "Other")
            if cat == "Storage":
                groups.setdefault("Storage", []).append(comp)
            elif cat not in groups:
                groups[cat] = comp

        cpu = groups.get("CPU")
        mb = groups.get("Motherboard")
        ram = groups.get("RAM")
        gpu = groups.get("GPU")
        psu = groups.get("PSU")
        case = groups.get("Case")
        storage = groups.get("Storage", [])

        # ── 4. Run compatibility checks ─────────────────────────
        issues, passed, recs, watt_est, rec_psu = CompatibilityChecker.check(groups)
        issues = unknown_issues + issues

        # ── 5. Determine status ─────────────────────────────────
        has_crit = any(i["severity"] == "critical" for i in issues)
        has_unknown = len(unknown) > 0

        # Keep non-critical warnings (like low RAM/storage) from downgrading overall compatibility.
        # Status rules:
        # - incompatible: any critical issues
        # - warning: unknown components present (partial analysis) or explicit warning-level unknowns
        # - compatible: otherwise (may still include non-critical warnings/recommendations)
        if has_crit:
            status = "incompatible"
            summary = "Incompatible."
        elif has_unknown:
            status = "warning"
            summary = "Unknown components detected. Analysis completed for known parts."
        else:
            status = "compatible"
            summary = "Compatible."

        # ── 6. Calculate total price ────────────────────────────
        total = 0
        # Sum prices from all detected groups (include Cooling and other categories).
        for cat, comp in groups.items():
            items = comp if isinstance(comp, list) else [comp]
            for c in items:
                if c and not c.get("estimated"):
                    p = Utils.num(c.get("price"))
                    if p and p > 0:
                        total += p
        # Round to nearest integer to match frontend total display
        total = int(round(total))

        # ── 7. Performance analysis ─────────────────────────────
        tier = fps_data = bot = res = ups = None
        # actual PSU wattage (from detected PSU spec) — used for upgrade suggestions
        psu_w = Utils.num(psu.get("specs", {}).get("wattage", 0)) if psu else 0

        if status != "incompatible" and cpu and gpu:
            cpu_s = PerformanceAnalyzer.cpu_score(cpu)
            gpu_s = PerformanceAnalyzer.gpu_score(gpu)
            ram_cap = Utils.num(ram.get("specs", {}).get("capacity", 0)) if ram else 0
            tier = PerformanceAnalyzer.tier(cpu_s, gpu_s)
            res = PerformanceAnalyzer.resolution(gpu_s)
            fps_data = PerformanceAnalyzer.fps(cpu_s, gpu_s)
            bot = PerformanceAnalyzer.bottleneck(cpu_s, gpu_s)
            ups = PerformanceAnalyzer.upgrades(
                gpu_s, cpu_s=cpu_s, has_gpu=True, ram_capacity=ram_cap, psu_w=psu_w
            )
        elif status != "incompatible" and cpu and not gpu:
            cpu_s = PerformanceAnalyzer.cpu_score(cpu)
            gpu_s = 0
            tier = PerformanceAnalyzer.tier(cpu_s, gpu_s)
            res = PerformanceAnalyzer.resolution(gpu_s)
            fps_data = PerformanceAnalyzer.fps(cpu_s, gpu_s)
            bot = PerformanceAnalyzer.bottleneck(cpu_s, gpu_s)
            ups = PerformanceAnalyzer.upgrades(
                gpu_s, cpu_s=cpu_s, has_gpu=False, psu_w=psu_w
            )

        # ── 8. Build output parts list ──────────────────────────
        parts_out = []
        for i in detected:
            c = i["component"]
            p = Utils.num(c.get("price")) if c else None
            parts_out.append(
                {
                    "name": c.get("name", i["input"]) if c else i["input"],
                    "type": c.get("category", "Unknown") if c else "Unknown",
                    "source": i["source"],
                    "verified": i["verified"],
                    "price": p,
                    "priceFormatted": f"₱{p:,.2f}" if p else "N/A",
                }
            )

        # ── 9. Return final report ──────────────────────────────
        return {
            "compatible": status != "incompatible",
            "status": status,
            "summary": summary,
            "buildTier": tier,
            "totalBuildPrice": total,
            "totalBuildPriceFormatted": f"₱{total:,.2f}" if total else "N/A",
            "wattageEstimate": watt_est,
            "recommendedPsuWattage": rec_psu,
            "detectedParts": parts_out,
            "issues": issues,
            "passedChecks": passed,
            "recommendations": recs,
            "bottleneckAnalysis": bot,
            "gamingResolution": res,
            "estimatedFps": fps_data or {},
            "upgradeSuggestions": ups,
        }
