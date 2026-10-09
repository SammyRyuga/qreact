"""
Shared compilation helpers used by every strategy (static, full
retranspile, incremental) so the first-compile pinned layout is defined once.
"""
from __future__ import annotations

from qiskit import transpile
from qiskit.transpiler import CouplingMap

from .topology import pinned_initial_layout


def compile_baseline(logical_qc, coupling, seed: int):
    """Transpile onto the supplied topology using its declared main vertices.

    ``n_main`` is stored as graph metadata by ``build_topology``. The fallback
    supports caller-created legacy graphs that do not carry this metadata.
    """
    cmap = CouplingMap(list(coupling.edges()))
    n_main = int(coupling.graph.get("n_main", coupling.number_of_nodes() // 2))
    initial_layout = pinned_initial_layout(logical_qc.num_qubits, n_main)

    compiled = transpile(
        logical_qc,
        coupling_map=cmap,
        optimization_level=1,
        seed_transpiler=seed,
        initial_layout=initial_layout,
    )
    return compiled, cmap


def extract_layout(compiled_circ, n_log: int) -> dict:
    """Logical qubit index -> physical qubit index, read from final layout."""
    tl = compiled_circ.layout
    if tl is None:
        return {i: i for i in range(n_log)}
    try:
        arr = tl.final_index_layout(filter_ancillas=True)
    except Exception:
        arr = tl.initial_index_layout(filter_ancillas=True)
    return {i: arr[i] for i in range(n_log)}
