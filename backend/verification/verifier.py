"""
RepairVerifier: the single place every candidate's safety is decided. No
placeholders, no hardcoded True, no "assume equivalent."

Performs, in this order (cheap/structural first, expensive simulation
last):

  1. topology_ok      -- every 2-qubit op sits on a coupling edge
  2. mapping_ok        -- logical->physical mapping is bijective
  3. locality_ok       -- every operation the candidate touches/changes was
                          already classified as INTERIOR to the region by
                          RepairRegionBuilder, BEFORE this candidate was
                          generated (Phase-2 Correction 2: a candidate may
                          not modify an operand of an operation that
                          preservation-checking treats as outside the
                          region)
  4. preservation_ok   -- everything outside the region is
                          structurally/semantically unchanged (see
                          verification/preservation.py for the exact
                          invariant)
  5. semantic_ok       -- exact logical measurement-distribution match.
                          None (not True/False) when verification was
                          unavailable; treated as FAILING, never as passed.
  6. disruption_ok     -- within the configured DisruptionBudget

A candidate is accepted only if every one of these is True (semantic_ok
must be exactly True, not merely "not False").
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .topology import check_adjacency, check_mapping_bijective
from .preservation import check_preservation, check_records_match_circuit
from .semantic import CompositeSemanticVerifier


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    topology_ok: bool
    mapping_ok: bool
    locality_ok: bool
    preservation_ok: bool
    semantic_ok: bool | None
    disruption_ok: bool
    failure_reasons: tuple = field(default_factory=tuple)


class RepairVerifier:
    def __init__(self, semantic_verifier=None):
        self.semantic_verifier = semantic_verifier or CompositeSemanticVerifier()

    def verify(self, candidate, before_artifact, after_circuit, after_ops, region, budget, n_log) -> VerificationResult:
        reasons = []

        topo_ok, topo_violations = check_adjacency(after_circuit, before_artifact.coupling_graph)
        reasons.extend(topo_violations)

        map_ok, map_violations = check_mapping_bijective(candidate.new_layout)
        reasons.extend(map_violations)

        locality_ok, locality_violations = _check_locality(candidate, region)
        reasons.extend(locality_violations)

        preservation = check_preservation(before_artifact.operations, after_ops, region)
        reasons.extend(preservation.unexpected_changes)
        records_ok, record_violations = check_records_match_circuit(after_ops, after_circuit)
        reasons.extend(record_violations)
        preservation_ok = bool(preservation.passed and records_ok)

        semantic_ok = None
        if topo_ok and map_ok and locality_ok and records_ok:
            # Only worth the exact-simulation cost once the cheap
            # structural checks have already passed.
            sem_result = self.semantic_verifier.verify(
                before_artifact.compiled_circuit, before_artifact.layout,
                after_circuit, candidate.new_layout, n_log,
                input_layout_a=before_artifact.input_layout,
                input_layout_b=candidate.new_input_layout,
            )
            if not sem_result.available:
                semantic_ok = None
                reasons.append(sem_result.reason)
            else:
                semantic_ok = sem_result.equivalent
                if not semantic_ok:
                    reasons.append(sem_result.reason)
        else:
            reasons.append("semantic check skipped: topology/mapping/locality failed first")

        disruption_ok, disruption_violations = budget.check(candidate, region)
        reasons.extend(disruption_violations)

        passed = bool(
            topo_ok and map_ok and locality_ok and preservation_ok
            and semantic_ok is True and disruption_ok
        )

        return VerificationResult(
            passed=passed, topology_ok=topo_ok, mapping_ok=map_ok, locality_ok=locality_ok,
            preservation_ok=preservation_ok, semantic_ok=semantic_ok, disruption_ok=disruption_ok,
            failure_reasons=tuple(reasons),
        )


def _check_locality(candidate, region) -> tuple:
    """Every operation/physical-qubit the candidate claims to touch must
    already be declared INTERIOR to the region -- checked structurally,
    ahead of (and independent from) the full preservation diff."""
    interior_ids = set(region.affected_operation_ids)
    violations = []
    for node_id in candidate.touched_operation_ids:
        if node_id not in interior_ids:
            violations.append(
                f"candidate {candidate.candidate_id} touches operation {node_id} "
                f"which is not classified interior to the declared repair region"
            )
    for pq in candidate.touched_physical_qubits:
        if pq not in region.physical_qubits:
            violations.append(
                f"candidate {candidate.candidate_id} touches physical qubit {pq} "
                f"outside the declared region {list(region.physical_qubits)}"
            )
    return (len(violations) == 0, violations)
