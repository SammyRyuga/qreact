import pytest
from qiskit import QuantumCircuit
from drift.models import DriftEvent
from repair.region import RepairRegionBuilder
from repair.planner import LocalRepairPlanner
from repair.budget import DisruptionBudget
from repair.candidates import generate_relabel_candidate, PURE_RELABEL
from verification.topology import check_adjacency, check_mapping_bijective
from verification.preservation import check_preservation
from verification.semantic import (ExactMeasurementDistributionVerifier, RandomizedInputStateVerifier,
                                   CompositeSemanticVerifier)
from verification.verifier import RepairVerifier
from compiler.artifact import OperationRecord
from dataclasses import replace


def _event(q):
    return DriftEvent(step=1, drifted_qubits=(q,), drifted_edges=(), qubit_delta_by_resource={},
                      edge_delta_by_resource={}, threshold=0.35, trigger_reason="x", affected_resources=(q,))


def _valid_candidate(setup):
    """Return (artifact, region, candidate) for a candidate that GENUINELY
    passes full verification, so adversarial tests start from a known-good
    baseline and then tamper with it. Many generated candidates are (rightly)
    rejected -- e.g. a relabel onto a non-twin qubit breaks coupling edges."""
    art = setup["artifact"]
    for step in range(1, 15):
        for q in sorted(art.layout.values()):
            ev = _event(q)
            ev = DriftEvent(step=step, drifted_qubits=(q,), drifted_edges=(), qubit_delta_by_resource={},
                            edge_delta_by_resource={}, threshold=0.35, trigger_reason="x", affected_resources=(q,))
            region = RepairRegionBuilder(max_radius=2, max_operations=24, max_qubits=6).build(art, ev)
            if region.too_large:
                continue
            for cand in LocalRepairPlanner().generate_candidates(art, ev, region, setup["seq"][step]):
                res = RepairVerifier().verify(cand, art, cand.compiled_circuit, cand.operation_records,
                                              region, DisruptionBudget(), 4)
                if res.passed:
                    return art, region, cand
    pytest.skip("no fully-verified candidate available in this fixture")


def test_mapping_bijection():
    assert check_mapping_bijective({0: 1, 1: 2})[0]
    ok, why = check_mapping_bijective({0: 1, 1: 1})
    assert not ok and "both map to physical 1" in why[0]


def test_topology_rejects_broken_coupling_edge(setup):
    art = setup["artifact"]
    import networkx as nx
    a, b = next(iter(nx.non_edges(art.coupling_graph)))
    bad = QuantumCircuit(8)
    bad.cx(a, b)   # a genuine non-edge of this topology
    ok, why = check_adjacency(bad, art.coupling_graph)
    assert not ok and "not a coupling-graph edge" in why[0]


def test_valid_relabel_passes_every_check(setup):
    art, region, cand = _valid_candidate(setup)
    res = RepairVerifier().verify(cand, art, cand.compiled_circuit, cand.operation_records,
                                  region, DisruptionBudget(), 4)
    assert res.topology_ok and res.mapping_ok and res.locality_ok and res.preservation_ok
    assert res.disruption_ok


def test_preservation_rejects_change_outside_region(setup):
    art, region, cand = _valid_candidate(setup)
    outside = next(op for op in art.operations
                   if op.node_id not in set(region.affected_operation_ids) | set(region.boundary_operation_ids))
    tampered = [replace(op, physical_qubits=(7,) * len(op.physical_qubits)) if op.node_id == outside.node_id else op
                for op in art.operations]
    res = check_preservation(art.operations, tampered, region)
    assert not res.passed and any("outside" in u for u in res.unexpected_changes)


def test_preservation_rejects_change_to_boundary_operation(setup):
    art, region, _ = _valid_candidate(setup)
    if not region.boundary_operation_ids:
        pytest.skip("no boundary ops for this region")
    bid = region.boundary_operation_ids[0]
    tampered = [replace(op, physical_qubits=tuple(reversed(op.physical_qubits)) + (op.physical_qubits[0],) * 0)
                if op.node_id == bid else op for op in art.operations]
    tampered = [replace(op, physical_qubits=(7,) + op.physical_qubits[1:]) if op.node_id == bid else op
                for op in art.operations]
    res = check_preservation(art.operations, tampered, region)
    assert not res.passed and any("boundary" in u for u in res.unexpected_changes)


def test_preservation_rejects_op_type_change_inside_region(setup):
    art, region, _ = _valid_candidate(setup)
    inside = region.affected_operation_ids[0]
    tampered = [replace(op, op_type="x") if op.node_id == inside else op for op in art.operations]
    res = check_preservation(art.operations, tampered, region)
    assert not res.passed and any("op_type" in u for u in res.unexpected_changes)


def test_preservation_rejects_new_op_outside_region(setup):
    art, region, _ = _valid_candidate(setup)
    outside_q = next(q for q in range(8) if q not in region.physical_qubits)
    extra = OperationRecord(node_id="rogue", operation_index=-1, op_type="swap", logical_qubits=(None, None),
                            physical_qubits=(outside_q, outside_q))
    res = check_preservation(art.operations, list(art.operations) + [extra], region)
    assert not res.passed and any("outside the declared region" in u for u in res.unexpected_changes)


def test_preservation_rejects_removed_operation(setup):
    art, region, _ = _valid_candidate(setup)
    res = check_preservation(art.operations, art.operations[1:], region)
    assert not res.passed and any("removed" in u for u in res.unexpected_changes)


def test_locality_rejects_candidate_touching_foreign_operation(setup):
    art, region, cand = _valid_candidate(setup)
    foreign = next(op.node_id for op in art.operations if op.node_id not in region.affected_operation_ids)
    cand.touched_operation_ids = tuple(cand.touched_operation_ids) + (foreign,)
    res = RepairVerifier().verify(cand, art, cand.compiled_circuit, cand.operation_records,
                                  region, DisruptionBudget(), 4)
    assert not res.locality_ok and not res.passed


def test_semantic_rejects_intentionally_invalid_remapping(setup):
    """Adversarial: a real, topology-valid circuit that computes the WRONG
    thing (an extra non-Pauli rotation on a logical qubit). Must be rejected.
    (An extra X would NOT work as a test: on this H -> CX-cascade -> Z-measure
    circuit family it is a Z-type error that no measurement-distribution check
    can see -- see README 'Known limitations'.)"""
    art, region, cand = _valid_candidate(setup)
    wrong = cand.compiled_circuit.copy_empty_like()
    phys0 = cand.new_layout[0]
    wrong.ry(0.9, phys0)
    for instr in cand.compiled_circuit.data:
        wrong.append(instr.operation, instr.qubits, instr.clbits)
    cand.compiled_circuit = wrong
    from compiler.artifact import build_operation_records
    honest_records = build_operation_records(wrong, cand.new_layout, generation=99)   # records that describe `wrong`
    res = RepairVerifier().verify(cand, art, wrong, honest_records, region, DisruptionBudget(), 4)
    assert res.topology_ok and res.mapping_ok          # structurally fine ...
    assert res.semantic_ok is False and not res.passed  # ... but computes the wrong thing


def test_exact_zero_input_check_is_blind_to_cx_drop_but_composite_is_not(setup):
    """Documents WHY the randomized verifier exists: this benchmark's output
    from |0..0> is exactly uniform, so dropping a CX is invisible to the
    zero-input check but visible to the composite."""
    art = setup["artifact"]
    broken = art.compiled_circuit.copy_empty_like()
    dropped = False
    for instr in art.compiled_circuit.data:
        if instr.operation.name == "cx" and not dropped:
            dropped = True
            continue
        broken.append(instr.operation, instr.qubits, instr.clbits)
    args = (art.compiled_circuit, art.layout, broken, art.layout, 4)
    kw = dict(input_layout_a=art.input_layout, input_layout_b=art.input_layout)
    assert ExactMeasurementDistributionVerifier().verify(*args, **kw).equivalent is True   # blind
    assert RandomizedInputStateVerifier().verify(*args, **kw).equivalent is False          # catches it
    assert CompositeSemanticVerifier().verify(*args, **kw).equivalent is False


def test_semantic_unavailable_is_never_treated_as_pass(setup):
    art, region, cand = _valid_candidate(setup)
    v = RepairVerifier(semantic_verifier=CompositeSemanticVerifier(
        [ExactMeasurementDistributionVerifier(max_exact_qubits=2)]))
    res = v.verify(cand, art, cand.compiled_circuit, cand.operation_records, region,
                   DisruptionBudget(), 4)
    assert res.semantic_ok is None and not res.passed
    assert any("verification_unavailable" in r for r in res.failure_reasons)


def test_disruption_budget_rejects_oversized_candidate(setup):
    art, region, cand = _valid_candidate(setup)
    res = RepairVerifier().verify(cand, art, cand.compiled_circuit, cand.operation_records, region,
                                  DisruptionBudget(max_changed_operations=0), 4)
    assert not res.disruption_ok and not res.passed
    assert any("max_changed_operations" in r for r in res.failure_reasons)


def test_verifier_rejects_candidate_whose_records_lie_about_the_circuit(setup):
    """Adversarial: the real circuit changes but the sidecar records claim
    nothing did. Preservation on records alone would pass this."""
    art, region, cand = _valid_candidate(setup)
    tampered = cand.compiled_circuit.copy_empty_like()
    tampered.ry(0.9, cand.new_layout[0])
    for instr in cand.compiled_circuit.data:
        tampered.append(instr.operation, instr.qubits, instr.clbits)
    res = RepairVerifier().verify(cand, art, tampered, cand.operation_records, region, DisruptionBudget(), 4)
    assert not res.preservation_ok and not res.passed
    assert any("do not match the circuit" in r for r in res.failure_reasons)


def test_swap_candidate_circuit_really_contains_the_swaps_its_records_claim(setup):
    from repair.candidates import generate_swap_candidate
    art = setup["artifact"]
    for q in art.layout.values():
        ev = _event(q)
        region = RepairRegionBuilder(max_radius=2, max_operations=24, max_qubits=6).build(art, ev)
        cand = generate_swap_candidate(art, ev, region, setup["seq"][3])
        if cand is None:
            continue
        names = [i.operation.name for i in cand.compiled_circuit.data]
        assert names[:len(cand.inserted_swaps)] == ["swap"] * len(cand.inserted_swaps)
        res = RepairVerifier().verify(cand, art, cand.compiled_circuit, cand.operation_records, region,
                                      DisruptionBudget(), 4)
        assert res.preservation_ok
        return
    pytest.skip("no swap candidate in fixture")
