import json
from services.cache import memoize
from sqlalchemy import or_
from models.component import Component

# Compatibility and performance helpers
from services.compatibility.compatibility_service import CompatibilityService
from services.compatibility.performance_analyzer import PerformanceAnalyzer
from services.build_finder.build_fix_service import BuildFixService


@memoize(timeout=300)
def get_build_recommendation(answers: dict) -> dict:
    
    # Determine parameters from answers
    platform = answers.get('platform', 'No Preference (Optimized Value)')
    form_factor = answers.get('formFactor', 'Standard ATX (Spacious Layout)')
    tier = answers.get('targetTier', 'Education, Office & Light Gaming')
    style = answers.get('style', 'Stealth Air Cooling (No-RGB)')
    budget_request = answers.get('budget', 'Normal Cost')
    
    # Determine which CPU platform to prefer
    prefer_amd = 'AMD' in platform
    prefer_intel = 'Intel' in platform
    
    # Scenario-aware budget allocation
    allocations = _get_allocations(tier)
    
    # Generate ALL compatible builds without fixed budget constraints
    all_builds = _generate_all_candidate_builds(
        tier, allocations, form_factor, style,
        prefer_amd, prefer_intel
    )
    
    if not all_builds:
        return {
            'component_ids': [],
            'components': [],
            'total_price': 0,
            'answers': answers,
            'issues': ['Unable to assemble any compatible builds. Database may lack components.']
        }
    
    # Categorize builds into low/normal/high by price
    builds_by_tier = _categorize_builds_by_price(all_builds)
    
    # Select build based on user's budget tier request
    selected_build = None
    budget_lower = budget_request.lower()
    if any(token in budget_lower for token in ['low', 'budget build', 'under']):
        selected_build = builds_by_tier.get('low', [None])[0]
    elif any(token in budget_lower for token in ['normal', 'mainstream', 'mid']):
        selected_build = builds_by_tier.get('normal', [None])[0]
    elif any(token in budget_lower for token in ['high', 'high performance', 'enthusiast']):
        selected_build = builds_by_tier.get('high', [None])[-1]  # Get the most expensive
    else:
        # Fallback: choose normal if available, otherwise first available
        selected_build = builds_by_tier.get('normal', [None])[0] or all_builds[0]
    
    # Fallback to any build if categorization failed
    if not selected_build:
        selected_build = all_builds[0]
    
    # Build ordered response
    recommended_ids = []
    components = []
    total_price = 0
    for cat in ['CPU', 'Motherboard', 'RAM', 'GPU', 'Storage', 'Cooling', 'PSU', 'Case']:
        comp = selected_build.get(cat)
        if comp:
            recommended_ids.append(comp.get('id'))
            components.append(comp)
            total_price += comp.get('price') or 0
    
    # ALWAYS recompute compatibility to catch socket mismatches, etc.
    # Build parts list for compatibility check
    parts_for_check = []
    for comp in components:
        parts_for_check.append({
            'name': comp.get('name'),
            'category': comp.get('category'),
            'brand': comp.get('brand'),
            'specs': comp.get('specs', {}),
            'performance_score': comp.get('performance_score'),
            'price': comp.get('price'),
        })
    
    # Check actual compatibility (not just the stored report)
    report = CompatibilityService.evaluate_build(parts_for_check)
    changes_made = []

    # If incompatible, attempt minimal fixes while respecting questionnaire answers
    if report.get('status') == 'incompatible' or not report.get('compatible'):
        fix_result = BuildFixService.fix_build(parts_for_check, answers=answers)
        if fix_result.get('fixed'):
            # adopt fixed components and recompute ids/price/report
            fixed_components = fix_result.get('components', [])
            components = fixed_components
            
            # Look up database IDs for all fixed components
            recommended_ids = []
            for comp in fixed_components:
                # If component already has an id, use it
                if comp.get('id'):
                    recommended_ids.append(comp.get('id'))
                else:
                    # Look up by name and category
                    db_comp = Component.query.filter_by(
                        name=comp.get('name'),
                        category=comp.get('category')
                    ).first()
                    if db_comp:
                        recommended_ids.append(db_comp.component_id)
            
            total_price = int(round(sum((c.get('price') or 0) for c in fixed_components)))
            report = fix_result.get('compatibility_report') or report
            changes_made = fix_result.get('changes', [])
    
    return {
        'component_ids': recommended_ids,
        'components': components,
        'total_price': int(round(total_price)),
        'answers': answers,
        'compatibility_report': report,
        'scenario': _classify_scenario(tier),
        'build_score': selected_build.get('_score', 0),
        'price_tier': selected_build.get('_price_tier', 'normal'),
        'all_builds_count': len(all_builds),
        'low_count': len(builds_by_tier.get('low', [])),
        'normal_count': len(builds_by_tier.get('normal', [])),
        'high_count': len(builds_by_tier.get('high', []))
    }


def _get_allocations(tier: str) -> dict:
    if 'Streaming' in tier or 'Creation' in tier:
        # Heavy on CPU and GPU for streaming/content creation
        return {
            'CPU': 0.25,
            'GPU': 0.30,
            'Motherboard': 0.12,
            'RAM': 0.15,  # More RAM for multitasking
            'Storage': 0.10,
            'Cooling': 0.05,
            'PSU': 0.08,
            'Case': 0.05
        }
    elif 'Gaming' in tier:
        # Heavy GPU emphasis for gaming
        return {
            'CPU': 0.20,
            'GPU': 0.40,  # GPU-heavy
            'Motherboard': 0.10,
            'RAM': 0.10,
            'Storage': 0.08,
            'Cooling': 0.05,
            'PSU': 0.09,
            'Case': 0.04
        }
    else:
        # Office/light gaming — balanced budget
        return {
            'CPU': 0.25,
            'GPU': 0.25,
            'Motherboard': 0.12,
            'RAM': 0.12,
            'Storage': 0.12,
            'Cooling': 0.05,
            'PSU': 0.07,
            'Case': 0.05
        }


def _classify_scenario(tier: str) -> str:
    if 'Streaming' in tier or 'Creation' in tier:
        return 'streaming_creation'
    elif 'Gaming' in tier:
        return 'gaming'
    else:
        return 'office_light'


def _categorize_builds_by_price(all_builds: list) -> dict:
    if not all_builds:
        return {'low': [], 'normal': [], 'high': []}
    
    # Sort by total price
    sorted_builds = sorted(all_builds, key=lambda b: b.get('_total_price', 0))
    
    count = len(sorted_builds)
    low_threshold = max(1, count // 3)
    high_threshold = max(2, count * 2 // 3)
    
    categorized = {
        'low': sorted_builds[:low_threshold],
        'normal': sorted_builds[low_threshold:high_threshold],
        'high': sorted_builds[high_threshold:]
    }
    
    # Mark each build with its tier
    for build in categorized['low']:
        build['_price_tier'] = 'low'
    for build in categorized['normal']:
        build['_price_tier'] = 'normal'
    for build in categorized['high']:
        build['_price_tier'] = 'high'
    
    return categorized


def _generate_all_candidate_builds(tier: str, allocations: dict,
                                   form_factor: str, style: str,
                                   prefer_amd: bool, prefer_intel: bool) -> list:
    all_builds = []
    
    # Get CPUs at 3 price/performance levels
    budget_cpus = _candidate_cpus(tier, 6000, prefer_amd, prefer_intel, limit=2)  # Budget CPUs
    mid_cpus = _candidate_cpus(tier, 9000, prefer_amd, prefer_intel, limit=3)     # Mid CPUs
    high_cpus = _candidate_cpus(tier, 12000, prefer_amd, prefer_intel, limit=2)   # High CPUs
    
    all_cpu_candidates = budget_cpus + mid_cpus + high_cpus
    
    if not all_cpu_candidates:
        print("[DEBUG] No CPUs found at any price level")
        return []
    
    # For each CPU, build 3 variants (min/mid/max price)
    for cpu_comp in all_cpu_candidates:
        # Min-cost variant (cheapest compatible parts)
        min_build = _build_around_cpu_variant(
            cpu_comp, tier, allocations, form_factor, style,
            prefer_amd, prefer_intel, variant='min'
        )
        if min_build:
            all_builds.append(min_build)
        
        # Mid-cost variant
        mid_build = _build_around_cpu_variant(
            cpu_comp, tier, allocations, form_factor, style,
            prefer_amd, prefer_intel, variant='mid'
        )
        if mid_build:
            all_builds.append(mid_build)
        
        # Max-cost variant (best compatible parts)
        max_build = _build_around_cpu_variant(
            cpu_comp, tier, allocations, form_factor, style,
            prefer_amd, prefer_intel, variant='max'
        )
        if max_build:
            all_builds.append(max_build)
    
    if not all_builds:
        return []
    
    # Sort by: (compatibility_status, performance_score)
    def build_score(build):
        report = build.get('_report', {})
        status = report.get('status', 'incompatible')
        perf = build.get('_performance', {}).get('score', 0)
        
        # Status priority: compatible > warning > incompatible
        status_priority = {'compatible': 3, 'warning': 2, 'incompatible': 1}.get(status, 0)
        
        # Return tuple for sorting: higher status and higher perf first
        return (status_priority, perf)
    
    all_builds.sort(key=build_score, reverse=True)
    
    return all_builds


def _build_around_cpu_variant(cpu_comp: Component, tier: str, allocations: dict,
                              form_factor: str, style: str,
                              prefer_amd: bool, prefer_intel: bool,
                              variant: str = 'mid') -> dict:
    cpu_dict = cpu_comp.to_dict()
    cpu_price = cpu_dict.get('price', 0)
    
    # Find compatible motherboard at appropriate price level
    if variant == 'min':
        mb_candidates = _find_compatible_motherboards(cpu_comp, form_factor, 3000, limit=1)
    elif variant == 'max':
        mb_candidates = _find_compatible_motherboards(cpu_comp, form_factor, 10000, limit=2)
    else:
        mb_candidates = _find_compatible_motherboards(cpu_comp, form_factor, 5000, limit=2)
    
    if not mb_candidates:
        return None
    
    mb_comp = mb_candidates[0]
    mb_dict = mb_comp.to_dict()
    mb_price = mb_dict.get('price', 0)
    
    # Find compatible RAM
    if variant == 'min':
        ram_candidates = _find_compatible_ram(mb_comp, 2000, limit=1)
    elif variant == 'max':
        ram_candidates = _find_compatible_ram(mb_comp, 5000, limit=2)
    else:
        ram_candidates = _find_compatible_ram(mb_comp, 3000, limit=2)
    
    if not ram_candidates:
        return None
    
    ram_comp = ram_candidates[0]
    ram_dict = ram_comp.to_dict()
    ram_price = ram_dict.get('price', 0)
    
    # GPU selection based on tier
    if 'Gaming' in tier:
        if variant == 'min':
            gpu_candidates = Component.query.filter_by(category='GPU').filter(Component.price <= 10000).order_by(Component.performance_score.desc()).limit(1).all()
        elif variant == 'max':
            gpu_candidates = Component.query.filter_by(category='GPU').order_by(Component.performance_score.desc()).limit(2).all()
        else:
            gpu_candidates = Component.query.filter_by(category='GPU').filter(Component.price <= 15000).order_by(Component.performance_score.desc()).limit(2).all()
    else:
        # Office/light gaming - entry GPU
        if variant == 'min':
            gpu_candidates = Component.query.filter_by(category='GPU').filter(Component.price <= 8000).order_by(Component.price.asc()).limit(1).all()
        elif variant == 'max':
            gpu_candidates = Component.query.filter_by(category='GPU').filter(Component.price <= 20000).order_by(Component.performance_score.desc()).limit(2).all()
        else:
            gpu_candidates = Component.query.filter_by(category='GPU').filter(Component.price <= 12000).order_by(Component.price.asc()).limit(2).all()
    
    if not gpu_candidates:
        gpu_candidates = Component.query.filter_by(category='GPU').order_by(Component.price.asc()).limit(1).all()
    
    gpu_comp = gpu_candidates[0] if gpu_candidates else None
    gpu_dict = gpu_comp.to_dict() if gpu_comp else {'id': 0, 'name': 'No GPU', 'price': 0, 'category': 'GPU'}
    gpu_price = gpu_dict.get('price', 0)
    
    # Storage
    if variant == 'min':
        storage_candidates = Component.query.filter_by(category='Storage').order_by(Component.price.asc()).limit(1).all()
    elif variant == 'max':
        storage_candidates = Component.query.filter_by(category='Storage').order_by(Component.performance_score.desc()).limit(1).all()
    else:
        storage_candidates = Component.query.filter_by(category='Storage').filter(Component.price <= 3000).order_by(Component.performance_score.desc()).limit(1).all()
    
    storage_comp = storage_candidates[0] if storage_candidates else None
    storage_dict = storage_comp.to_dict() if storage_comp else {'id': 0, 'name': 'No Storage', 'price': 0, 'category': 'Storage'}
    storage_price = storage_dict.get('price', 0)
    
    # Cooling
    if 'Stealth' in style:
        cooling_candidates = Component.query.filter_by(category='Cooling').filter(Component.name.like('%Stock%')).limit(1).all()
        if not cooling_candidates:
            cooling_candidates = Component.query.filter_by(category='Cooling').filter(Component.price <= 1500).order_by(Component.price.asc()).limit(1).all()
    else:
        if variant == 'min':
            cooling_candidates = Component.query.filter_by(category='Cooling').order_by(Component.price.asc()).limit(1).all()
        elif variant == 'max':
            cooling_candidates = Component.query.filter_by(category='Cooling').order_by(Component.price.desc()).limit(1).all()
        else:
            cooling_candidates = Component.query.filter_by(category='Cooling').filter(Component.price <= 3000).order_by(Component.price.asc()).limit(1).all()
    
    cooling_comp = cooling_candidates[0] if cooling_candidates else None
    cooling_dict = cooling_comp.to_dict() if cooling_comp else {'id': 0, 'name': 'Stock Cooler', 'price': 0, 'category': 'Cooling'}
    cooling_price = cooling_dict.get('price', 0)
    
    # PSU
    if variant == 'min':
        psu_candidates = Component.query.filter_by(category='PSU').order_by(Component.price.asc()).limit(1).all()
    elif variant == 'max':
        psu_candidates = Component.query.filter_by(category='PSU').order_by(Component.price.desc()).limit(1).all()
    else:
        psu_candidates = Component.query.filter_by(category='PSU').filter(Component.price <= 4000).order_by(Component.price.asc()).limit(1).all()
    
    psu_comp = psu_candidates[0] if psu_candidates else None
    psu_dict = psu_comp.to_dict() if psu_comp else {'id': 0, 'name': 'Generic PSU', 'price': 2595, 'category': 'PSU'}
    psu_price = psu_dict.get('price', 0)
    
    # Case
    if variant == 'min':
        case_candidates = Component.query.filter_by(category='Case').order_by(Component.price.asc()).limit(1).all()
    elif variant == 'max':
        case_candidates = Component.query.filter_by(category='Case').order_by(Component.price.desc()).limit(1).all()
    else:
        case_candidates = Component.query.filter_by(category='Case').filter(Component.price <= 3000).order_by(Component.price.asc()).limit(1).all()
    
    case_comp = case_candidates[0] if case_candidates else None
    case_dict = case_comp.to_dict() if case_comp else {'id': 0, 'name': 'Generic Case', 'price': 1550, 'category': 'Case'}
    case_price = case_dict.get('price', 0)
    
    # Assemble complete build
    build = {
        'CPU': cpu_dict,
        'Motherboard': mb_dict,
        'RAM': ram_dict,
        'GPU': gpu_dict,
        'Storage': storage_dict,
        'Cooling': cooling_dict,
        'PSU': psu_dict,
        'Case': case_dict
    }
    
    # Calculate total price
    total_price = cpu_price + mb_price + ram_price + gpu_price + storage_price + cooling_price + psu_price + case_price
    build['_total_price'] = total_price
    
    # Validate via CompatibilityService
    parts_input = {
        'CPU': cpu_dict,
        'Motherboard': mb_dict,
        'RAM': ram_dict,
        'GPU': gpu_dict,
        'Storage': storage_dict,
        'Cooling': cooling_dict,
        'PSU': psu_dict,
        'Case': case_dict
    }
    
    report = CompatibilityService.evaluate_build(parts_input)
    build['_report'] = report
    
    # Calculate performance score using available components
    cpu_score = PerformanceAnalyzer.cpu_score(cpu_dict.get('name', '')) or 0
    gpu_score = PerformanceAnalyzer.gpu_score(gpu_dict.get('name', '')) or 0
    perf_score = (cpu_score + gpu_score) / 2
    build['_performance'] = {'score': perf_score, 'cpu': cpu_score, 'gpu': gpu_score}
    build['_score'] = perf_score
    
    return build


def _generate_candidate_builds(tier: str, avg_budget: float, allocations: dict,
                                form_factor: str, style: str,
                                prefer_amd: bool, prefer_intel: bool,
                                max_candidates: int = 20) -> list:
    all_builds = []
    
    # Get CPU candidates with dynamic budget (strict first, then relaxed)
    cpu_budget = int(avg_budget * allocations['CPU'])
    cpu_candidates = _candidate_cpus(
        tier, cpu_budget, prefer_amd, prefer_intel, limit=6
    )
    
    # Aggressive fallback for tight budgets: allow 50% of total for CPU if under 20k
    if not cpu_candidates and avg_budget < 20000:
        relaxed_cpu_budget = int(avg_budget * 0.50)
        cpu_candidates = _candidate_cpus(
            tier, relaxed_cpu_budget, prefer_amd, prefer_intel, limit=6
        )
    
    # More aggressive fallback: 60% if still nothing
    if not cpu_candidates and avg_budget < 20000:
        relaxed_cpu_budget = int(avg_budget * 0.60)
        cpu_candidates = _candidate_cpus(
            tier, relaxed_cpu_budget, prefer_amd, prefer_intel, limit=8
        )
    
    # Standard relaxation: 1.5x the original budget
    if not cpu_candidates:
        relaxed_cpu_budget = int(cpu_budget * 1.5)
        cpu_candidates = _candidate_cpus(
            tier, relaxed_cpu_budget, prefer_amd, prefer_intel, limit=6
        )
    
    if not cpu_candidates:
        print(f"[DEBUG] No CPU candidates found. Strict: {cpu_budget}, Tight-budget: {int(avg_budget * 0.50)}, Very-relaxed: {int(cpu_budget * 1.5)}")
        return []
    
    # For each CPU, try to build complete compatible systems
    for cpu_comp in cpu_candidates:
        builds_for_cpu = _build_around_cpu(
            cpu_comp, tier, avg_budget, allocations,
            form_factor, style, prefer_amd, prefer_intel
        )
        all_builds.extend(builds_for_cpu)
    
    if not all_builds:
        return []
    
    # Sort by: (compatibility_status, performance_score, total_price)
    def build_score(build):
        report = build.get('_report', {})
        status = report.get('status', 'incompatible')
        perf = build.get('_performance', {}).get('score', 0)
        
        # Status priority: compatible > warning > incompatible
        status_priority = {'compatible': 3, 'warning': 2, 'incompatible': 1}.get(status, 0)
        
        # Return tuple for sorting: higher status and higher perf first
        return (status_priority, perf)
    
    all_builds.sort(key=build_score, reverse=True)
    
    # Return top candidates (prefer compatible; fallback to warning; avoid incompatible)
    compatible_builds = [b for b in all_builds if b.get('_report', {}).get('status') == 'compatible']
    if compatible_builds:
        return compatible_builds[:5]
    
    warning_builds = [b for b in all_builds if b.get('_report', {}).get('status') == 'warning']
    if warning_builds:
        return warning_builds[:5]
    
    # Last resort: return top incompatible builds and let user decide
    return all_builds[:5]


def _build_around_cpu(cpu_comp: Component, tier: str, avg_budget: float, allocations: dict,
                       form_factor: str, style: str,
                       prefer_amd: bool, prefer_intel: bool) -> list:
    builds = []
    
    cpu_dict = cpu_comp.to_dict()
    cpu_price = cpu_dict.get('price', 0)
    
    # Dynamic budget adjustment: if CPU is expensive, redistribute to other components
    # Remaining budget after CPU purchase
    remaining = avg_budget - cpu_price
    
    if remaining <= 0:
        # CPU is too expensive for this budget, skip
        print(f"[DEBUG] CPU {cpu_comp.name} (₱{cpu_price}) exceeds budget {avg_budget}")
        return []
    
    # Recalculate allocations for remaining budget
    # Shrink only the CPU allocation, keep others proportional
    remaining_allocations = allocations.copy()
    del remaining_allocations['CPU']  # Remove CPU from allocation
    total_remaining_pct = sum(remaining_allocations.values())
    
    # Normalize remaining allocations to sum to 1
    for key in remaining_allocations:
        remaining_allocations[key] = remaining_allocations[key] / total_remaining_pct
    
    # Motherboard
    mb_budget = int(remaining * remaining_allocations.get('Motherboard', 0.12))
    mb_candidates = _find_compatible_motherboards(cpu_comp, form_factor, mb_budget, limit=3)
    
    if not mb_candidates:
        # Relax budget by 30%
        relaxed_mb_budget = int(mb_budget * 1.3)
        mb_candidates = _find_compatible_motherboards(cpu_comp, form_factor, relaxed_mb_budget, limit=3)
    
    if not mb_candidates:
        # Final fallback: any motherboard
        mb_candidates = _find_motherboards(form_factor, int(mb_budget * 1.5), limit=5)
    
    if not mb_candidates:
        print(f"[DEBUG] No motherboards found for CPU {cpu_comp.name}. Budget: {mb_budget}")
        return []
    
    for mb_comp in mb_candidates:
        mb_dict = mb_comp.to_dict()
        mb_price = mb_dict.get('price', 0)
        remaining2 = remaining - mb_price
        
        if remaining2 <= 0:
            continue
        
        # RAM
        ram_budget = int(remaining2 * remaining_allocations.get('RAM', 0.12))
        ram_candidates = _find_compatible_ram(mb_comp, ram_budget, limit=2)
        
        if not ram_candidates:
            ram_candidates = _find_compatible_ram(mb_comp, int(ram_budget * 1.3), limit=3)
        
        if not ram_candidates:
            ram_candidates = _find_ram(int(ram_budget * 1.5), limit=3)
        
        if not ram_candidates:
            print(f"[DEBUG] No RAM found for MB {mb_comp.name}. Budget: {ram_budget}")
            continue
        
        for ram_comp in ram_candidates:
            ram_dict = ram_comp.to_dict()
            ram_price = ram_dict.get('price', 0)
            remaining3 = remaining2 - ram_price
            
            if remaining3 <= 0:
                continue
            
            # GPU (scenario-aware; optional for office tier)
            gpu_budget = int(remaining3 * remaining_allocations.get('GPU', 0.25))
            gpu_comp = _select_gpu_for_scenario(tier, gpu_budget)
            gpu_dict = gpu_comp.to_dict() if gpu_comp else {}
            gpu_price = gpu_dict.get('price', 0) if gpu_comp else 0
            remaining4 = remaining3 - gpu_price
            
            if remaining4 < 0:
                remaining4 = 0
            
            # Storage
            storage_budget = int(remaining4 * remaining_allocations.get('Storage', 0.10))
            storage_comp = _select_storage(storage_budget)
            
            if not storage_comp:
                storage_comp = _select_storage(int(storage_budget * 1.5))
            
            storage_dict = storage_comp.to_dict() if storage_comp else {}
            storage_price = storage_dict.get('price', 0) if storage_comp else 0
            remaining5 = remaining4 - storage_price
            
            if remaining5 < 0:
                remaining5 = 0
            
            # Cooling
            cooling_budget = int(remaining5 * remaining_allocations.get('Cooling', 0.05))
            cooling_comp = _select_cooling(style, cooling_budget)
            
            if not cooling_comp:
                cooling_comp = _select_cooling(style, int(cooling_budget * 1.5))
            
            cooling_dict = cooling_comp.to_dict() if cooling_comp else {}
            cooling_price = cooling_dict.get('price', 0) if cooling_comp else 0
            remaining6 = remaining5 - cooling_price
            
            if remaining6 < 0:
                remaining6 = 0
            
            # PSU
            psu_budget = int(remaining6 * remaining_allocations.get('PSU', 0.08))
            psu_comp = _select_psu_for_system({'CPU': cpu_dict, 'GPU': gpu_dict}, psu_budget)
            
            if not psu_comp:
                psu_comp = _select_psu_for_system({'CPU': cpu_dict, 'GPU': gpu_dict}, int(psu_budget * 1.5))
            
            psu_dict = psu_comp.to_dict() if psu_comp else {}
            psu_price = psu_dict.get('price', 0) if psu_comp else 0
            remaining7 = remaining6 - psu_price
            
            if remaining7 < 0:
                remaining7 = 0
            
            # Case (uses all remaining budget)
            case_budget = remaining7
            case_comp = _select_case(form_factor, case_budget)
            
            if not case_comp:
                case_comp = _select_case(form_factor, int(case_budget * 1.5))
            
            case_dict = case_comp.to_dict() if case_comp else {}
            
            # Assemble build dict
            build = {
                'CPU': cpu_dict,
                'Motherboard': mb_dict,
                'RAM': ram_dict,
                'Storage': storage_dict,
                'Cooling': cooling_dict,
                'Case': case_dict
            }
            if gpu_dict:
                build['GPU'] = gpu_dict
            if psu_dict:
                build['PSU'] = psu_dict
            
            # Skip if critical components missing
            if not all([build.get('CPU'), build.get('Motherboard'), build.get('RAM')]):
                continue
            
            # Validate compatibility
            parts_list = [v for v in build.values() if v]
            report = CompatibilityService.evaluate_build(parts_list)
            build['_report'] = report
            
            # Compute performance score
            cpu_s = PerformanceAnalyzer.cpu_score(cpu_dict)
            gpu_s = PerformanceAnalyzer.gpu_score(gpu_dict) if gpu_dict else 0
            perf_score = _compute_scenario_score(tier, cpu_s, gpu_s)
            build['_performance'] = {
                'cpu_score': cpu_s,
                'gpu_score': gpu_s,
                'score': perf_score
            }
            build['_score'] = perf_score
            
            builds.append(build)
    
    return builds


def _compute_scenario_score(tier: str, cpu_s: int, gpu_s: int) -> int:
    if 'Streaming' in tier or 'Creation' in tier:
        # Emphasize CPU heavily for streaming
        return int(cpu_s * 0.6 + gpu_s * 0.4)
    elif 'Gaming' in tier:
        # Emphasize GPU for gaming
        return int(cpu_s * 0.3 + gpu_s * 0.7)
    else:
        # Balanced
        return int(cpu_s * 0.5 + gpu_s * 0.5)


def _find_compatible_motherboards(cpu_comp: Component, form_factor: str, budget: int, limit: int = 3) -> list:
    q = Component.query.filter_by(category='Motherboard').filter(Component.price <= budget)
    
    # Try to extract socket from CPU
    cpu_socket = None
    try:
        specs = cpu_comp.specs or {}
        compat = cpu_comp.compatibility or {}
        cpu_socket = specs.get('socket') or compat.get('socket')
    except Exception:
        pass
    
    # Filter by socket if available
    if cpu_socket:
        socket_str = str(cpu_socket).lower()
        # Try JSON filtering
        try:
            q_filtered = q.filter(
                or_(
                    Component.specs['socket'].astext.ilike(f'%{socket_str}%'),
                    Component.compatibility['socket'].astext.ilike(f'%{socket_str}%')
                )
            )
            candidates = q_filtered.order_by(Component.performance_score.desc()).limit(limit).all()
            if candidates:
                return candidates
        except Exception:
            pass
        
        # Fallback: filter by name patterns (e.g., "LGA1700" or "AM5")
        try:
            q_filtered = q.filter(Component.name.ilike(f'%{socket_str}%'))
            candidates = q_filtered.order_by(Component.performance_score.desc()).limit(limit).all()
            if candidates:
                return candidates
        except Exception:
            pass
    
    # Final fallback: just return top motherboards by performance
    return q.order_by(Component.performance_score.desc()).limit(limit).all()


def _find_motherboards(form_factor: str, budget: int, limit: int = 3) -> list:
    q = Component.query.filter_by(category='Motherboard').filter(Component.price <= budget)
    
    # Try form factor filter first
    if 'Micro' in form_factor:
        micro_mbs = q.filter(or_(
            Component.name.ilike('%micro%'),
            Component.name.ilike('%matx%'),
            Component.name.ilike('%m-atx%')
        )).order_by(Component.performance_score.desc()).limit(limit).all()
        if micro_mbs:
            return micro_mbs
    
    # Fallback: any motherboard
    return q.order_by(Component.performance_score.desc()).limit(limit).all()


def _find_compatible_ram(mb_comp: Component, budget: int, limit: int = 2) -> list:
    q = Component.query.filter_by(category='RAM').filter(Component.price <= budget)
    
    mb_mem = None
    try:
        specs = mb_comp.specs or {}
        compat = mb_comp.compatibility or {}
        mb_mem = specs.get('memory_type') or compat.get('memory_type')
    except Exception:
        pass
    
    # Try memory type match first
    if mb_mem:
        mem_type = str(mb_mem).lower()
        if 'ddr5' in mem_type:
            candidates = q.filter(Component.name.ilike('%ddr5%')).order_by(Component.performance_score.desc()).limit(limit).all()
            if candidates:
                return candidates
        elif 'ddr4' in mem_type:
            candidates = q.filter(Component.name.ilike('%ddr4%')).order_by(Component.performance_score.desc()).limit(limit).all()
            if candidates:
                return candidates
    
    # Fallback: try DDR5 first (more modern)
    candidates = q.filter(Component.name.ilike('%ddr5%')).order_by(Component.performance_score.desc()).limit(limit).all()
    if candidates:
        return candidates
    
    # Last fallback: any RAM
    return q.order_by(Component.performance_score.desc()).limit(limit).all()


def _find_ram(budget: int, limit: int = 2) -> list:
    q = Component.query.filter_by(category='RAM').filter(Component.price <= budget)
    return q.order_by(Component.performance_score.desc()).limit(limit).all()


def _select_gpu_for_scenario(tier: str, budget: int) -> Component:
    q = Component.query.filter_by(category='GPU').filter(Component.price <= budget)
    if not q.first():
        return None
    
    if 'Streaming' in tier or 'Creation' in tier:
        # Prefer high-end for streaming/creation
        return q.order_by(Component.performance_score.desc()).first()
    elif 'Gaming' in tier:
        # High performance for gaming
        return q.order_by(Component.performance_score.desc()).first()
    else:
        # Entry-level for office
        return q.order_by(Component.price.asc()).first()


def _select_cpu(tier: str, budget: int, prefer_amd: bool = False, prefer_intel: bool = False) -> Component:
    q = Component.query.filter_by(category='CPU').filter(Component.price <= budget)
    
    if prefer_amd:
        q = q.filter(or_(Component.name.ilike('%ryzen%'), Component.name.ilike('%amd%')))
    elif prefer_intel:
        q = q.filter(or_(Component.name.ilike('%intel%'), Component.name.ilike('%core%')))
    
    return q.order_by(Component.performance_score.desc()).first()


def _candidate_cpus(tier: str, budget: int, prefer_amd: bool, prefer_intel: bool, limit: int = 6) -> list:
    q = Component.query.filter_by(category='CPU').filter(Component.price <= budget)
    if prefer_amd:
        q = q.filter(or_(Component.name.ilike('%ryzen%'), Component.name.ilike('%amd%')))
    elif prefer_intel:
        q = q.filter(or_(Component.name.ilike('%intel%'), Component.name.ilike('%core%')))
    return q.order_by(Component.performance_score.desc()).limit(limit).all()


def _select_storage(budget: int) -> Component:
    q = Component.query.filter_by(category='Storage').filter(Component.price <= budget)
    comp = q.order_by(Component.performance_score.desc()).first()
    
    # Fallback: relax budget
    if not comp:
        q = Component.query.filter_by(category='Storage').filter(Component.price <= int(budget * 1.5))
        comp = q.order_by(Component.performance_score.desc()).first()
    
    return comp


def _select_cooling(style: str, budget: int) -> Component:
    q = Component.query.filter_by(category='Cooling').filter(Component.price <= budget)
    
    if 'Stealth' in style or 'Air' in style:
        # Air cooling preferred
        air_cooling = q.filter(~Component.name.ilike('%liquid%')).order_by(Component.price.desc()).first()
        if air_cooling:
            return air_cooling
        # Fallback: any cooling
        return q.order_by(Component.price.desc()).first()
    else:
        # Liquid cooling preferred
        liquid = q.filter(or_(Component.name.ilike('%liquid%'), Component.name.ilike('%aio%'))).order_by(Component.price.desc()).first()
        if liquid:
            return liquid
        # Fallback: any cooling
        return q.order_by(Component.price.desc()).first()


def _select_psu(budget: int) -> Component:
    q = Component.query.filter_by(category='PSU').filter(Component.price <= budget)
    comp = q.order_by(Component.price.desc()).first()
    
    # Fallback: relax budget
    if not comp:
        q = Component.query.filter_by(category='PSU').filter(Component.price <= int(budget * 1.5))
        comp = q.order_by(Component.price.desc()).first()
    
    return comp


def _select_case(form_factor: str, budget: int) -> Component:
    q = Component.query.filter_by(category='Case').filter(Component.price <= budget)
    
    if 'Micro' in form_factor:
        micro_cases = q.filter(or_(
            Component.name.ilike('%micro%'),
            Component.name.ilike('%matx%'),
            Component.name.ilike('%mini%')
        )).order_by(Component.price.desc()).first()
        if micro_cases:
            return micro_cases
    
    # Fallback: any case
    return q.order_by(Component.price.desc()).first()


def _select_psu_for_system(system_parts: dict, budget: int) -> Component:
    q = Component.query.filter_by(category='PSU').filter(Component.price <= budget)
    comp = q.order_by(Component.price.desc()).first()
    
    # Fallback: relax budget significantly
    if not comp:
        q = Component.query.filter_by(category='PSU').filter(Component.price <= int(budget * 2))
        comp = q.order_by(Component.price.desc()).first()
    
    return comp
