"""
Shared metrics -- the canonical `gini()` (deduped: the original prototype
had two separate copies, in app.py and run_evaluation.py), plus the
expanded metric set requested in Phase 2 item 16.

Every number here is computed from an actual run's recorded fields
(`fidelities`, `costs`, `usage`, `num_recompiles`, `num_local_patches`,
`num_fallbacks`, `equivalence_checks`) -- nothing is estimated or assumed
favorably. See execution/experiment.py for where these counters are
produced.
"""
from __future__ import annotations
import numpy as np


def gini(x) -> float:
    x = np.array(sorted(x), dtype=float)
    n = len(x)
    if x.sum() == 0:
        return 0.0
    cum = np.cumsum(x)
    return (n + 1 - 2 * np.sum(cum) / cum[-1]) / n


def compute_strategy_metrics(result: dict) -> dict:
    """Metrics common to all three strategies (static, full, incremental)."""
    fids = result["fidelities"]
    costs = result["costs"]
    usage = result["usage"]
    return {
        "mean_fidelity": float(np.mean(fids)),
        "total_cost": float(sum(costs)),
        "num_recompiles": result["num_recompiles"],
        "gini_usage": gini(usage),
        "active_qubit_count": int(sum(1 for u in usage if u > 0)),
        "peak_qubit_usage": float(max(usage)) if usage else 0.0,
        "mean_usage": float(np.mean(usage)) if usage else 0.0,
        "usage_distribution": [float(u) for u in usage],
    }


def compute_incremental_metrics(result: dict, n_steps: int) -> dict:
    """Metrics specific to the incremental strategy's repair pipeline.
    Uses explicit counters recorded during the run (`num_local_patches`,
    `num_fallbacks`, `drift_event_count`) rather than re-deriving them
    arithmetically from num_recompiles, which would silently miscount a
    fallback that occurred with zero candidates generated (no
    equivalence-check entry recorded for it)."""
    eq = result.get("equivalence_checks", [])
    n_pass = sum(1 for c in eq if c)
    n_fail = len(eq) - n_pass
    n_local = result.get("num_local_patches", n_pass)
    n_fallback = result.get("num_fallbacks", 0)
    drift_events = result.get("drift_event_count", n_local + n_fallback)
    region_sizes = result.get("region_sizes", [])
    region_fractions = result.get("region_fractions", [])
    changed_op_counts = result.get("changed_operation_counts", [])
    preservation_ratios = result.get("preservation_ratios", [])
    added_swaps = result.get("added_swaps_counts", [])
    depth_deltas = result.get("depth_deltas", [])

    def _mean(xs):
        return float(np.mean(xs)) if xs else 0.0

    return {
        "patch_acceptance_rate": (n_local / drift_events) if drift_events else 0.0,
        "local_patch_count": n_local,
        "full_fallback_count": n_fallback,
        "drift_event_count": drift_events,
        "mean_region_size": _mean(region_sizes),
        "mean_region_fraction": _mean(region_fractions),
        "mean_changed_operations": _mean(changed_op_counts),
        "mean_preservation_ratio": _mean(preservation_ratios),
        "mean_added_swaps": _mean(added_swaps),
        "mean_depth_delta": _mean(depth_deltas),
        "verification_pass_rate": (n_pass / len(eq)) if eq else 0.0,
        "verification_failure_rate": (n_fail / len(eq)) if eq else 0.0,
        "fallback_rate": (n_fallback / n_steps) if n_steps else 0.0,
    }


def compute_comparative_metrics(static_m: dict, full_m: dict, incremental_m: dict) -> dict:
    return {
        "fidelity_delta_vs_static": incremental_m["mean_fidelity"] - static_m["mean_fidelity"],
        "fidelity_delta_vs_full": incremental_m["mean_fidelity"] - full_m["mean_fidelity"],
        "cost_savings_vs_full": (
            (full_m["total_cost"] - incremental_m["total_cost"]) / full_m["total_cost"]
            if full_m["total_cost"] else 0.0
        ),
    }
