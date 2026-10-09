import pytest

from compiler.topology import build_topology, pinned_initial_layout


@pytest.mark.parametrize("n_phys", [6, 7, 8, 9, 10])
def test_build_topology_contains_exact_requested_physical_count(n_phys):
    graph, edges = build_topology(n_phys)

    assert graph.number_of_nodes() == n_phys
    assert set(graph.nodes()) == set(range(n_phys))
    assert graph.graph["n_phys"] == n_phys
    assert all(a in graph and b in graph for a, b in edges)
    assert all(0 <= a < n_phys and 0 <= b < n_phys for a, b in edges)
    assert {tuple(sorted(edge)) for edge in edges} == {
        tuple(sorted(edge)) for edge in graph.edges()
    }


def test_odd_device_can_reserve_enough_main_qubits_for_logical_layout():
    n_log, n_phys = 5, 7
    n_main = max(3, n_log, n_phys // 2)
    graph, edges = build_topology(n_phys, n_main=n_main)

    assert graph.number_of_nodes() == 7
    assert graph.graph["n_main"] == 5
    assert pinned_initial_layout(n_log, n_main) == [0, 1, 2, 3, 4]
    assert all(node < n_main for node in pinned_initial_layout(n_log, n_main))
    assert all(a in graph and b in graph for a, b in edges)


def test_pinned_layout_rejects_logical_width_larger_than_main_region():
    with pytest.raises(ValueError, match="Initial layout needs"):
        pinned_initial_layout(n_log=5, n_main=4)
