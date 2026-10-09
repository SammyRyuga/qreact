"""
Immutable calibration data model.

A CalibrationSnapshot is a frozen, point-in-time record of per-qubit and
per-edge error metrics. It never mutates after creation -- the random-walk
drift behavior lives in the *provider* (see synthetic.py), which emits a
NEW snapshot each step rather than mutating an existing one in place. This
replaces the original CalibrationSource, which conflated "the current
calibration state" with "the stateful RNG stream that evolves it," and
which callers had to externally `copy.deepcopy()` just to keep a history
of past snapshots around safely.
"""
from __future__ import annotations
from types import MappingProxyType
import numpy as np


def _canon(a: int, b: int) -> tuple:
    return (a, b) if a <= b else (b, a)


class CalibrationSnapshot:
    """
    Read-only calibration state.

    - readout_err, gate_err_1q: numpy arrays indexed by physical qubit,
      explicitly marked read-only (`setflags(write=False)`) so accidental
      in-place mutation raises instead of silently corrupting a snapshot
      some earlier step is still holding a reference to.
    - gate_err_2q: a read-only mapping (MappingProxyType) keyed by a
      canonical (min, max) physical-qubit edge tuple.
    """

    def __init__(self, step: int, n_qubits: int, edges, readout_err, gate_err_1q, gate_err_2q):
        readout_err = np.array(readout_err, dtype=float)
        gate_err_1q = np.array(gate_err_1q, dtype=float)
        readout_err.setflags(write=False)
        gate_err_1q.setflags(write=False)
        self.step = step
        self.n_qubits = n_qubits
        self.edges = tuple(_canon(a, b) for (a, b) in edges)
        self.readout_err = readout_err
        self.gate_err_1q = gate_err_1q
        self._gate_err_2q = MappingProxyType({_canon(a, b): float(v) for (a, b), v in gate_err_2q.items()})

    @property
    def gate_err_2q(self) -> MappingProxyType:
        return self._gate_err_2q

    def edge_err(self, a: int, b: int) -> float:
        """Matches the original CalibrationSource.edge_err fallback behavior
        exactly: 0.05 for an edge with no recorded calibration."""
        return self._gate_err_2q.get(_canon(a, b), 0.05)

    def qubit_error(self, q: int) -> float:
        """Combined scalar error metric for a physical qubit. Several
        places in the original code computed `readout_err[q] + gate_err_1q[q]`
        inline and repeatedly; this is the single canonical definition."""
        return float(self.readout_err[q] + self.gate_err_1q[q])

    def __repr__(self) -> str:
        return f"CalibrationSnapshot(step={self.step}, n_qubits={self.n_qubits})"
