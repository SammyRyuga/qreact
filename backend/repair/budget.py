"""
DisruptionBudget answers a DIFFERENT question than DriftDetector's
threshold:

    DriftDetector.threshold -- "Has the hardware changed enough to
                                require ANY action at all?"
    DisruptionBudget        -- "Is this particular LOCAL REPAIR small
                                enough to be considered incremental?"

These must never be conflated, in code or in logs: a drift event can be
real and still have no acceptably small repair (region_too_large /
budget exceeded), in which case the system falls back to a full
retranspile -- that is not a contradiction, it is the budget doing its job.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class DisruptionBudget:
    max_region_qubits: int = 6
    max_region_operations: int = 24
    max_changed_operations: int = 12
    max_added_swaps: int = 2
    max_depth_increase: int = 4
    max_changed_physical_qubits: int = 4
    max_candidate_count: int = 3
    max_topology_radius: int = 2

    def check(self, candidate, region) -> tuple:
        violations = []
        if region.region_size > self.max_region_qubits:
            violations.append(
                f"region_size {region.region_size} exceeds max_region_qubits {self.max_region_qubits}")
        if len(region.affected_operation_ids) > self.max_region_operations:
            violations.append(
                f"region operations {len(region.affected_operation_ids)} exceeds "
                f"max_region_operations {self.max_region_operations}")
        if len(candidate.changed_operation_ids) > self.max_changed_operations:
            violations.append(
                f"changed_operations {len(candidate.changed_operation_ids)} exceeds "
                f"max_changed_operations {self.max_changed_operations}")
        if len(candidate.inserted_swaps) > self.max_added_swaps:
            violations.append(
                f"added swaps {len(candidate.inserted_swaps)} exceeds max_added_swaps {self.max_added_swaps}")
        if candidate.estimated_depth_delta > self.max_depth_increase:
            violations.append(
                f"depth increase {candidate.estimated_depth_delta} exceeds "
                f"max_depth_increase {self.max_depth_increase}")
        if len(candidate.touched_physical_qubits) > self.max_changed_physical_qubits:
            violations.append(
                f"changed physical qubits {len(candidate.touched_physical_qubits)} exceeds "
                f"max_changed_physical_qubits {self.max_changed_physical_qubits}")
        if region.radius > self.max_topology_radius:
            violations.append(f"region radius {region.radius} exceeds max_topology_radius {self.max_topology_radius}")
        return (len(violations) == 0, violations)
