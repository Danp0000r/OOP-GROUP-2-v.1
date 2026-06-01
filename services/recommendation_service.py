"""
Recommendation service — suggests compatible components based on
what the user has already picked and their stated budget.
"""
from services.cache import memoize
from models.cpu      import CPU
from models.gpu      import GPU
from models.ram      import RAM
from models.motherboard import Motherboard
from models.psu      import PSU
from models.storage  import Storage
from models.cooling  import Cooling
from models.case     import Case


@memoize(timeout=300)
def recommend_motherboard(cpu: CPU, budget: int = None) -> list:
    """Return motherboards compatible with the given CPU socket and memory type."""
    q = Motherboard.query.filter_by(socket=cpu.socket, memory_type=cpu.memory_type)
    if budget:
        q = q.filter(Motherboard.price <= budget)
    return q.order_by(Motherboard.price).limit(3).all()


@memoize(timeout=300)
def recommend_ram(cpu: CPU, motherboard: Motherboard, budget: int = None) -> list:
    """Return RAM kits matching the CPU/MB memory type."""
    q = RAM.query.filter_by(memory_type=cpu.memory_type)
    if budget:
        q = q.filter(RAM.price <= budget)
    return q.order_by(RAM.price).limit(3).all()


@memoize(timeout=300)
def recommend_cooling(cpu: CPU, budget: int = None) -> list:
    """Return coolers that can handle the CPU TDP."""
    q = Cooling.query.filter(Cooling.tdp_rating >= (cpu.tdp or 65))
    if budget:
        q = q.filter(Cooling.price <= budget)
    return q.order_by(Cooling.price).limit(3).all()


@memoize(timeout=300)
def recommend_psu(total_tdp: int, budget: int = None) -> list:
    """Return PSUs with 20 % headroom over the estimated system TDP."""
    min_watts = int(total_tdp * 1.2)
    q = PSU.query.filter(PSU.wattage >= min_watts)
    if budget:
        q = q.filter(PSU.price <= budget)
    return q.order_by(PSU.wattage).limit(3).all()


@memoize(timeout=300)
def recommend_gpu(budget: int = None) -> list:
    """Return best-value GPUs sorted by VRAM then price."""
    q = GPU.query
    if budget:
        q = q.filter(GPU.price <= budget)
    return q.order_by(GPU.vram_gb.desc(), GPU.price).limit(3).all()


@memoize(timeout=300)
def full_recommendation(cpu_id: int, budget: int) -> dict:
    """
    Given a chosen CPU and total budget, return a recommended component
    set for every remaining slot.

    Returns a dict keyed by category, each value a list of Component dicts.
    """
    cpu = CPU.get_by_id(cpu_id)
    remaining = budget - cpu.price
    # rough budget split (percentages of remaining)
    splits = {
        "Motherboard": 0.20,
        "RAM":         0.10,
        "GPU":         0.35,
        "Storage":     0.10,
        "PSU":         0.10,
        "Cooling":     0.08,
        "Case":        0.07,
    }
    budgets = {k: int(remaining * v) for k, v in splits.items()}
    result = {}
    result["Motherboard"] = [m.to_dict() for m in recommend_motherboard(cpu, budgets["Motherboard"])]
    result["RAM"]         = [r.to_dict() for r in recommend_ram(cpu, None, budgets["RAM"])]
    result["GPU"]         = [g.to_dict() for g in recommend_gpu(budgets["GPU"])]
    result["Storage"]     = [s.to_dict() for s in Storage.query.filter(Storage.price <= budgets["Storage"]).order_by(Storage.read_speed.desc()).limit(3).all()]
    result["PSU"]         = [p.to_dict() for p in recommend_psu(150, budgets["PSU"])]
    result["Cooling"]     = [c.to_dict() for c in recommend_cooling(cpu, budgets["Cooling"])]
    result["Case"]        = [c.to_dict() for c in Case.query.filter(Case.price <= budgets["Case"]).order_by(Case.price).limit(3).all()]
    return result
