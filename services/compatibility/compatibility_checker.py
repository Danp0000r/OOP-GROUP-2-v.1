from services.compatibility.utils import Utils


class CompatibilityChecker:

    @staticmethod
    def check(groups):
        cpu = groups.get("CPU")
        mb = groups.get("Motherboard")
        ram = groups.get("RAM")
        gpu = groups.get("GPU")
        psu = groups.get("PSU")
        case = groups.get("Case")
        cooler = groups.get("Cooling")
        storage = groups.get("Storage", [])

        issues, passed, recs = [], [], []

        # ── Socket ──────────────────────────────────────────────
        if cpu and mb:
            cs = (cpu.get("compatibility", {}).get("motherboard_socket") or
                  cpu.get("specs", {}).get("socket", "")).upper()
            ms = (mb.get("compatibility", {}).get("cpu_socket") or
                  mb.get("specs", {}).get("socket_type", "")).upper()
            if cs and ms:
                if cs != ms:
                    issues.append({
                        "severity": "critical",
                        "component": "CPU/Motherboard",
                        "message": f"Socket mismatch: {cs} vs {ms}"
                    })
                    recs.append(f"Use {cs} motherboard or {ms} CPU.")
                else:
                    passed.append(f"✓ Socket: {cs}")

        # ── RAM (motherboard + CPU) ─────────────────────────────
        if ram and mb:
            rt = (ram.get("compatibility", {}).get("ram_type") or
                  ram.get("specs", {}).get("type", "")).upper()
            mr = (mb.get("compatibility", {}).get("ram_type") or
                  mb.get("specs", {}).get("ram_type", "")).upper()

            ram_ok = True

            # Motherboard compatibility
            if rt and mr and rt != mr:
                issues.append({
                    "severity": "critical",
                    "component": "RAM/Motherboard",
                    "message": f"RAM type mismatch: RAM is {rt}, motherboard requires {mr}"
                })
                recs.append(f"Use {mr} RAM.")
                ram_ok = False

            # CPU compatibility (independent check)
            if cpu:
                cr = cpu.get("compatibility", {}).get("ram_type", [])
                if isinstance(cr, str):
                    cr = [cr]
                cr = [x.upper() for x in cr]
                if cr and rt and rt not in cr:
                    issues.append({
                        "severity": "critical",
                        "component": "CPU/RAM",
                        "message": f"CPU does not support {rt} RAM. Supported: {', '.join(cr)}"
                    })
                    recs.append(f"Use RAM compatible with CPU ({', '.join(cr)}).")
                    ram_ok = False

            if ram_ok:
                passed.append(f"✓ RAM: {rt}")

        # ── PSU ─────────────────────────────────────────────────
        cpu_w = Utils.num(cpu.get("specs", {}).get("tdp", 65)) if cpu else 65
        gpu_w = Utils.num(gpu.get("specs", {}).get("tdp", 100)) if gpu else 0
        watt_est = int((cpu_w + gpu_w + 100) * 1.25)
        rec_psu = next((t for t in [450, 500, 550, 600, 650, 750, 850, 1000] if t >= int(watt_est * 1.3)), 500)

        if psu:
            pw = Utils.num(psu.get("specs", {}).get("wattage", 0))
            if pw < watt_est:
                issues.append({
                    "severity": "critical",
                    "component": "PSU",
                    "message": f"{pw}W insufficient for {watt_est}W"
                })
                recs.append(f"Get {rec_psu}W+ PSU.")
            elif pw >= rec_psu:
                passed.append(f"✓ PSU: {pw}W (load ~{watt_est}W)")

            # Headroom check for future upgrades
            if pw >= rec_psu * 1.5:
                passed.append(f"💡 PSU headroom: {pw}W allows future GPU upgrades")

        # ── Form Factor ─────────────────────────────────────────
        if mb and case:
            mf = (mb.get("specs", {}).get("form_factor", "ATX")).upper()
            cf = (case.get("specs", {}).get("form_factor", "ATX")).upper()
            fits = {
                "ATX": ["ATX", "MATX", "MICROATX", "ITX"],
                "MATX": ["MATX", "MICROATX", "ITX"],
                "ITX": ["ITX"]
            }
            if mf in fits.get(cf, []):
                passed.append(f"✓ Form: {mf} in {cf}")
            else:
                issues.append({
                    "severity": "critical",
                    "component": "Case",
                    "message": f"{mf} doesn't fit {cf}"
                })

        # ── GPU Clearance ───────────────────────────────────────
        if gpu and case:
            gl = Utils.num(gpu.get("specs", {}).get("length_mm",
                            gpu.get("specs", {}).get("length", "0mm")))
            cl = Utils.num(case.get("specs", {}).get("gpu_length_limit", 999))
            if gl and cl and gl <= cl:
                passed.append(f"✓ GPU: {gl}mm in {cl}mm")
            elif gl and cl:
                issues.append({
                    "severity": "critical",
                    "component": "GPU/Case",
                    "message": f"GPU {gl}mm > case {cl}mm"
                })

        # ── CPU Cooler Height Clearance (air coolers) ───────────
        if cooler and case:
            ch = Utils.num(cooler.get("specs", {}).get("height_mm", 0))
            cl = Utils.num(case.get("specs", {}).get("cpu_cooler_limit_mm", 999))
            cooler_type = cooler.get("specs", {}).get("type", "air")
            if cooler_type == "air" and ch and cl:
                if ch <= cl:
                    passed.append(f"✓ Cooler: {ch}mm fits (limit {cl}mm)")
                else:
                    issues.append({
                        "severity": "critical",
                        "component": "Cooler/Case",
                        "message": f"CPU cooler {ch}mm exceeds case limit {cl}mm"
                    })

        # ── Radiator Support (liquid coolers) ───────────────────
        if cooler and case:
            rad = cooler.get("specs", {}).get("radiator_size", "")
            rad_support = case.get("specs", {}).get("radiator_support", [])
            cooler_type = cooler.get("specs", {}).get("type", "air")
            if cooler_type == "liquid" and rad and rad_support:
                if rad in rad_support:
                    passed.append(f"✓ Radiator: {rad} supported by case")
                else:
                    issues.append({
                        "severity": "critical",
                        "component": "Cooler/Case",
                        "message": f"Case does not support {rad} radiator"
                    })

        # ── Cooler Socket Compatibility ─────────────────────────
        if cooler and cpu:
            cooler_sockets = cooler.get("compatibility", {}).get("cpu_socket", [])
            cpu_socket = (cpu.get("compatibility", {}).get("motherboard_socket") or
                         cpu.get("specs", {}).get("socket", "")).upper()
            if cooler_sockets and cpu_socket:
                if isinstance(cooler_sockets, str):
                    cooler_sockets = [cooler_sockets]
                cooler_sockets = [s.upper() for s in cooler_sockets]
                if cpu_socket in cooler_sockets:
                    passed.append(f"✓ Cooler compatible with {cpu_socket}")
                else:
                    issues.append({
                        "severity": "warning",
                        "component": "Cooler/CPU",
                        "message": f"Cooler may not support {cpu_socket} socket"
                    })

        return issues, passed, recs, watt_est, rec_psu