"""
Semantic equivalence verification.

ExactMeasurementDistributionVerifier reproduces the original project's
exact-Statevector logical measurement-distribution comparison exactly --
see its docstring below for why this specific comparison, not a raw
full-width Operator/statevector comparison, is the correct check once two
circuits may place the same logical qubits on different physical qubits.

SemanticVerifier is an abstract base so future verification strategies
(Operator-based, randomized test states, stabilizer-based, shot-based
statistical equivalence) can be added later without changing anything
that calls into this module.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np
from qiskit.quantum_info import Statevector

# Circuits above this size are not exactly simulated -- see
# SemanticVerificationResult.available.
DEFAULT_MAX_EXACT_QUBITS = 22


@dataclass(frozen=True)
class SemanticVerificationResult:
    available: bool           # False => "verification_unavailable" -- NOT "assumed passed"
    equivalent: bool | None   # None when not available
    reason: str


class SemanticVerifier(ABC):
    @abstractmethod
    def verify(self, circ_a, layout_a, circ_b, layout_b, n_log, atol=1e-6,
               input_layout_a=None, input_layout_b=None) -> SemanticVerificationResult:
        raise NotImplementedError


class ExactMeasurementDistributionVerifier(SemanticVerifier):
    """
    Compares the EXACT (statevector, not shot-sampled) logical
    measurement-outcome distribution of two compiled circuits, each read
    off through ITS OWN layout. This is the original project's
    `unitary_equivalent` / `_exact_logical_distribution`, unchanged
    mathematically.

    Why "through its own layout" matters: circ_a and circ_b may place the
    same logical qubits on different physical qubits. A raw, full-width
    Operator/statevector comparison across the two would see them as
    "different" purely because of that relabeling, even when they compute
    the identical logical function -- that was a real bug this project
    already hit and fixed once. Reading probabilities via
    `sv.probabilities(qargs=[layout[i] for i in range(n_log)])` sidesteps
    it by comparing in logical-qubit order on both sides.
    """

    def __init__(self, max_exact_qubits: int = DEFAULT_MAX_EXACT_QUBITS):
        self.max_exact_qubits = max_exact_qubits

    def verify(self, circ_a, layout_a, circ_b, layout_b, n_log, atol=1e-6,
               input_layout_a=None, input_layout_b=None) -> SemanticVerificationResult:
        n_qubits = max(circ_a.num_qubits, circ_b.num_qubits)
        if n_qubits > self.max_exact_qubits:
            return SemanticVerificationResult(
                available=False, equivalent=None,
                reason=f"verification_unavailable: {n_qubits} qubits exceeds exact-simulation limit "
                       f"({self.max_exact_qubits}); refusing to assume equivalence",
            )
        try:
            pa = _exact_logical_distribution(circ_a, layout_a, n_log)
            pb = _exact_logical_distribution(circ_b, layout_b, n_log)
        except Exception as exc:
            return SemanticVerificationResult(
                available=False, equivalent=None,
                reason=f"verification_unavailable: exact simulation raised {type(exc).__name__}: {exc}",
            )
        equivalent = bool(np.allclose(pa, pb, atol=atol))
        return SemanticVerificationResult(
            available=True, equivalent=equivalent,
            reason="exact logical measurement distributions match" if equivalent
                   else "exact logical measurement distributions differ",
        )


def _exact_logical_distribution(circ, layout, n_log):
    circ_no_meas = circ.remove_final_measurements(inplace=False)
    sv = Statevector.from_instruction(circ_no_meas)
    qargs = [layout[i] for i in range(n_log)]
    return sv.probabilities(qargs=qargs)


class RandomizedInputStateVerifier(SemanticVerifier):
    """
    Compares exact logical measurement distributions after preparing
    SEEDED, RANDOM product input states on the logical qubits.

    Why this exists: the project's benchmark circuit (H on every qubit,
    a CX cascade, RZ, measure) has an exactly UNIFORM output distribution
    when started from |0...0>, because a CX cascade is a basis-state
    permutation and RZ is diagonal. A check that only ever feeds in
    |0...0> therefore cannot distinguish many wrong rewrites from correct
    ones. Random input states break that symmetry, so a mis-wired or
    dropped gate changes the output distribution and is caught.

    Each circuit's input is placed on ITS OWN input layout (where the
    logical qubit's input lives -- which differs from the output layout
    once SWAPs or a relabel are involved) and read out through ITS OWN
    output layout, so physical relabeling never causes a false mismatch.
    The random angles are deterministic given `seed`.
    """

    def __init__(self, trials: int = 3, seed: int = 20260101, max_exact_qubits: int = DEFAULT_MAX_EXACT_QUBITS):
        self.trials = trials
        self.seed = seed
        self.max_exact_qubits = max_exact_qubits

    def verify(self, circ_a, layout_a, circ_b, layout_b, n_log, atol=1e-6,
               input_layout_a=None, input_layout_b=None) -> SemanticVerificationResult:
        n_qubits = max(circ_a.num_qubits, circ_b.num_qubits)
        if n_qubits > self.max_exact_qubits:
            return SemanticVerificationResult(
                available=False, equivalent=None,
                reason=f"verification_unavailable: {n_qubits} qubits exceeds exact-simulation limit")
        in_a = input_layout_a if input_layout_a is not None else layout_a
        in_b = input_layout_b if input_layout_b is not None else layout_b
        rng = np.random.RandomState(self.seed)
        try:
            for _ in range(self.trials):
                angles = [(rng.uniform(0.3, 2.8), rng.uniform(0.0, 6.28)) for _ in range(n_log)]
                pa = _prepared_logical_distribution(circ_a, in_a, layout_a, n_log, angles)
                pb = _prepared_logical_distribution(circ_b, in_b, layout_b, n_log, angles)
                if not np.allclose(pa, pb, atol=atol):
                    return SemanticVerificationResult(
                        available=True, equivalent=False,
                        reason="randomized-input logical distributions differ")
        except Exception as exc:
            return SemanticVerificationResult(
                available=False, equivalent=None,
                reason=f"verification_unavailable: randomized check raised {type(exc).__name__}: {exc}")
        return SemanticVerificationResult(
            available=True, equivalent=True,
            reason=f"randomized-input logical distributions match over {self.trials} trials")


class CompositeSemanticVerifier(SemanticVerifier):
    """Requires EVERY component verifier to pass. If any component is
    unavailable the composite is unavailable (never silently skipped)."""

    def __init__(self, verifiers=None):
        self.verifiers = verifiers or [ExactMeasurementDistributionVerifier(), RandomizedInputStateVerifier()]

    def verify(self, circ_a, layout_a, circ_b, layout_b, n_log, atol=1e-6,
               input_layout_a=None, input_layout_b=None) -> SemanticVerificationResult:
        reasons = []
        for v in self.verifiers:
            r = v.verify(circ_a, layout_a, circ_b, layout_b, n_log, atol,
                         input_layout_a=input_layout_a, input_layout_b=input_layout_b)
            if not r.available:
                return r
            if not r.equivalent:
                return r
            reasons.append(r.reason)
        return SemanticVerificationResult(available=True, equivalent=True, reason=" | ".join(reasons))


def _prepared_logical_distribution(circ, in_layout, out_layout, n_log, angles):
    from qiskit import QuantumCircuit
    nm = circ.remove_final_measurements(inplace=False)
    prep = QuantumCircuit(nm.num_qubits)
    for i in range(n_log):
        theta, phi = angles[i]
        prep.ry(theta, in_layout[i])
        prep.rz(phi, in_layout[i])
    full = prep.compose(nm)
    sv = Statevector.from_instruction(full)
    return sv.probabilities(qargs=[out_layout[i] for i in range(n_log)])
