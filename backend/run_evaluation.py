"""Multi-seed batch evaluation. Shares the same ExperimentRunner / strategy
code path as app.py (the original kept two separately hand-rolled loops).
Usage:  python run_evaluation.py [--edges]"""
import json
import sys
import time
import numpy as np

from compiler.circuits import build_logical_circuit
from compiler.topology import build_topology
from calibration.synthetic import SyntheticCalibrationProvider
from execution.experiment import ExperimentRunner
from execution.strategies import run_static, run_full_retranspile
from metrics.metrics import compute_strategy_metrics, compute_incremental_metrics

N_LOG, N_PHYS, N_STEPS = 4, 8, 25
SEEDS = [7, 11, 23, 42, 99]


def main(detect_edges: bool = False, out_path: str = "real_results.json"):
    qc = build_logical_circuit(N_LOG)
    n_main = max(3, N_LOG, N_PHYS // 2)
    coupling, edges = build_topology(N_PHYS, n_main=n_main)
    per_seed = {"static": [], "full": [], "incremental": []}
    inc_extra, eq_pass, eq_fail, fallback_log = [], 0, 0, []
    t0 = time.time()
    for seed in SEEDS:
        seq = SyntheticCalibrationProvider(coupling.number_of_nodes(), edges, seed=seed).sequence(N_STEPS)
        runner = ExperimentRunner(threshold=0.35, detect_edges=detect_edges)
        r_s = run_static(qc, coupling, seq, seed)
        r_f = run_full_retranspile(qc, coupling, seq, seed)
        r_i = runner.run_incremental_strategy(qc, coupling, seq, seed)
        for name, r in (("static", r_s), ("full", r_f), ("incremental", r_i)):
            m = compute_strategy_metrics(r)
            per_seed[name].append({"seed": seed, **{k: m[k] for k in
                                   ("mean_fidelity", "total_cost", "num_recompiles", "gini_usage")}})
        extra = compute_incremental_metrics(r_i, N_STEPS)
        extra["seed"] = seed
        inc_extra.append(extra)
        eq_pass += sum(1 for c in r_i["equivalence_checks"] if c)
        eq_fail += sum(1 for c in r_i["equivalence_checks"] if not c)
        fallback_log += [l for l in r_i["log"] if "fallback" in l]
        print(f"seed {seed} done ({time.time()-t0:.1f}s)")

    summary = {}
    for name, rows in per_seed.items():
        summary[name] = {
            "mean_fidelity": float(np.mean([r["mean_fidelity"] for r in rows])),
            "mean_total_cost": float(np.mean([r["total_cost"] for r in rows])),
            "mean_gini": float(np.mean([r["gini_usage"] for r in rows])),
            "per_seed": rows,
        }
    summary["incremental_repair_per_seed"] = inc_extra
    summary["equivalence_checks"] = {"passed": eq_pass, "failed_and_fell_back": eq_fail}
    summary["fallback_log"] = fallback_log
    summary["config"] = {"n_log": N_LOG, "n_phys": coupling.number_of_nodes(), "n_steps": N_STEPS,
                         "seeds": SEEDS, "detect_edges": detect_edges,
                         "calibration": "synthetic seeded random walk"}
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    for name in ("static", "full", "incremental"):
        s = summary[name]
        print(f"{name:12s} fidelity={s['mean_fidelity']:.4f} cost={s['mean_total_cost']:7.1f} gini={s['mean_gini']:.4f}")
    local = sum(e["local_patch_count"] for e in inc_extra)
    fb = sum(e["full_fallback_count"] for e in inc_extra)
    drift = sum(e["drift_event_count"] for e in inc_extra)
    print(f"drift events={drift} local patches={local} fallbacks={fb} "
          f"mean preservation={np.mean([e['mean_preservation_ratio'] for e in inc_extra]):.3f}")


if __name__ == "__main__":
    main(detect_edges="--edges" in sys.argv)
