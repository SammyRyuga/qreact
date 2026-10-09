from drift.models import DriftEvent
from repair.region import RepairRegionBuilder


def event(qubits=(), edges=(), step=1):
    return DriftEvent(step=step, drifted_qubits=tuple(qubits), drifted_edges=tuple(edges),
                      qubit_delta_by_resource={}, edge_delta_by_resource={}, threshold=0.35,
                      trigger_reason="relative_calibration_change", affected_resources=tuple(qubits))


def test_region_is_bounded_and_classifies_operations_upfront(setup):
    art = setup["artifact"]
    region = RepairRegionBuilder(max_radius=1, max_operations=24, max_qubits=6).build(art, event([2]))
    assert not region.too_large
    assert 2 in region.physical_qubits and region.region_size <= 6
    assert 0 < region.region_fraction <= 1
    interior, boundary = set(region.affected_operation_ids), set(region.boundary_operation_ids)
    assert not interior & boundary
    # classification is complete: every op touching the region is interior or boundary
    for op in art.operations:
        touches = any(p in region.physical_qubits for p in op.physical_qubits)
        inside = all(p in region.physical_qubits for p in op.physical_qubits)
        if touches and inside:
            assert op.node_id in interior
        elif touches:
            assert op.node_id in boundary
        else:
            assert op.node_id not in interior | boundary


def test_boundary_ops_cross_the_region_edge(setup):
    art = setup["artifact"]
    region = RepairRegionBuilder(max_radius=1, max_operations=24, max_qubits=6).build(art, event([2]))
    for nid in region.boundary_operation_ids:
        op = art.operation_by_id(nid)
        assert any(p in region.physical_qubits for p in op.physical_qubits)
        assert any(p not in region.physical_qubits for p in op.physical_qubits)


def test_region_too_large_by_qubit_bound(setup):
    art = setup["artifact"]
    region = RepairRegionBuilder(max_radius=2, max_operations=24, max_qubits=2).build(art, event([1]))
    assert region.too_large and "region_too_large" in region.reason
    assert region.affected_operation_ids == ()


def test_region_too_large_by_operation_bound(setup):
    art = setup["artifact"]
    region = RepairRegionBuilder(max_radius=2, max_operations=1, max_qubits=8).build(art, event([1]))
    assert region.too_large and "operation-count" in region.reason


def test_edge_drift_seeds_both_endpoints(setup):
    art = setup["artifact"]
    region = RepairRegionBuilder(max_radius=0, max_operations=24, max_qubits=8).build(art, event(edges=[(0, 1)]))
    assert {0, 1} <= set(region.physical_qubits)
