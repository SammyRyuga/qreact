"""
ExperimentRunner: coordinates the full incremental-repair pipeline per
calibration step --

  DriftDetector -> RepairRegionBuilder -> LocalRepairPlanner ->
  (per candidate, best-scored first) DisruptionBudget + RepairVerifier ->
  RepairPatch accepted, or FallbackController.full_recompile()

This replaces the original run_incremental()'s inlined if/else chain.
Every existing output (fidelities, costs, usage, num_recompiles,
equivalence_checks, example) is still produced with the same meaning, so
app.py's response shape does not change. Additional counters
(num_local_patches, num_fallbacks, drift_event_count, region_sizes, ...)
are recorded explicitly during the run rather than reconstructed
arithmetically afterward, so metrics derived from them cannot silently
miscount an edge case (e.g. a fallback triggered with zero candidates
generated, which has no equivalence-check entry).
"""
from __future__ import annotations
import numpy as np

from compiler.compilation import compile_baseline, extract_layout
from compiler.artifact import make_artifact
from drift.detector import DriftDetector
from repair.region import RepairRegionBuilder
from repair.planner import LocalRepairPlanner
from repair.budget import DisruptionBudget
from repair.patch import patch_from_candidate
from verification.preservation import check_preservation
from verification.verifier import RepairVerifier
from events.models import EventType, EventLog
from .fallback import FallbackController
from .simulation import simulate_fidelity, circuit_png_base64


class ExperimentRunner:
    def __init__(self, threshold: float = 0.35, budget=None, planner=None, verifier=None,
                 region_builder=None, detector=None, detect_edges: bool = True, edge_threshold=None):
        self.threshold = threshold
        self.budget = budget or DisruptionBudget()
        self.planner = planner or LocalRepairPlanner()
        self.verifier = verifier or RepairVerifier()
        self.region_builder = region_builder or RepairRegionBuilder(
            max_radius=self.budget.max_topology_radius,
            max_operations=self.budget.max_region_operations,
            max_qubits=self.budget.max_region_qubits,
        )
        self.detector = detector or DriftDetector(
            threshold=threshold, detect_edges=detect_edges, edge_threshold=edge_threshold)

    def run_incremental_strategy(self, logical_qc, coupling, calib_sequence, seed: int, capture_example: bool = False):
        events = EventLog()
        compiled, cmap = compile_baseline(logical_qc, coupling, seed)
        layout = extract_layout(compiled, logical_qc.num_qubits)
        artifact = make_artifact(
            generation=0, logical_circuit=logical_qc, compiled_circuit=compiled,
            coupling_graph=coupling, layout=layout,
            baseline_snapshot=calib_sequence[0], validated_snapshot=calib_sequence[0],
        )
        fallback_ctl = FallbackController()

        fids, costs, usage = [], [], np.zeros(coupling.number_of_nodes())
        num_recompiles = 1
        num_local_patches = 0
        num_fallbacks = 0
        drift_event_count = 0
        equivalence_checks = []
        region_sizes, region_fractions = [], []
        changed_operation_counts, preservation_ratios = [], []
        added_swaps_counts, depth_deltas = [], []
        patches = []
        repair_records = []
        example = None
        legacy_log = []
        n_log = logical_qc.num_qubits

        for i, snap in enumerate(calib_sequence):
            cost = 0
            if i > 0:
                physical_edges = {op.physical_qubits for op in artifact.operations if len(op.physical_qubits) == 2}
                drift_event = self.detector.detect(
                    snap, artifact.validated_snapshot, artifact.layout.values(), physical_edges, step=i)
                events.add(EventType.CALIBRATION_SNAPSHOT, f"step {i}: calibration snapshot received", step=i)

                if drift_event.has_drift:
                    drift_event_count += 1
                    events.add(EventType.DRIFT_DETECTED,
                               f"step {i}: drift on qubits {list(drift_event.drifted_qubits)} "
                               f"edges {list(drift_event.drifted_edges)}", step=i, severity="warning")
                    region = self.region_builder.build(artifact, drift_event)
                    events.add(EventType.REGION_BUILT,
                               f"step {i}: region {region.region_id} size={region.region_size} "
                               f"ops={len(region.affected_operation_ids)} too_large={region.too_large}",
                               step=i, region_id=region.region_id)
                    region_sizes.append(region.region_size)
                    region_fractions.append(region.region_fraction)
                    rec = {"step": i, "drift_event": drift_event.as_dict(), "region": _region_dict(region),
                           "candidates": [], "selected_candidate": None, "fallback": None}
                    repair_records.append(rec)

                    accepted_patch = None
                    if not region.too_large:
                        candidates = self.planner.generate_candidates(artifact, drift_event, region, snap)
                        for cand in candidates:
                            events.add(EventType.CANDIDATE_GENERATED,
                                       f"step {i}: candidate {cand.candidate_id} ({cand.candidate_type}) "
                                       f"score={cand.disruption_score:.3f}", step=i, candidate_id=cand.candidate_id)
                            vresult = self.verifier.verify(
                                cand, artifact, cand.compiled_circuit, cand.operation_records,
                                region, self.budget, n_log)
                            equivalence_checks.append(bool(vresult.semantic_ok))
                            if not vresult.passed:
                                cand.rejection_reason = "; ".join(vresult.failure_reasons) or "unknown"
                            rec["candidates"].append(_candidate_dict(cand, vresult))
                            if vresult.passed:
                                events.add(EventType.CANDIDATE_VERIFIED,
                                           f"step {i}: candidate {cand.candidate_id} verification PASSED",
                                           step=i, candidate_id=cand.candidate_id)
                                patch = patch_from_candidate(
                                    patch_id=f"patch-{i}", source_artifact_version=artifact.generation,
                                    before_layout=artifact.layout, drift_event=drift_event, region=region,
                                    candidate=cand, verification_result=vresult, accepted=True)
                                patches.append(patch)
                                cand.accepted = True
                                rec["candidates"][-1]["accepted"] = True
                                rec["selected_candidate"] = cand.candidate_id
                                events.add(EventType.LOCAL_PATCH_ACCEPTED,
                                           f"step {i}: patch {patch.patch_id} accepted "
                                           f"({cand.candidate_type}), cost={cand.estimated_cost:.1f}", step=i)
                                legacy_log.append(
                                    f"step {i}: drifted phys qubits {sorted(drift_event.drifted_qubits)} -> "
                                    f"localized {cand.candidate_type} over region {list(region.physical_qubits)}, "
                                    f"equivalence check PASSED, cost={cand.estimated_cost:.0f}")
                                if capture_example and example is None:
                                    example = {
                                        "step": i,
                                        "drifted_phys": sorted(drift_event.drifted_qubits),
                                        "region": list(region.physical_qubits),
                                        "before_layout": dict(artifact.layout),
                                        "after_layout": dict(cand.new_layout),
                                        "before_png": circuit_png_base64(artifact.compiled_circuit),
                                        "after_png": circuit_png_base64(cand.compiled_circuit),
                                    }
                                preservation = check_preservation(artifact.operations, cand.operation_records, region)
                                total_ops = len(artifact.operations)
                                preservation_ratios.append(
                                    len(preservation.unchanged_operation_ids) / total_ops if total_ops else 1.0)
                                changed_operation_counts.append(len(cand.changed_operation_ids))
                                added_swaps_counts.append(len(cand.inserted_swaps))
                                depth_deltas.append(cand.estimated_depth_delta)

                                artifact = make_artifact(
                                    generation=artifact.generation + 1, logical_circuit=logical_qc,
                                    compiled_circuit=cand.compiled_circuit, coupling_graph=coupling,
                                    layout=cand.new_layout, baseline_snapshot=artifact.baseline_snapshot,
                                    validated_snapshot=snap, input_layout=cand.new_input_layout,
                                )
                                accepted_patch = patch
                                cost = cand.estimated_cost
                                num_recompiles += 1
                                num_local_patches += 1
                                break
                            else:
                                events.add(EventType.CANDIDATE_REJECTED,
                                           f"step {i}: candidate {cand.candidate_id} rejected "
                                           f"({'; '.join(vresult.failure_reasons) or 'no reason recorded'})",
                                           step=i, candidate_id=cand.candidate_id, severity="warning")

                    if accepted_patch is None:
                        reason = "region_too_large" if region.too_large else "no_feasible_candidate"
                        artifact, reason = fallback_ctl.full_recompile(
                            logical_qc, coupling, seed + i, artifact.generation + 1, snap, reason)
                        events.add(EventType.FALLBACK_TRIGGERED, f"step {i}: fallback triggered ({reason})",
                                   step=i, severity="warning", reason=reason)
                        events.add(EventType.FULL_RECOMPILE, f"step {i}: full re-transpilation complete", step=i)
                        legacy_log.append(f"step {i}: {reason} -> full fallback")
                        rec["fallback"] = {"reason": reason, "action": "full_retranspile_from_logical_circuit"}
                        cost = n_log * coupling.number_of_nodes()
                        num_recompiles += 1
                        num_fallbacks += 1

            fids.append(simulate_fidelity(artifact.compiled_circuit, snap, artifact.layout))
            costs.append(cost)
            for p in set(artifact.layout.values()):
                usage[p] += 1
            events.add(EventType.EXPERIMENT_STEP, f"step {i}: fidelity={fids[-1]:.4f}", step=i)

        return {
            "fidelities": fids, "costs": costs, "usage": usage.tolist(),
            "num_recompiles": num_recompiles, "num_local_patches": num_local_patches,
            "num_fallbacks": num_fallbacks, "drift_event_count": drift_event_count,
            "equivalence_checks": equivalence_checks,
            "region_sizes": region_sizes, "region_fractions": region_fractions,
            "changed_operation_counts": changed_operation_counts,
            "preservation_ratios": preservation_ratios,
            "added_swaps_counts": added_swaps_counts, "depth_deltas": depth_deltas,
            "patches": [p.as_dict() for p in patches], "repair_records": repair_records,
            "example": example, "events": events, "log": legacy_log,
        }


def _region_dict(region) -> dict:
    return {
        "region_id": region.region_id, "physical_qubits": list(region.physical_qubits),
        "affected_logical_qubits": list(region.affected_logical_qubits),
        "affected_operation_ids": list(region.affected_operation_ids),
        "boundary_operation_ids": list(region.boundary_operation_ids),
        "region_edges": [list(e) for e in region.region_edges], "radius": region.radius,
        "region_size": region.region_size, "region_fraction": region.region_fraction,
        "reason": region.reason, "too_large": region.too_large,
    }


def _verification_dict(v) -> dict:
    return {
        "passed": v.passed, "topology_ok": v.topology_ok, "mapping_ok": v.mapping_ok,
        "locality_ok": v.locality_ok, "preservation_ok": v.preservation_ok,
        "semantic_ok": v.semantic_ok, "disruption_ok": v.disruption_ok,
        "failure_reasons": list(v.failure_reasons),
    }


def _candidate_dict(cand, vresult) -> dict:
    return {
        "candidate_id": cand.candidate_id, "candidate_type": cand.candidate_type,
        "touched_physical_qubits": list(cand.touched_physical_qubits),
        "touched_logical_qubits": list(cand.touched_logical_qubits),
        "changed_operation_ids": list(cand.changed_operation_ids),
        "new_layout": {str(k): v for k, v in cand.new_layout.items()},
        "inserted_swaps": [{"position": s.position, "physical_edge": list(s.physical_edge), "node_id": s.node_id}
                           for s in cand.inserted_swaps],
        "estimated_depth_delta": cand.estimated_depth_delta, "estimated_cost": cand.estimated_cost,
        "estimated_error": cand.estimated_error, "score": cand.disruption_score,
        "accepted": False, "rejection_reason": cand.rejection_reason,
        "verification": _verification_dict(vresult),
    }
