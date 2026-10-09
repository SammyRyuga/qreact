"""
FallbackController: owns the one non-negotiable safety rule --
NO LOCAL PATCH IS DEPLOYED UNLESS ALL REQUIRED VERIFIERS PASS.

Fallback always re-transpiles from the ORIGINAL logical circuit (never
from a partially-modified one), producing a brand-new CompiledArtifact
generation with a fresh baseline calibration reference. The system is
never left holding a partially modified, unverified circuit.
"""
from __future__ import annotations
from compiler.compilation import compile_baseline, extract_layout
from compiler.artifact import make_artifact

FALLBACK_REASONS = (
    "no_drift", "region_too_large", "no_feasible_candidate", "topology_failure",
    "mapping_failure", "preservation_failure", "semantic_verification_failure",
    "disruption_budget_failure", "verification_unavailable", "internal_exception",
)


class FallbackController:
    def full_recompile(self, logical_circuit, coupling, seed: int, generation: int, calib_snapshot, reason: str):
        assert reason in FALLBACK_REASONS, f"unrecognized fallback reason: {reason!r}"
        compiled, _cmap = compile_baseline(logical_circuit, coupling, seed)
        layout = extract_layout(compiled, logical_circuit.num_qubits)
        new_artifact = make_artifact(
            generation=generation, logical_circuit=logical_circuit, compiled_circuit=compiled,
            coupling_graph=coupling, layout=layout,
            baseline_snapshot=calib_snapshot, validated_snapshot=calib_snapshot,
        )
        return new_artifact, reason
