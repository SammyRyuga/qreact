"""
RepairPatch: the explicit, first-class object representing "what changed
in response to this drift event."

Per the approved Phase 2 correction (#3), this carries enough EXACT delta
information to reconstruct what changed -- not merely before/after
layouts: `inserted_swaps` gives each inserted SWAP's position and physical
edge, `changed_operations` / `inserted_operations` / `removed_operations`
give the exact node_id-level diff.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class RepairPatch:
    patch_id: str
    source_artifact_version: int
    drift_event_step: int
    region_id: str
    candidate_type: str
    before_layout: dict
    after_layout: dict
    changed_operations: tuple          # node_ids whose physical_qubits changed
    inserted_operations: tuple         # node_ids of brand-new ops (e.g. SWAPs)
    removed_operations: tuple          # node_ids present before, absent after (empty for all v1 candidate types)
    changed_physical_qubits: tuple
    inserted_swaps: tuple              # tuple[SwapInsertion, ...] -- position + physical_edge + node_id
    estimated_cost: float
    verification_result: object        # VerificationResult
    accepted: bool
    fallback_reason: str | None = None

    def as_dict(self) -> dict:
        return {
            "patch_id": self.patch_id,
            "source_artifact_version": self.source_artifact_version,
            "drift_event_step": self.drift_event_step,
            "region_id": self.region_id,
            "candidate_type": self.candidate_type,
            "before_layout": dict(self.before_layout),
            "after_layout": dict(self.after_layout),
            "changed_operations": list(self.changed_operations),
            "inserted_operations": list(self.inserted_operations),
            "removed_operations": list(self.removed_operations),
            "changed_physical_qubits": list(self.changed_physical_qubits),
            "inserted_swaps": [
                {"position": s.position, "physical_edge": list(s.physical_edge), "node_id": s.node_id}
                for s in self.inserted_swaps
            ],
            "estimated_cost": self.estimated_cost,
            "accepted": self.accepted,
            "fallback_reason": self.fallback_reason,
        }


def patch_from_candidate(patch_id, source_artifact_version, before_layout, drift_event, region,
                          candidate, verification_result, accepted, fallback_reason=None) -> RepairPatch:
    return RepairPatch(
        patch_id=patch_id, source_artifact_version=source_artifact_version,
        drift_event_step=drift_event.step, region_id=region.region_id,
        candidate_type=candidate.candidate_type,
        before_layout=dict(before_layout), after_layout=dict(candidate.new_layout),
        changed_operations=candidate.changed_operation_ids,
        inserted_operations=tuple(s.node_id for s in candidate.inserted_swaps),
        removed_operations=(),
        changed_physical_qubits=candidate.touched_physical_qubits,
        inserted_swaps=candidate.inserted_swaps,
        estimated_cost=candidate.estimated_cost,
        verification_result=verification_result, accepted=accepted, fallback_reason=fallback_reason,
    )
