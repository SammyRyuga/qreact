import numpy as np, pytest
from execution.fallback import FallbackController, FALLBACK_REASONS
from execution.experiment import ExperimentRunner
from repair.budget import DisruptionBudget
from repair.region import RepairRegionBuilder
from compiler.circuits import build_logical_circuit
from compiler.topology import build_topology
from calibration.synthetic import SyntheticCalibrationProvider


def test_full_fallback_recompiles_from_logical_circuit(setup):
    art = setup["artifact"]
    new, reason = FallbackController().full_recompile(
        setup["qc"], setup["coupling"], seed=3, generation=art.generation + 1,
        calib_snapshot=setup["seq"][5], reason="region_too_large")
    assert reason == "region_too_large" and new.generation == art.generation + 1
    assert new.baseline_snapshot is setup["seq"][5] and new.validated_snapshot is setup["seq"][5]
    assert new.logical_circuit is setup["qc"]
    assert new.input_layout == {i: i for i in range(4)}
    assert len(new.operations) == len(new.compiled_circuit.data)


def test_unknown_fallback_reason_is_refused(setup):
    with pytest.raises(AssertionError):
        FallbackController().full_recompile(setup["qc"], setup["coupling"], 1, 1, setup["seq"][0], "because")


def test_all_documented_reasons_are_known():
    for r in ("region_too_large", "no_feasible_candidate", "semantic_verification_failure",
              "verification_unavailable", "disruption_budget_failure", "internal_exception"):
        assert r in FALLBACK_REASONS


def test_region_too_large_forces_fallback_end_to_end():
    qc = build_logical_circuit(4)
    coupling, edges = build_topology(8)
    seq = SyntheticCalibrationProvider(coupling.number_of_nodes(), edges, seed=11).sequence(15)
    runner = ExperimentRunner(threshold=0.35, detect_edges=False,
                              budget=DisruptionBudget(max_region_qubits=0, max_topology_radius=0))
    r = runner.run_incremental_strategy(qc, coupling, seq, seed=11)
    assert r["drift_event_count"] > 0
    assert r["num_local_patches"] == 0
    assert r["num_fallbacks"] == r["drift_event_count"]
    assert all(rec["fallback"] and rec["fallback"]["reason"] == "region_too_large" for rec in r["repair_records"])


def test_every_drift_event_ends_in_exactly_one_outcome():
    qc = build_logical_circuit(4)
    coupling, edges = build_topology(8)
    seq = SyntheticCalibrationProvider(coupling.number_of_nodes(), edges, seed=23).sequence(20)
    r = ExperimentRunner(threshold=0.35, detect_edges=False).run_incremental_strategy(qc, coupling, seq, seed=23)
    assert r["num_local_patches"] + r["num_fallbacks"] == r["drift_event_count"]
    for rec in r["repair_records"]:
        assert bool(rec["selected_candidate"]) != bool(rec["fallback"])   # patch XOR fallback, never both/neither


def test_accepted_patches_were_fully_verified():
    qc = build_logical_circuit(4)
    coupling, edges = build_topology(8)
    seq = SyntheticCalibrationProvider(coupling.number_of_nodes(), edges, seed=11).sequence(15)
    r = ExperimentRunner(threshold=0.35, detect_edges=False).run_incremental_strategy(qc, coupling, seq, seed=11)
    for rec in r["repair_records"]:
        if rec["selected_candidate"]:
            sel = next(c for c in rec["candidates"] if c["candidate_id"] == rec["selected_candidate"])
            v = sel["verification"]
            assert v["passed"] and v["topology_ok"] and v["mapping_ok"] and v["locality_ok"]
            assert v["preservation_ok"] and v["semantic_ok"] is True and v["disruption_ok"]


def test_deterministic_seed_behavior_and_seed_sensitivity():
    qc = build_logical_circuit(4)
    coupling, edges = build_topology(8)

    def run(seed):
        seq = SyntheticCalibrationProvider(coupling.number_of_nodes(), edges, seed=seed).sequence(12)
        r = ExperimentRunner(threshold=0.35, detect_edges=False).run_incremental_strategy(qc, coupling, seq, seed=seed)
        return r

    a, b, c = run(11), run(11), run(23)
    assert a["fidelities"] == b["fidelities"] and a["costs"] == b["costs"]
    assert a["events"].messages() == b["events"].messages()
    assert a["repair_records"] == b["repair_records"]
    assert a["fidelities"] != c["fidelities"] or a["events"].messages() != c["events"].messages()
