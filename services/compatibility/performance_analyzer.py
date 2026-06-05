class PerformanceAnalyzer:

    @staticmethod
    def cpu_score(name_or_component):
        if isinstance(name_or_component, dict):
            return name_or_component.get("performance_score", 50)
        
        # Fallback to legacy name-based matching
        scores = {
            "3100": 40, "3600": 55, "5600g": 60, "5600": 65,
            "5700x": 80, "7800x3d": 95,
            "12100f": 50, "12400f": 65, "13400f": 80,
            "13600k": 85, "14900k": 100
        }
        name_l = str(name_or_component).lower()
        for k, v in scores.items():
            if k in name_l:
                return v
        return 50

    @staticmethod
    def gpu_score(name_or_component):
        if isinstance(name_or_component, dict):
            return name_or_component.get("performance_score", 50)
        
        # Fallback to legacy name-based matching
        scores = {
            "gtx 1650": 25, "gtx 1660 super": 38, "rx 6600": 48,
            "rtx 3060": 50, "rtx 4060": 58, "rx 7700 xt": 75,
            "rtx 4070": 80, "rtx 4080": 90, "rtx 4090": 100
        }
        name_l = str(name_or_component).lower()
        for k, v in scores.items():
            if k in name_l:
                return v
        return 50

    @staticmethod
    def tier(cpu_s, gpu_s):
        s = gpu_s * 0.7 + cpu_s * 0.3
        # Slightly more conservative thresholds to classify low-end builds as Budget
        if s < 35:
            return "Budget"
        elif s < 55:
            return "Entry-Midrange"
        elif s < 75:
            return "Midrange"
        elif s < 90:
            return "High-End"
        else:
            return "Enthusiast"

    @staticmethod
    def resolution(gpu_s):
        if gpu_s >= 75:
            return "1440p High / 4K Medium-High (60+ fps)"
        elif gpu_s >= 58:
            return "1080p Ultra / 1440p High (60+ fps)"
        elif gpu_s >= 48:
            return "1080p High / 1440p Medium (60+ fps)"
        elif gpu_s >= 38:
            return "1080p High (60+ fps) / 1440p Low-Medium"
        elif gpu_s >= 25:
            return "1080p Medium (60+ fps)"
        else:
            return "1080p Low-Medium (30-60 fps)"
    
    @staticmethod
    def fps_disclaimer():
        return (
            "FPS estimates are approximate conservative benchmarks at 1080p High settings. "
            "Assumes DLSS/FSR enabled where available (recommended for AAA titles). "
            "Actual performance varies by: exact game settings, driver version, OS, GPU memory clock, "
            "background processes, monitor refresh rate, and power limits. "
            "Higher FPS possible with lower settings or FSR Quality mode. "
            "4K estimates assume Medium-High settings, not Ultra."
        )

    @staticmethod
    def fps(cpu_s, gpu_s):
        # GPU baseline FPS tables (1080p High settings, with DLSS enabled where available)
        # Conservative estimates - actual may vary by driver, OS, background apps
        gpu_baselines = {
            "CS2": {25: 180, 38: 250, 48: 300, 50: 320, 58: 340, 75: 380},
            "Valorant": {25: 220, 38: 290, 48: 340, 50: 360, 58: 400, 75: 440},
            "Fortnite": {25: 100, 38: 145, 48: 185, 50: 200, 58: 240, 75: 290},
            "GTA V": {25: 75, 38: 100, 48: 125, 50: 140, 58: 150, 75: 180},
            "Cyberpunk": {25: 40, 38: 55, 48: 70, 50: 90, 58: 105, 75: 130},
        }
        
        results = {}
        
        # CPU modifier: ratio affects performance
        if cpu_s > 0 and gpu_s > 0:
            ratio = cpu_s / gpu_s
            if ratio < 0.6:
                cpu_mod = 0.85  # Heavy bottleneck
            elif ratio < 0.8:
                cpu_mod = 0.92  # Moderate bottleneck
            elif ratio > 1.5:
                cpu_mod = 1.0   # CPU-strong, no modifier
            else:
                cpu_mod = 0.95  # Balanced
        else:
            cpu_mod = 1.0
        
        for game, baselines in gpu_baselines.items():
            # Find closest baseline for GPU score
            closest_gpu = min(baselines.keys(), key=lambda x: abs(x - gpu_s))
            base_1080p = baselines[closest_gpu]
            
            # Apply CPU modifier
            fps_1080p = max(15, int(base_1080p * cpu_mod))
            
            results[game] = {
                "1080p": fps_1080p,
                "1440p": int(fps_1080p * 0.62),
                "4K": int(fps_1080p * 0.33)
            }
        
        return results

    @staticmethod
    def bottleneck(cpu_s, gpu_s):
        if cpu_s == 0 or gpu_s == 0:
            return {
                "description": "Insufficient data.",
                "balance": "Unknown",
                "cpuPerformanceScore": cpu_s,
                "gpuPerformanceScore": gpu_s
            }

        ratio = cpu_s / gpu_s

        if ratio < 0.6:
            desc = "Heavy CPU bottleneck – GPU significantly under‑utilised."
            balance = "CPU-limited"
        elif ratio < 0.8:
            desc = "Moderate CPU bottleneck in CPU‑intensive titles."
            balance = "CPU-heavy"
        elif ratio > 1.5:
            desc = "CPU much stronger – GPU is the main limiter. Great for high-refresh gaming."
            balance = "GPU-focused gaming build"
        elif ratio > 1.2:
            desc = "Slight GPU bottleneck, typical for GPU‑bound games."
            balance = "GPU-leaning"
        else:
            desc = "Well‑balanced for 1080p gaming."
            balance = "Excellent balance"

        return {
            "description": desc,
            "balance": balance,
            "cpuPerformanceScore": cpu_s,
            "gpuPerformanceScore": gpu_s
        }

    @staticmethod
    def upgrades(gpu_s, cpu_s=None, has_gpu=False, ram_capacity=0, psu_w=0):
        if not has_gpu:
            return ["Add a dedicated GPU for gaming (RTX 4060 or RX 6600 recommended)."]
        
        suggestions = []
        
        # GPU upgrade path
        if gpu_s >= 75:
            suggestions.append("GPU already high-end. Consider 32GB RAM or 1440p+ monitor upgrade.")
        elif gpu_s >= 58:
            suggestions.append("GPU solid for 1080p. Next tier: RTX 4070 / RX 7800 XT for 1440p.")
        elif gpu_s >= 48:
            suggestions.append("GPU good for 1080p. Consider RTX 4060 / RX 6700 for improved 1440p gaming.")
        elif gpu_s >= 38:
            suggestions.append("Upgrade GPU to RTX 4060 / RX 6600 for smoother 1080p High settings.")
        else:
            suggestions.append("Upgrade GPU to at least GTX 1660 Super / RX 580 for playable 1080p gaming.")
        
        # CPU/GPU balance context
        if cpu_s and gpu_s > 0:
            ratio = cpu_s / gpu_s
            if ratio < 0.6:
                suggestions.append("IMPORTANT: CPU is bottlenecking GPU. Upgrade CPU to match GPU tier.")
            elif ratio > 1.5:
                suggestions.append("CPU upgrade not priority. GPU upgrade will provide more gaming benefit.")
        
        # PSU headroom warning
        if psu_w > 0 and gpu_s >= 58 and psu_w < 750:
            suggestions.append("PSU marginal for high-end GPU upgrades. Consider 750W+ PSU.")
        
        # RAM adequacy
        if ram_capacity > 0 and ram_capacity < 16:
            suggestions.append("Upgrade to 16GB RAM for modern games (8GB is below recommended).")
        elif ram_capacity >= 16:
            suggestions.append("RAM is adequate for modern gaming.")
        
        return suggestions