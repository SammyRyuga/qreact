"""Topology-level verification checks: coupling-edge validity and
logical<->physical mapping bijectivity."""
from __future__ import annotations


def check_adjacency(circuit, coupling_graph) -> tuple:
    """Every two-qubit operation must sit on a real coupling-graph edge.
    Unchanged logic from the original _adjacency_ok, now returning the
    specific violations instead of a bare bool."""
    violations = []
    for instr in circuit.data:
        if len(instr.qubits) == 2:
            a = circuit.find_bit(instr.qubits[0]).index
            b = circuit.find_bit(instr.qubits[1]).index
            if not coupling_graph.has_edge(a, b):
                violations.append(f"{instr.operation.name} on physical ({a},{b}) is not a coupling-graph edge")
    return (len(violations) == 0, violations)


def check_mapping_bijective(layout: dict) -> tuple:
    """Logical->physical mapping must be injective (no two logical qubits
    sharing one physical qubit) over the active logical qubits."""
    physical = list(layout.values())
    if len(set(physical)) == len(physical):
        return (True, [])
    seen, dupes = {}, []
    for lq, pq in layout.items():
        if pq in seen:
            dupes.append(f"logical {seen[pq]} and logical {lq} both map to physical {pq}")
        seen[pq] = lq
    return (False, dupes)
