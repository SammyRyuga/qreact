from drift.models import DriftEvent
from repair.region import RepairRegionBuilder
from repair.planner import LocalRepairPlanner
from repair.candidates import generate_swap_candidate, _idle_physical_qubits, LOCAL_SWAP
from repair.budget import DisruptionBudget
from verification.verifier import RepairVerifier


def _event(q, step=1):
    return DriftEvent(step=step, drifted_qubits=(q,), drifted_edges=(), qubit_delta_by_resource={},
                      edge_delta_by_resource={}, threshold=0.35, trigger_reason="x", affected_resources=(q,))


def test_planner_scores_are_deterministic_and_sorted(setup):
    art = setup["artifact"]
    ev = _event(next(iter(art.layout.values())))
    region = RepairRegionBuilder(max_radius=2, max_operations=24, max_qubits=6).build(art, ev)
    p = LocalRepairPlanner()
    a = p.generate_candidates(art, ev, region, setup["seq"][3])
    b = p.generate_candidates(art, ev, region, setup["seq"][3])
    assert [c.candidate_id for c in a] == [c.candidate_id for c in b]
    assert [c.disruption_score for c in a] == sorted([c.disruption_score for c in a], reverse=True)


def test_candidates_do_not_mutate_the_source_artifact(setup):
    art = setup["artifact"]
    before_ops = [(o.node_id, o.physical_qubits) for o in art.operations]
    before_layout = dict(art.layout)
    ev = _event(next(iter(art.layout.values())))
    region = RepairRegionBuilder(max_radius=2, max_operations=24, max_qubits=6).build(art, ev)
    LocalRepairPlanner().generate_candidates(art, ev, region, setup["seq"][3])
    assert before_ops == [(o.node_id, o.physical_qubits) for o in art.operations]
    assert before_layout == art.layout


def test_swap_candidate_only_uses_idle_bridges_and_idle_target(setup):
    art = setup["artifact"]
    idle = _idle_physical_qubits(art)
    found = 0
    for q in art.layout.values():
        ev = _event(q)
        region = RepairRegionBuilder(max_radius=2, max_operations=24, max_qubits=6).build(art, ev)
        cand = generate_swap_candidate(art, ev, region, setup["seq"][3])
        if cand is None:
            continue
        found += 1
        assert cand.candidate_type == LOCAL_SWAP
        path_qubits = {q for s in cand.inserted_swaps for q in s.physical_edge}
        assert path_qubits - {q} <= idle                      # every bridge AND the target are idle
        for s in cand.inserted_swaps:
            assert art.coupling_graph.has_edge(*s.physical_edge)   # swaps sit on real edges
        # the real circuit was actually modified -- not just metadata
        assert sum(1 for i in cand.compiled_circuit.data if i.operation.name == "swap") >= len(cand.inserted_swaps)
    assert found >= 1


def test_swap_candidate_refuses_when_target_would_be_occupied(setup):
    """With every non-drifted qubit occupied, no idle target exists and no
    swap candidate may be produced (never assume an occupied target is safe)."""
    art = setup["artifact"]
    q = next(iter(art.layout.values()))
    ev = _event(q)
    region = RepairRegionBuilder(max_radius=2, max_operations=24, max_qubits=6).build(art, ev)
    import repair.candidates as c
    original = c._idle_physical_qubits
    c._idle_physical_qubits = lambda artifact: set()
    try:
        assert generate_swap_candidate(art, ev, region, setup["seq"][3]) is None
    finally:
        c._idle_physical_qubits = original


def test_high_score_never_overrides_failed_verification(setup):
    art = setup["artifact"]
    ev = _event(next(iter(art.layout.values())))
    region = RepairRegionBuilder(max_radius=2, max_operations=24, max_qubits=6).build(art, ev)
    cands = LocalRepairPlanner().generate_candidates(art, ev, region, setup["seq"][3])
    assert cands
    top = cands[0]
    top.touched_physical_qubits = tuple(top.touched_physical_qubits) + (99,)   # sabotage the best-scored one
    res = RepairVerifier().verify(top, art, top.compiled_circuit, top.operation_records, region,
                                  DisruptionBudget(), 4)
    assert not res.passed and not res.locality_ok
