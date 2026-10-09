"""Static and Full-Retranspile baseline strategies -- unchanged behavior
from the original prototype, refactored only to share compile_baseline()/
extract_layout() instead of each independently re-deriving the same
pinned-layout transpile call."""
from __future__ import annotations
import numpy as np
from qiskit import transpile

from compiler.compilation import compile_baseline, extract_layout
from drift.detector import DriftDetector
from .simulation import simulate_fidelity


def run_static(logical_qc, coupling, calib_sequence, seed: int):
    compiled, cmap = compile_baseline(logical_qc, coupling, seed)
    layout = extract_layout(compiled, logical_qc.num_qubits)
    fids, costs, usage = [], [], np.zeros(coupling.number_of_nodes())
    first = True
    for snap in calib_sequence:
        cost = logical_qc.num_qubits * coupling.number_of_nodes() if first else 0
        first = False
        fids.append(simulate_fidelity(compiled, snap, layout))
        costs.append(cost)
        for p in set(layout.values()):
            usage[p] += 1
    return {"fidelities": fids, "costs": costs, "usage": usage.tolist(), "num_recompiles": 1}


def run_full_retranspile(logical_qc, coupling, calib_sequence, seed: int, threshold: float = 0.35):
    compiled, cmap = compile_baseline(logical_qc, coupling, seed)
    layout = extract_layout(compiled, logical_qc.num_qubits)
    # detect_edges=False: matches the original project's qubit-only drift
    # behavior exactly for this baseline strategy (see tests/test_drift.py).
    detector = DriftDetector(threshold=threshold, detect_edges=False)
    baseline_snap = calib_sequence[0]
    fids, costs, usage = [], [], np.zeros(coupling.number_of_nodes())
    num_recompiles = 1
    for i, snap in enumerate(calib_sequence):
        cost = 0
        if i > 0:
            event = detector.detect(snap, baseline_snap, layout.values(), [], step=i)
            if event.has_drift:
                compiled = transpile(logical_qc, coupling_map=cmap, optimization_level=1, seed_transpiler=seed + i)
                layout = extract_layout(compiled, logical_qc.num_qubits)
                baseline_snap = snap
                cost = logical_qc.num_qubits * coupling.number_of_nodes()
                num_recompiles += 1
        fids.append(simulate_fidelity(compiled, snap, layout))
        costs.append(cost)
        for p in set(layout.values()):
            usage[p] += 1
    return {"fidelities": fids, "costs": costs, "usage": usage.tolist(), "num_recompiles": num_recompiles}
