from typing import List, Dict, Optional
from models.component import Component
from services.compatibility.compatibility_service import CompatibilityService
from services.compatibility.compatibility_checker import CompatibilityChecker
from services.compatibility.utils import Utils
from database.db import db


class BuildFixService:
    """Attempt minimal, questionnaire-aware fixes for incompatible builds."""

    @staticmethod
    def fix_build(parts: List[Dict], answers: Optional[Dict] = None) -> Dict:
        """
        parts: list of component dicts (name, category, specs, price...)
        answers: optional questionnaire answers (may include 'platform' and 'budget')

        Returns: {
          'fixed': bool,
          'components': updated parts list,
          'changes': [ { 'category': ..., 'from': ..., 'to': ... } ],
          'compatibility_report': report
        }
        """
        report = CompatibilityService.evaluate_build(parts)
        if report.get('compatible'):
            return { 'fixed': True, 'components': parts, 'changes': [], 'compatibility_report': report }

        # Work on a copy
        working = {p.get('type') if p.get('type') else p.get('category'): p for p in parts if p}
        changes = []

        # Helper: re-evaluate and short-circuit if fixed
        def reevaluate():
            plist = [v for k, v in working.items()]
            rep = CompatibilityService.evaluate_build(plist)
            return rep

        rep = report

        # Process critical issues in order of low-impact first (PSU, RAM, Cooler/Case, GPU/Case, Socket, Form factor)
        criticals = [i for i in rep.get('issues', []) if i.get('severity') == 'critical']

        # Strategy functions
        def fix_psu():
            psu = working.get('PSU')
            if not psu:
                return False
            rec_w = rep.get('recommendedPsuWattage') or rep.get('recommendedPsuWattage')
            try:
                need = int(rec_w)
            except Exception:
                need = None
            if need:
                q = Component.query.filter_by(category='PSU')
                try:
                    candidate = q.filter(Component.specs['wattage'].astext.cast(db.Integer) >= need).order_by(Component.price.asc()).first()  # type: ignore
                except Exception:
                    # fallback: search by wattage field in specs may not be available; pick cheapest PSU with wattage >= need by scanning
                    candidate = None
                    for c in q.order_by(Component.price.asc()).all():
                        try:
                            pw = int((c.specs or {}).get('wattage') or 0)
                        except Exception:
                            pw = 0
                        if pw >= need:
                            candidate = c
                            break
                if candidate and candidate.price and candidate.price != psu.get('price'):
                    old = psu
                    new = candidate.to_dict()
                    working['PSU'] = new
                    changes.append({'category': 'PSU', 'from': old.get('name'), 'to': new.get('name')})
                    return True
            return False

        def fix_ram():
            ram = working.get('RAM')
            mb = working.get('Motherboard')
            cpu = working.get('CPU')
            desired = None
            # prefer motherboard requirement
            if mb:
                desired = (mb.get('compatibility', {}).get('ram_type') or mb.get('specs', {}).get('ram_type'))
            if not desired and cpu:
                desired = cpu.get('compatibility', {}).get('ram_type')
            if not desired:
                return False
            desired = str(desired).lower()
            q = Component.query.filter_by(category='RAM')
            # try name contains desired
            cand = q.filter(Component.name.ilike(f"%{desired}%")).order_by(Component.price.asc()).first()
            if not cand:
                cand = q.order_by(Component.price.asc()).first()
            if cand:
                new = cand.to_dict()
                if not ram or new.get('name') != ram.get('name'):
                    old = ram
                    working['RAM'] = new
                    changes.append({'category': 'RAM', 'from': old.get('name') if old else None, 'to': new.get('name')})
                    return True
            return False

        def fix_cooler_case():
            cooler = working.get('Cooling')
            case = working.get('Case')
            if not cooler or not case:
                return False
            # check cooler height
            ch = Utils.num(cooler.get('specs', {}).get('height_mm', 0))
            cl = Utils.num(case.get('specs', {}).get('cpu_cooler_limit_mm', 999))
            if ch and cl and ch > cl:
                # try find smaller cooler
                q = Component.query.filter_by(category='Cooling')
                cand = q.filter(Component.name.ilike('%low-profile%')).order_by(Component.price.asc()).first()
                if not cand:
                    cand = q.order_by(Component.price.asc()).first()
                if cand:
                    new = cand.to_dict()
                    old = cooler
                    working['Cooling'] = new
                    changes.append({'category': 'Cooling', 'from': old.get('name'), 'to': new.get('name')})
                    return True
            # radiator support
            rad = cooler.get('specs', {}).get('radiator_size')
            rad_support = case.get('specs', {}).get('radiator_support', [])
            if rad and rad_support and rad not in rad_support:
                # try find AIO that fits or replace case
                q = Component.query.filter_by(category='Cooling')
                cand = q.filter(Component.name.ilike('%aio%')).order_by(Component.price.asc()).first()
                if cand:
                    working['Cooling'] = cand.to_dict()
                    changes.append({'category': 'Cooling', 'from': cooler.get('name'), 'to': cand.name})
                    return True
            return False

        def fix_gpu_case():
            gpu = working.get('GPU')
            case = working.get('Case')
            if not gpu or not case:
                return False
            gl = Utils.num(gpu.get('specs', {}).get('length_mm', 0))
            cl = Utils.num(case.get('specs', {}).get('gpu_length_limit', 999))
            if gl and cl and gl > cl:
                # try find shorter GPU with similar performance (±20%)
                perf = gpu.get('performance_score', 0)
                q = Component.query.filter_by(category='GPU')
                candidates = []
                try:
                    candidates = q.filter(Component.specs['length_mm'].astext.cast(db.Integer) <= cl).order_by(Component.performance_score.desc()).limit(5).all()  # type: ignore
                except Exception:
                    candidates = q.order_by(Component.performance_score.desc()).limit(5).all()
                for c in candidates:
                    if abs((c.performance_score or 0) - perf) <= max(10, int((perf or 0) * 0.2)):
                        old = gpu
                        new = c.to_dict()
                        working['GPU'] = new
                        changes.append({'category': 'GPU', 'from': old.get('name'), 'to': new.get('name')})
                        return True
                # fallback: try replacing case instead
                qcase = Component.query.filter_by(category='Case')
                ccase = qcase.order_by(Component.price.asc()).first()
                if ccase:
                    old = case
                    working['Case'] = ccase.to_dict()
                    changes.append({'category': 'Case', 'from': old.get('name'), 'to': ccase.name})
                    return True
            return False

        def fix_socket():
            cpu = working.get('CPU')
            mb = working.get('Motherboard')
            if not cpu or not mb:
                return False
            cs = (cpu.get('compatibility', {}).get('motherboard_socket') or cpu.get('specs', {}).get('socket', '')).upper()
            ms = (mb.get('compatibility', {}).get('cpu_socket') or mb.get('specs', {}).get('socket_type', '')).upper()
            if cs and ms and cs != ms:
                # Prefer changing motherboard to match CPU
                socket_str = cs.lower()
                q = Component.query.filter_by(category='Motherboard')
                candidates = []
                # Prefer JSON field match on specs/compatibility
                try:
                    from sqlalchemy import or_
                    q_filtered = q.filter(
                        or_(
                            Component.specs['socket_type'].astext.ilike(f"%{socket_str}%"),
                            Component.compatibility['cpu_socket'].astext.ilike(f"%{socket_str}%")
                        )
                    )
                    candidates = q_filtered.order_by(Component.price.asc()).limit(5).all()
                except Exception:
                    # Fallback to name-based or in-Python filtering if JSON queries unsupported
                    try:
                        candidates = q.filter(Component.name.ilike(f"%{socket_str}%")).order_by(Component.price.asc()).limit(5).all()
                    except Exception:
                        candidates = q.order_by(Component.price.asc()).limit(20).all()

                # As a last fallback, scan loaded components for matching specs in Python
                if not candidates:
                    all_mbs = q.order_by(Component.price.asc()).all()
                    for m in all_mbs:
                        try:
                            st = (m.specs or {}).get('socket_type') or (m.compatibility or {}).get('cpu_socket')
                            if st and socket_str in str(st).lower():
                                candidates.append(m)
                                if len(candidates) >= 5:
                                    break
                        except Exception:
                            continue

                if candidates:
                    cand = candidates[0]
                    old = mb
                    working['Motherboard'] = cand.to_dict()
                    changes.append({'category': 'Motherboard', 'from': old.get('name'), 'to': cand.name})
                    return True
                # fallback: try changing CPU if allowed by answers
                platform = (answers or {}).get('platform', '')
                # if user explicitly chose a platform, avoid changing CPU
                if platform and ('AMD' in platform or 'Intel' in platform):
                    return False
                # try find CPU matching motherboard socket
                sock = ms.lower()
                qcpu = Component.query.filter_by(category='CPU')
                try:
                    cpu_cands = qcpu.filter(Component.name.ilike(f"%{sock}%")).order_by(Component.performance_score.desc()).limit(3).all()
                except Exception:
                    cpu_cands = qcpu.order_by(Component.performance_score.desc()).limit(3).all()
                if cpu_cands:
                    cand = cpu_cands[0]
                    old = cpu
                    working['CPU'] = cand.to_dict()
                    changes.append({'category': 'CPU', 'from': old.get('name'), 'to': cand.name})
                    return True
            return False

        def fix_form_factor():
            mb = working.get('Motherboard')
            case = working.get('Case')
            if not mb or not case:
                return False
            mf = (mb.get('specs', {}).get('form_factor', '')).upper()
            cf = (case.get('specs', {}).get('form_factor', '')).upper()
            # If mismatch, try find case that fits
            if mf and cf and mf != cf:
                q = Component.query.filter_by(category='Case')
                try:
                    candidates = q.filter(Component.name.ilike(f"%{mf}%")).order_by(Component.price.asc()).limit(3).all()
                except Exception:
                    candidates = q.order_by(Component.price.asc()).limit(3).all()
                if candidates:
                    cand = candidates[0]
                    old = case
                    working['Case'] = cand.to_dict()
                    changes.append({'category': 'Case', 'from': old.get('name'), 'to': cand.name})
                    return True
            return False

        # Try fixes in prioritized order, re-evaluating after each.
        fix_functions = [fix_psu, fix_ram, fix_cooler_case, fix_gpu_case, fix_socket, fix_form_factor]

        for f in fix_functions:
            try:
                applied = f()
            except Exception:
                applied = False
            if applied:
                rep = reevaluate()
                if rep.get('compatible'):
                    return { 'fixed': True, 'components': [v for k, v in working.items()], 'changes': changes, 'compatibility_report': rep }

        # Last-ditch: return best attempted report
        return { 'fixed': False, 'components': [v for k, v in working.items()], 'changes': changes, 'compatibility_report': rep }
