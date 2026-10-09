"""
Device topology construction and the pinned initial layout convention.

The graph always contains exactly ``n_phys`` physical qubits.  The first
``n_main`` vertices form the main coupling graph; remaining vertices are
spare/twin resources connected to a main vertex and its existing neighbors.
"""
from __future__ import annotations

import networkx as nx


def build_topology(n_phys: int = 8, n_main: int | None = None):
    """Build a coupling graph with exactly ``n_phys`` vertices.

    ``n_main`` is the number of vertices reserved for the initial logical
    layout. If omitted, the original even-device convention is retained:
    ``max(3, n_phys // 2)`` main vertices. For a device with an uneven number
    of vertices, the extra vertex is represented as a real spare node rather
    than silently being dropped.

    Existing even-sized topologies retain the same main-edge construction and
    twin-edge insertion order, preserving seeded experiment reproducibility.
    """
    if not isinstance(n_phys, int) or isinstance(n_phys, bool) or n_phys < 3:
        raise ValueError("n_phys must be an integer greater than or equal to 3")

    if n_main is None:
        n_main = max(3, n_phys // 2)

    if not isinstance(n_main, int) or isinstance(n_main, bool):
        raise ValueError("n_main must be an integer")
    if n_main < 3 or n_main > n_phys:
        raise ValueError("n_main must be between 3 and n_phys")

    n_twins = n_phys - n_main
    g = nx.Graph()
    g.graph["n_phys"] = n_phys
    g.graph["n_main"] = n_main

    # Register every physical resource first. This prevents isolated or extra
    # vertices from disappearing when the requested device size is odd.
    g.add_nodes_from(range(n_phys))

    main_edges = (
        [(i, i + 1) for i in range(n_main - 1)]
        + [(0, n_main - 1)]
    )
    g.add_edges_from(main_edges)

    # Preserve the prior per-twin edge construction order for the original
    # even-sized configurations. When there are more spare nodes than main
    # nodes, assign additional spares round-robin across the main vertices.
    for twin_offset in range(n_twins):
        main_index = twin_offset % n_main
        twin = n_main + twin_offset
        g.add_edge(twin, main_index)
        for neighbor in list(g.neighbors(main_index)):
            if neighbor != twin:
                g.add_edge(twin, neighbor)

    edges = list(g.edges())

    # Fail loudly if this function ever returns a contradictory topology.
    expected_nodes = set(range(n_phys))
    if set(g.nodes()) != expected_nodes or g.number_of_nodes() != n_phys:
        raise RuntimeError(
            f"Topology construction mismatch: requested {n_phys} physical qubits, "
            f"created nodes {sorted(g.nodes())}"
        )
    if any(a not in expected_nodes or b not in expected_nodes for a, b in edges):
        raise RuntimeError("Topology contains an edge with an invalid physical-qubit index")

    return g, edges


def pinned_initial_layout(n_log: int, n_main: int) -> list[int]:
    """Pin logical qubits to the initial main vertices, leaving spares idle."""
    if n_log < 0:
        raise ValueError("n_log must be non-negative")
    if n_log > n_main:
        raise ValueError(
            f"Initial layout needs {n_log} main qubits, but topology has only {n_main}"
        )
    return list(range(n_log))
