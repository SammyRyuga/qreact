"""
Synthetic calibration provider: a reproducible, seeded random-walk model of
device drift. This is the ONLY calibration source in this codebase --
clearly labeled as synthetic throughout the README and API, never implied
to be live telemetry.

Numerically, `advance()` replicates the original CalibrationSource.step()
exactly: same RNG call order, same distributions, same periodic
recalibration rule every 8th step by default. This is deliberate -- see
tests/test_calibration.py, which checks that a fixed seed reproduces the
exact original sequence of values.
"""
from __future__ import annotations
import numpy as np

from .models import CalibrationSnapshot
from .provider import CalibrationProvider


class SyntheticCalibrationProvider(CalibrationProvider):
    def __init__(self, n_qubits: int, edges, seed: int = 7, recalibration_period: int = 8):
        self.n_qubits = n_qubits
        self.edges = list(edges)
        self.recalibration_period = recalibration_period
        self._rng = np.random.RandomState(seed)
        self._readout_err = self._rng.uniform(0.01, 0.04, n_qubits)
        self._gate_err_1q = self._rng.uniform(0.0005, 0.003, n_qubits)
        self._gate_err_2q = {e: self._rng.uniform(0.005, 0.03) for e in self.edges}
        self._t = 0

    def get_snapshot(self) -> CalibrationSnapshot:
        return CalibrationSnapshot(
            step=self._t, n_qubits=self.n_qubits, edges=self.edges,
            readout_err=self._readout_err, gate_err_1q=self._gate_err_1q,
            gate_err_2q=self._gate_err_2q,
        )

    def advance(self) -> CalibrationSnapshot:
        self._t += 1
        self._readout_err = np.clip(self._readout_err + self._rng.normal(0, 0.004, self.n_qubits), 0.005, 0.08)
        self._gate_err_1q = np.clip(self._gate_err_1q + self._rng.normal(0, 0.0003, self.n_qubits), 0.0002, 0.01)
        for e in self.edges:
            self._gate_err_2q[e] = float(np.clip(self._gate_err_2q[e] + self._rng.normal(0, 0.003), 0.002, 0.08))
        if self._t % self.recalibration_period == 0:
            self._readout_err = self._rng.uniform(0.01, 0.04, self.n_qubits)
            self._gate_err_1q = self._rng.uniform(0.0005, 0.003, self.n_qubits)
            for e in self.edges:
                self._gate_err_2q[e] = float(self._rng.uniform(0.005, 0.03))
        return self.get_snapshot()

    def sequence(self, n_steps: int) -> list:
        """Convenience matching the original call-site pattern (both app.py
        and run_evaluation.py used to hand-roll this loop independently,
        with an external copy.deepcopy per step): n_steps snapshots, the
        first being the unmodified initial state, i.e. get_snapshot() once
        followed by advance() exactly (n_steps - 1) times."""
        seq = [self.get_snapshot()]
        for _ in range(n_steps - 1):
            seq.append(self.advance())
        return seq
