"""Logical circuit construction. Unchanged from the original prototype."""
from __future__ import annotations
from qiskit import QuantumCircuit


def build_logical_circuit(n_log: int = 4) -> QuantumCircuit:
    """A small circuit with real entangling structure -- forces real routing
    decisions. Unchanged from the original prototype."""
    qc = QuantumCircuit(n_log, n_log, name="logical_circuit")
    for q in range(n_log):
        qc.h(q)
    for i in range(n_log):
        for j in range(i + 1, n_log):
            qc.cx(i, j)
    for q in range(n_log):
        qc.rz(0.37, q)
    qc.measure(range(n_log), range(n_log))
    return qc
