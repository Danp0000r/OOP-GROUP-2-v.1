from typing import List, Dict, Optional
import os
import logging
from models.component import Component
from services.compatibility.compatibility_service import CompatibilityService
from services.compatibility.compatibility_checker import CompatibilityChecker
from services.compatibility.utils import Utils
from database.db import db


class BuildFixService:

    @staticmethod
    def fix_build(parts: List[Dict], answers: Optional[Dict] = None) -> Dict:
        report = CompatibilityService.evaluate_build(parts)
        if report.get("compatible"):
            return {
                "fixed": True,
                "components": parts,
                "changes": [],
                "compatibility_report": report,
            }

        # Work on a copy. Normalize keys to `category` values to avoid 'type' vs 'category' mismatches.
        CATEGORY_ORDER = [
            "CPU",
            "Motherboard",
            "RAM",
            "GPU",
            "Storage",
            "Cooling",
            "PSU",
            "Case",
        ]
        working = {}
        for p in parts:
            if not p:
                continue
            key = p.get("category") or p.get("type")
            if not key:
                key = ""
            working[key] = p
        # setup logger/debug flag
        DEBUG = (
            os.environ.get("FLASK_DEBUG", os.environ.get("DEBUG", "false")).lower()
            == "true"
        )
        logger = logging.getLogger(__name__)
        changes = []

        # Helper: re-evaluate and short-circuit if fixed
        def reevaluate():
            # Preserve category field when building list for re-evaluation
            plist = []
            for k, v in working.items():
                if v and not v.get("category"):
                    v["category"] = k
                plist.append(v)
            rep = CompatibilityService.evaluate_build(plist)
            return rep

        rep = report

        # Process critical issues in order of low-impact first (socket, RAM, form factor, cooler/case, GPU/case, PSU)
        criticals = [
            i for i in rep.get("issues", []) if i.get("severity") == "critical"
        ]

        def _normalize_list(value):
            if value is None:
                return []
            if isinstance(value, (list, tuple, set)):
                return list(value)
            return [value]

        def _find_ram_candidate(types):
            q = Component.query.filter_by(category="RAM")
            for t in types:
                t_str = str(t).strip()
                if not t_str:
                    continue
                try:
                    cand = (
                        q.filter(
                            Component.compatibility["ram_type"].astext.ilike(
                                f"%{t_str}%"
                            )
                        )
                        .order_by(Component.price.asc())
                        .first()
                    )
                except Exception:
                    try:
                        cand = (
                            q.filter(Component.specs["type"].astext.ilike(f"%{t_str}%"))
                            .order_by(Component.price.asc())
                            .first()
                        )
                    except Exception:
                        cand = (
                            q.filter(Component.name.ilike(f"%{t_str}%"))
                            .order_by(Component.price.asc())
                            .first()
                        )
                if cand:
                    return cand
            try:
                return q.order_by(Component.price.asc()).first()
            except Exception:
                return q.first()

        def _find_component_by_socket(category, socket_value):
            """Find component by socket, using Python-side filtering."""
            socket = str(socket_value).strip().upper()
            if not socket:
                if DEBUG:
                    logger.debug(f"_find_component_by_socket: Empty socket value")
                return None

            if DEBUG:
                logger.debug(
                    f"_find_component_by_socket: Looking for {category} with socket {socket}"
                )

            # Get all components of this category
            all_components = (
                Component.query.filter_by(category=category)
                .order_by(Component.price.asc())
                .limit(20)
                .all()
            )

            if not all_components:
                if DEBUG:
                    logger.debug(f"  No {category} components in database")
                return None

            # Filter using Python-side matching
            for comp in all_components:
                specs = comp.specs or {}
                compat = comp.compatibility or {}

                # Extract socket/cpu_socket from component
                comp_socket = None
                if category == "Motherboard":
                    comp_socket = (
                        compat.get("cpu_socket")
                        or specs.get("socket_type")
                        or specs.get("socket")
                    )
                elif category == "CPU":
                    comp_socket = compat.get("motherboard_socket") or specs.get(
                        "socket"
                    )
                else:
                    comp_socket = compat.get("cpu_socket") or specs.get("socket")

                if comp_socket:
                    comp_socket = str(comp_socket).upper()
                    if comp_socket == socket:
                        if DEBUG:
                            logger.debug(
                                f"  ✓ Found {comp.name} with socket {comp_socket}"
                            )
                        return comp

            if DEBUG:
                logger.debug(
                    f"  ✗ No {category} found with socket {socket}, returning cheapest"
                )
            return all_components[0] if all_components else None

        def _find_cooler_for_socket(cpu_socket):
            q = Component.query.filter_by(category="Cooling")
            try:
                candidates = (
                    q.filter(
                        Component.compatibility["cpu_socket"].astext.ilike(
                            f"%{cpu_socket}%"
                        )
                    )
                    .order_by(Component.price.asc())
                    .all()
                )
            except Exception:
                candidates = (
                    q.filter(Component.name.ilike(f"%{cpu_socket}%"))
                    .order_by(Component.price.asc())
                    .all()
                )
            return candidates[0] if candidates else None

        def _find_case_for_radiator(rad):
            q = Component.query.filter_by(category="Case")
            try:
                candidates = (
                    q.filter(
                        Component.specs["radiator_support"].astext.ilike(f"%{rad}%")
                    )
                    .order_by(Component.price.asc())
                    .all()
                )
            except Exception:
                candidates = (
                    q.filter(Component.name.ilike(f"%{rad}%"))
                    .order_by(Component.price.asc())
                    .all()
                )
            return candidates[0] if candidates else None

        def fix_psu():
            psu = working.get("PSU")
            if not psu:
                return False
            try:
                need = int(rep.get("recommendedPsuWattage") or 0)
            except Exception:
                need = None
            if need:
                q = Component.query.filter_by(category="PSU")
                try:
                    candidate = q.filter(Component.specs["wattage"].astext.cast(db.Integer) >= need).order_by(Component.price.asc()).first()  # type: ignore
                except Exception:
                    candidate = None
                    for c in q.order_by(Component.price.asc()).all():
                        try:
                            pw = int((c.specs or {}).get("wattage") or 0)
                        except Exception:
                            pw = 0
                        if pw >= need:
                            candidate = c
                            break
                if candidate:
                    new = candidate.to_dict()
                    if not psu or new.get("name") != psu.get("name"):
                        old = psu
                        working["PSU"] = new
                        changes.append(
                            {
                                "category": "PSU",
                                "from": old.get("name") if old else None,
                                "to": new.get("name"),
                            }
                        )
                        return True
            return False

        def fix_ram():
            ram = working.get("RAM")
            mb = working.get("Motherboard")
            cpu = working.get("CPU")

            if not ram:
                if DEBUG:
                    logger.debug("fix_ram: No RAM in working dict")
                return False

            # Determine desired RAM type from motherboard first (highest priority)
            desired = []
            if mb:
                # Try multiple possible locations for ram_type in motherboard
                mb_ram_type = mb.get("compatibility", {}).get("ram_type") or mb.get(
                    "specs", {}
                ).get("ram_type")
                if mb_ram_type:
                    desired.extend(_normalize_list(mb_ram_type))

            # If motherboard doesn't specify, check CPU compatibility
            if not desired and cpu:
                cpu_ram_types = cpu.get("compatibility", {}).get("ram_type")
                if cpu_ram_types:
                    desired.extend(_normalize_list(cpu_ram_types))

            if not desired:
                if DEBUG:
                    logger.debug("fix_ram: No desired RAM type found from MB or CPU")
                return False

            # Normalize to uppercase for matching
            desired = [str(x).upper() for x in desired if x]

            if DEBUG:
                logger.debug(f"fix_ram: Need RAM types: {desired}")

            # Find candidate RAM
            unique_types = []
            for value in desired:
                if value not in unique_types:
                    unique_types.append(value)

            candidate = _find_ram_candidate(unique_types)
            if candidate:
                new = candidate.to_dict()
                current_ram_type = (
                    ram.get("compatibility", {}).get("ram_type")
                    or ram.get("specs", {}).get("type", "")
                ).upper()
                if not ram or new.get("name") != ram.get("name"):
                    old = ram
                    working["RAM"] = new
                    changes.append(
                        {
                            "category": "RAM",
                            "from": old.get("name") if old else None,
                            "to": new.get("name"),
                        }
                    )
                    if DEBUG:
                        logger.debug(
                            f"fix_ram: Replaced RAM '{old.get('name') if old else None}' -> '{new.get('name')}'"
                        )
                    return True

            if DEBUG:
                logger.debug(
                    f"fix_ram: No compatible RAM found for types {unique_types}"
                )

            return False

        def fix_cooler_case():
            cooler = working.get("Cooling")
            case = working.get("Case")
            if not cooler or not case:
                return False
            changed = False
            ch = Utils.num(cooler.get("specs", {}).get("height_mm", 0))
            cl = Utils.num(case.get("specs", {}).get("cpu_cooler_limit_mm", 999))
            if ch and cl and ch > cl:
                q = Component.query.filter_by(category="Cooling")
                try:
                    cand = (
                        q.filter(Component.name.ilike("%low-profile%"))
                        .order_by(Component.price.asc())
                        .first()
                    )
                except Exception:
                    cand = q.order_by(Component.price.asc()).first()
                if cand:
                    new = cand.to_dict()
                    old = cooler
                    working["Cooling"] = new
                    changes.append(
                        {
                            "category": "Cooling",
                            "from": old.get("name"),
                            "to": new.get("name"),
                        }
                    )
                    return True
            rad = cooler.get("specs", {}).get("radiator_size")
            rad_support = case.get("specs", {}).get("radiator_support", [])
            if rad and rad_support and rad not in rad_support:
                # try change case first
                case_cand = _find_case_for_radiator(rad)
                if case_cand:
                    old = case
                    working["Case"] = case_cand.to_dict()
                    changes.append(
                        {
                            "category": "Case",
                            "from": old.get("name"),
                            "to": case_cand.name,
                        }
                    )
                    return True
                # fallback: choose a compatible liquid cooler or air cooler
                q = Component.query.filter_by(category="Cooling")
                try:
                    cand = (
                        q.filter(Component.name.ilike("%air%"))
                        .order_by(Component.price.asc())
                        .first()
                    )
                except Exception:
                    cand = q.order_by(Component.price.asc()).first()
                if cand:
                    old = cooler
                    working["Cooling"] = cand.to_dict()
                    changes.append(
                        {
                            "category": "Cooling",
                            "from": old.get("name"),
                            "to": cand.name,
                        }
                    )
                    return True
            return False

        def fix_gpu_case():
            gpu = working.get("GPU")
            case = working.get("Case")
            if not gpu or not case:
                return False
            gl = Utils.num(gpu.get("specs", {}).get("length_mm", 0))
            cl = Utils.num(case.get("specs", {}).get("gpu_length_limit", 999))
            if gl and cl and gl > cl:
                perf = gpu.get("performance_score", 0)
                q = Component.query.filter_by(category="GPU")
                candidates = []
                try:
                    candidates = q.filter(Component.specs["length_mm"].astext.cast(db.Integer) <= cl).order_by(Component.performance_score.desc()).limit(5).all()  # type: ignore
                except Exception:
                    candidates = (
                        q.order_by(Component.performance_score.desc()).limit(5).all()
                    )
                for c in candidates:
                    if abs((c.performance_score or 0) - perf) <= max(
                        10, int((perf or 0) * 0.2)
                    ):
                        old = gpu
                        new = c.to_dict()
                        working["GPU"] = new
                        changes.append(
                            {
                                "category": "GPU",
                                "from": old.get("name"),
                                "to": new.get("name"),
                            }
                        )
                        return True
                qcase = Component.query.filter_by(category="Case")
                ccase = qcase.order_by(Component.price.asc()).first()
                if ccase:
                    old = case
                    working["Case"] = ccase.to_dict()
                    changes.append(
                        {"category": "Case", "from": old.get("name"), "to": ccase.name}
                    )
                    return True
            return False

        def fix_socket():
            cpu = working.get("CPU")
            mb = working.get("Motherboard")
            if not cpu or not mb:
                if DEBUG:
                    logger.debug(f"fix_socket: CPU={bool(cpu)}, MB={bool(mb)}")
                return False

            # Extract socket from CPU - try multiple possible locations
            cs = (
                cpu.get("compatibility", {}).get("motherboard_socket")
                or cpu.get("specs", {}).get("socket")
                or ""
            ).upper()

            # Extract socket from Motherboard - try multiple possible locations
            ms = (
                mb.get("compatibility", {}).get("cpu_socket")
                or mb.get("specs", {}).get("socket_type")
                or ""
            ).upper()

            if DEBUG:
                logger.debug(f"fix_socket: cpu_socket={cs}, mb_socket={ms}")

            if cs and ms and cs != ms:
                # Socket mismatch detected - try to fix
                cand = _find_component_by_socket("Motherboard", cs)
                if cand:
                    old = mb
                    working["Motherboard"] = cand.to_dict()
                    changes.append(
                        {
                            "category": "Motherboard",
                            "from": old.get("name") if old else None,
                            "to": cand.name,
                        }
                    )
                    if DEBUG:
                        logger.debug(f"fix_socket: Replaced MB with {cand.name}")
                    return True

                # If no matching motherboard, try replacing CPU if platform not locked
                platform = (answers or {}).get("platform", "")
                if platform and ("AMD" in platform or "Intel" in platform):
                    if DEBUG:
                        logger.debug(
                            f"fix_socket: Platform locked to {platform}, won't change CPU"
                        )
                    return False

                cpu_cand = _find_component_by_socket("CPU", ms)
                if cpu_cand:
                    old = cpu
                    working["CPU"] = cpu_cand.to_dict()
                    changes.append(
                        {
                            "category": "CPU",
                            "from": old.get("name") if old else None,
                            "to": cpu_cand.name,
                        }
                    )
                    if DEBUG:
                        logger.debug(f"fix_socket: Replaced CPU with {cpu_cand.name}")
                    return True

                if DEBUG:
                    logger.debug(
                        f"fix_socket: No compatible components found for socket {cs}"
                    )

            return False

        def fix_form_factor():
            mb = working.get("Motherboard")
            case = working.get("Case")
            if not mb or not case:
                return False
            mf = (mb.get("specs", {}).get("form_factor", "")).upper()
            cf = (case.get("specs", {}).get("form_factor", "")).upper()
            if mf and cf and mf != cf:
                q = Component.query.filter_by(category="Case")
                try:
                    candidates = (
                        q.filter(Component.name.ilike(f"%{mf}%"))
                        .order_by(Component.price.asc())
                        .limit(3)
                        .all()
                    )
                except Exception:
                    candidates = q.order_by(Component.price.asc()).limit(3).all()
                if candidates:
                    cand = candidates[0]
                    old = case
                    working["Case"] = cand.to_dict()
                    changes.append(
                        {"category": "Case", "from": old.get("name"), "to": cand.name}
                    )
                    return True
            return False

        def fix_cooler_socket():
            cooler = working.get("Cooling")
            cpu = working.get("CPU")
            if not cooler or not cpu:
                return False
            cooler_sockets = cooler.get("compatibility", {}).get("cpu_socket", [])
            if isinstance(cooler_sockets, str):
                cooler_sockets = [cooler_sockets]
            cooler_sockets = [s.upper() for s in cooler_sockets if s]
            cpu_socket = (
                cpu.get("compatibility", {}).get("motherboard_socket")
                or cpu.get("specs", {}).get("socket", "")
            ).upper()
            if cooler_sockets and cpu_socket and cpu_socket not in cooler_sockets:
                cand = _find_cooler_for_socket(cpu_socket)
                if cand:
                    old = cooler
                    working["Cooling"] = cand.to_dict()
                    changes.append(
                        {
                            "category": "Cooling",
                            "from": old.get("name"),
                            "to": cand.name,
                        }
                    )
                    return True
            return False

        def fix_radiator_support():
            cooler = working.get("Cooling")
            case = working.get("Case")
            if not cooler or not case:
                return False
            cooler_type = cooler.get("specs", {}).get("type", "air")
            rad = cooler.get("specs", {}).get("radiator_size")
            if cooler_type == "liquid" and rad:
                rad_support = case.get("specs", {}).get("radiator_support", [])
                if isinstance(rad_support, str):
                    rad_support = [rad_support]
                if rad_support and rad not in rad_support:
                    case_cand = _find_case_for_radiator(rad)
                    if case_cand:
                        old = case
                        working["Case"] = case_cand.to_dict()
                        changes.append(
                            {
                                "category": "Case",
                                "from": old.get("name"),
                                "to": case_cand.name,
                            }
                        )
                        return True
                    q = Component.query.filter_by(category="Cooling")
                    try:
                        cooler_cand = (
                            q.filter(Component.name.ilike("%air%"))
                            .order_by(Component.price.asc())
                            .first()
                        )
                    except Exception:
                        cooler_cand = q.order_by(Component.price.asc()).first()
                    if cooler_cand:
                        old = cooler
                        working["Cooling"] = cooler_cand.to_dict()
                        changes.append(
                            {
                                "category": "Cooling",
                                "from": old.get("name"),
                                "to": cooler_cand.name,
                            }
                        )
                        return True
            return False

        def fix_ram_cpu_support():
            ram = working.get("RAM")
            cpu = working.get("CPU")
            if not ram or not cpu:
                return False
            rt = (
                ram.get("compatibility", {}).get("ram_type")
                or ram.get("specs", {}).get("type", "")
            ).upper()
            cr = cpu.get("compatibility", {}).get("ram_type", [])
            if isinstance(cr, str):
                cr = [cr]
            cr = [x.upper() for x in cr if x]
            if rt and cr and rt not in cr:
                return fix_ram()
            return False

        if report.get("compatible") and not any(
            i.get("severity") == "warning" for i in rep.get("issues", [])
        ):
            return {
                "fixed": True,
                "components": parts,
                "changes": [],
                "compatibility_report": report,
            }

        fix_functions = [
            fix_socket,
            fix_ram,
            fix_ram_cpu_support,
            fix_form_factor,
            fix_gpu_case,
            fix_cooler_case,
            fix_cooler_socket,
            fix_radiator_support,
            fix_psu,
        ]

        max_iters = 8
        for _ in range(max_iters):
            applied_any = False
            for f in fix_functions:
                try:
                    applied = f()
                except Exception:
                    applied = False
                if applied:
                    applied_any = True
                    rep = reevaluate()
                    if rep.get("compatible") and not any(
                        i.get("severity") == "warning" for i in rep.get("issues", [])
                    ):
                        ordered_components = [
                            working.get(c) for c in CATEGORY_ORDER if working.get(c)
                        ]
                        return {
                            "fixed": True,
                            "components": ordered_components,
                            "changes": changes,
                            "compatibility_report": rep,
                        }
            if not applied_any:
                break

        rep = reevaluate()
        ordered_components = [working.get(c) for c in CATEGORY_ORDER if working.get(c)]
        return {
            "fixed": rep.get("compatible", False),
            "components": ordered_components,
            "changes": changes,
            "compatibility_report": rep,
        }
