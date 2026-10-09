"""
RepairRegionBuilder: converts a DriftEvent into an explicit, BOUNDED
RepairRegion, derived from BOTH hardware locality (coupling-graph BFS) and
compiled-circuit locality (which operations actually touch the affected
resources).

Per the approved Phase 2 correction (#2): EVERY operation in the compiled
artifact is classified -- interior / boundary / outside -- as part of
region construction, BEFORE any repair candidate is generated. An
operation whose physical operands are entirely inside the region's
physical-qubit set is `affected_operation_ids` (interior, safe to
modify). An operation that touches the region but ALSO touches a physical
qubit outside it is `boundary_operation_ids` -- it interacts with the
region but is NOT modifiable by any candidate unless the region is
explicitly expanded, which v1 does not do (see README "Known
Limitations" -- no progressive-retry-with-larger-region escalation path
is implemented, by design: a region that doesn't fit goes straight to
full-retranspile fallback).

The builder has explicit, enforced bounds (max radius, max operations,
max qubits). Exceeding any of them produces a structured "region too
large" result (`too_large=True`) rather than a partial/best-effort region
-- callers must route this straight to FallbackController.
"""
from __future__ import annotations
from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class RepairRegion:
    region_id: str
    physical_qubits: tuple
    affected_logical_qubits: tuple
    affected_operation_ids: tuple        # INTERIOR: the only operations a candidate may modify
    boundary_operation_ids: tuple        # touches the region but also touches outside it -- NOT modifiable
    region_edges: tuple
    radius: int
    region_size: int
    region_fraction: float               # region_size / total physical qubits in the device
    reason: str
    too_large: bool = False


class RepairRegionBuilder:
    def __init__(self, max_radius: int = 2, max_operations: int = 24, max_qubits: int = 6):
        self.max_radius = max_radius
        self.max_operations = max_operations
        self.max_qubits = max_qubits

    def build(self, artifact, drift_event) -> RepairRegion:
        coupling = artifact.coupling_graph
        drifted_phys = set(drift_event.drifted_qubits)
        for (a, b) in drift_event.drifted_edges:
            drifted_phys.add(a)
            drifted_phys.add(b)

        neighbourhood, radius_used = _bounded_bfs(coupling, drifted_phys, self.max_radius, self.max_qubits)
        region_id = f"region-g{artifact.generation}-s{drift_event.step}"
        n_phys_total = coupling.number_of_nodes()

        if len(neighbourhood) > self.max_qubits:
            return _too_large_region(region_id, neighbourhood, radius_used, n_phys_total,
                                      "region_too_large: physical-qubit bound exceeded")

        # Compiled-circuit locality: classify EVERY operation now, before
        # any candidate exists (Correction 2).
        affected_ids, boundary_ids = [], []
        for op in artifact.operations:
            touched = [p for p in op.physical_qubits if p in neighbourhood]
            if not touched:
                continue
            fully_inside = len(touched) == len(op.physical_qubits)
            (affected_ids if fully_inside else boundary_ids).append(op.node_id)

        if len(affected_ids) > self.max_operations:
            return _too_large_region(region_id, neighbourhood, radius_used, n_phys_total,
                                      "region_too_large: operation-count bound exceeded")

        region_edges = tuple(
            (a, b) for (a, b) in coupling.edges() if a in neighbourhood and b in neighbourhood
        )
        affected_logical = tuple(sorted(
            lq for lq, pq in artifact.layout.items() if pq in neighbourhood
        ))

        return RepairRegion(
            region_id=region_id, physical_qubits=tuple(sorted(neighbourhood)),
            affected_logical_qubits=affected_logical,
            affected_operation_ids=tuple(affected_ids), boundary_operation_ids=tuple(boundary_ids),
            region_edges=region_edges, radius=radius_used, region_size=len(neighbourhood),
            region_fraction=len(neighbourhood) / n_phys_total,
            reason="hardware_locality+circuit_locality", too_large=False,
        )


def _bounded_bfs(coupling, seed_qubits: set, max_radius: int, max_qubits: int):
    neighbourhood = set(seed_qubits)
    frontier = set(seed_qubits)
    radius_used = 0
    for hop in range(1, max_radius + 1):
        nxt = set()
        for q in frontier:
            nxt |= set(coupling.neighbors(q))
        nxt -= neighbourhood
        if not nxt:
            break
        neighbourhood |= nxt
        frontier = nxt
        radius_used = hop
        if len(neighbourhood) >= max_qubits:
            break
    return neighbourhood, radius_used


def _too_large_region(region_id, neighbourhood, radius_used, n_phys_total, reason) -> RepairRegion:
    return RepairRegion(
        region_id=region_id, physical_qubits=tuple(sorted(neighbourhood)),
        affected_logical_qubits=(), affected_operation_ids=(), boundary_operation_ids=(),
        region_edges=(), radius=radius_used, region_size=len(neighbourhood),
        region_fraction=len(neighbourhood) / n_phys_total, reason=reason, too_large=True,
    )
