"""Structured drift representation -- replaces the original _drifted_logical,
which returned only a bare list of logical qubit indices with no magnitude,
no edges, and no stated reason."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DriftEvent:
    step: int
    drifted_qubits: tuple
    drifted_edges: tuple
    qubit_delta_by_resource: dict         # {physical_qubit: relative_delta}
    edge_delta_by_resource: dict           # {(a,b): relative_delta}
    threshold: float
    trigger_reason: str
    affected_resources: tuple              # mixed: ints (qubits) and (a,b) tuples (edges)

    @property
    def has_drift(self) -> bool:
        return bool(self.drifted_qubits) or bool(self.drifted_edges)

    def as_dict(self) -> dict:
        return {
            "step": self.step,
            "drifted_qubits": list(self.drifted_qubits),
            "drifted_edges": [list(e) for e in self.drifted_edges],
            "qubit_delta_by_resource": {str(k): v for k, v in self.qubit_delta_by_resource.items()},
            "edge_delta_by_resource": {f"{a}-{b}": v for (a, b), v in self.edge_delta_by_resource.items()},
            "threshold": self.threshold,
            "trigger_reason": self.trigger_reason,
            "affected_resources": [list(r) if isinstance(r, tuple) else r for r in self.affected_resources],
        }


def no_drift_event(step: int, threshold: float) -> DriftEvent:
    return DriftEvent(
        step=step, drifted_qubits=(), drifted_edges=(), qubit_delta_by_resource={},
        edge_delta_by_resource={}, threshold=threshold, trigger_reason="none", affected_resources=(),
    )
