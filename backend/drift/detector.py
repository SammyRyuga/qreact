"""
DriftDetector: compares a current CalibrationSnapshot against the snapshot
a compiled artifact's physical resources were last validated against, and
flags resources -- qubits AND edges -- whose relative error change exceeds
a configurable threshold.

This extends the original `_drifted_logical`, which only ever inspected
per-qubit error (readout + 1Q gate error) and never inspected 2Q/edge
error, even though the calibration model has always drifted edges too.
Qubit-only detection reproduces the original behavior exactly when
`detect_edges=False` (see tests/test_drift.py); edge detection is new,
additive capability.

Deliberately works in PHYSICAL resource terms, not logical ones: drift is
fundamentally a property of hardware, not of which logical qubit currently
happens to sit on it. Translating "physical resource X drifted" into
"which logical qubits/operations does this affect" is the
RepairRegionBuilder's job (repair/region.py), not this detector's.
"""
from __future__ import annotations
from .models import DriftEvent, no_drift_event


class DriftDetector:
    def __init__(self, threshold: float = 0.35, detect_edges: bool = True, edge_threshold: float | None = None):
        """
        threshold: relative-change threshold for QUBIT metrics.
        edge_threshold: relative-change threshold for EDGE (2Q gate)
            metrics. Deliberately a SEPARATE parameter rather than reusing
            `threshold` for both channels: empirically, this project's
            synthetic calibration model drifts 2Q-gate error roughly 2x
            more volatile (relative to its own typical magnitude) than
            per-qubit error (see tests/test_drift.py for the measurement).
            Reusing one threshold for both channels is not a "stricter
            safety margin" -- it just makes edge-drift fire on nearly
            every step regardless of circuit relevance, exhausting the
            repair-region budget before any candidate is ever attempted.
            Defaults to `2 * threshold` to keep the two channels' trigger
            RATES comparable; always explicitly overridable.
        """
        self.threshold = threshold
        self.detect_edges = detect_edges
        self.edge_threshold = edge_threshold if edge_threshold is not None else threshold * 2.0

    def detect(self, current, baseline, physical_qubits, physical_edges, step: int) -> DriftEvent:
        """
        current, baseline: CalibrationSnapshot
        physical_qubits: iterable of physical qubits currently in use
        physical_edges: iterable of (a, b) physical edges currently used by
            a two-qubit operation in the compiled circuit
        """
        drifted_qubits = []
        qubit_delta = {}
        for q in physical_qubits:
            cur = current.qubit_error(q)
            base = baseline.qubit_error(q)
            delta = _relative_delta(cur, base)
            if delta > self.threshold:
                drifted_qubits.append(q)
                qubit_delta[q] = delta

        drifted_edges = []
        edge_delta = {}
        if self.detect_edges:
            for (a, b) in physical_edges:
                cur = current.edge_err(a, b)
                base = baseline.edge_err(a, b)
                delta = _relative_delta(cur, base)
                if delta > self.edge_threshold:
                    drifted_edges.append((a, b))
                    edge_delta[(a, b)] = delta

        if not drifted_qubits and not drifted_edges:
            return no_drift_event(step, self.threshold)

        affected = tuple(drifted_qubits) + tuple(drifted_edges)
        return DriftEvent(
            step=step, drifted_qubits=tuple(drifted_qubits), drifted_edges=tuple(drifted_edges),
            qubit_delta_by_resource=qubit_delta, edge_delta_by_resource=edge_delta,
            threshold=self.threshold, trigger_reason="relative_calibration_change",
            affected_resources=affected,
        )


def _relative_delta(current: float, baseline: float) -> float:
    if baseline <= 0:
        return 0.0
    return abs(current - baseline) / baseline
