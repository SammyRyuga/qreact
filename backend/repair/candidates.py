"""
PatchCandidate generation.

Three candidate types, in increasing order of mechanism complexity:

  PURE_RELABEL   -- a consistent renaming of physical-qubit labels applied
                    uniformly to every operation inside the region. Always
                    correctness-preserving by construction (gate order and
                    content never change); can only ever break coupling-map
                    adjacency, which verification checks separately.

  LOCAL_SWAP     -- v1, deliberately narrow safe subset only (see README
                    "SWAP Safety Scope"). Fires only when exactly one
                    logical qubit needs to move, and only when a chain of
                    SWAPs exists through qubits that are ALL globally idle
                    -- every intermediate bridge AND the final target.
                    An occupied target is NEVER assumed safe: this project
                    does not track the logical state that might be sitting
                    on an occupied qubit well enough to prove a swap
                    through it preserves that other qubit's computation,
                    so it simply does not attempt it. If no idle-only path
                    exists, this candidate type is not generated at all --
                    there is no unsafe fallback within it.

  ALT_MAPPING    -- the same relabel mechanism as PURE_RELABEL, with a
                    different deterministic tie-break among valid targets
                    (prefers the farthest-within-region healthy qubit
                    rather than the nearest/cheapest), so the planner has
                    a genuine second option to score against when more
                    than one valid relabeling exists. Not a different
                    mechanism -- an honestly-labeled structural variation
                    of the same one.

NONE of these candidate types re-invoke transpile()/SabreSwap to produce a
"local" result. Doing so was the original bug this project already found
and fixed once: the router can silently re-route physical qubits outside
the intended region. Every candidate here is built by direct, explicit
instruction-list construction instead.
"""
from __future__ import annotations
from dataclasses import dataclass
import uuid

import networkx as nx

from compiler.artifact import relabel_operation_records, OperationRecord

PURE_RELABEL = "PURE_RELABEL"
LOCAL_SWAP = "LOCAL_SWAP"
ALT_MAPPING = "ALT_MAPPING"


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@dataclass(frozen=True)
class SwapInsertion:
    position: int               # index in the new operation list where this SWAP sits
    physical_edge: tuple        # (a, b)
    node_id: str


@dataclass
class PatchCandidate:
    candidate_id: str
    candidate_type: str
    touched_physical_qubits: tuple
    touched_logical_qubits: tuple
    touched_operation_ids: tuple        # interior ops this candidate reads/depends on (region-scoped)
    changed_operation_ids: tuple        # pre-existing ops whose physical_qubits actually change
    new_layout: dict
    physical_permutation: dict
    inserted_swaps: tuple = ()          # tuple[SwapInsertion, ...]
    added_two_qubit_ops: int = 0
    estimated_depth_delta: int = 0
    estimated_cost: float = 0.0
    estimated_error: float = 0.0
    disruption_score: float = 0.0
    topology_valid: bool | None = None
    semantic_valid: bool | None = None
    accepted: bool = False
    rejection_reason: str | None = None
    compiled_circuit: object = None     # the actual rewritten qiskit QuantumCircuit (built eagerly, real)
    operation_records: tuple = ()       # the candidate's resulting OperationRecord list
    new_input_layout: dict = None       # where each logical qubit's INPUT lives in the candidate circuit


def _build_full_permutation(old_to_new: dict, n_phys: int) -> dict:
    """Extends a partial bijection on drifted qubits into a full
    permutation of range(n_phys), identity outside the touched positions.
    Unchanged from the original prototype."""
    perm = {i: i for i in range(n_phys)}
    domain, codomain = set(old_to_new), set(old_to_new.values())
    only_domain = list(domain - codomain)
    only_codomain = list(codomain - domain)
    for src, dst in zip(only_codomain, only_domain):
        perm[src] = dst
    for old_p, new_p in old_to_new.items():
        perm[old_p] = new_p
    return perm


def _relabel_circuit(circuit, perm: dict):
    """Pure relabeling: gate order/content untouched, only which physical
    wire each qubit argument refers to changes. Unchanged from the
    original prototype."""
    new_circ = circuit.copy_empty_like()
    for instr in circuit.data:
        new_qubits = [circuit.qubits[perm[circuit.find_bit(q).index]] for q in instr.qubits]
        new_circ.append(instr.operation, new_qubits, instr.clbits)
    return new_circ


def _idle_physical_qubits(artifact) -> set:
    """A physical qubit is globally idle if NO operation in the current
    compiled artifact references it at all -- not merely "idle right now"
    at some point in a hypothetical timeline. This is what makes it safe
    to swap through: nothing else can possibly be disturbed."""
    used = set()
    for op in artifact.operations:
        used.update(op.physical_qubits)
    all_phys = set(artifact.coupling_graph.nodes())
    return all_phys - used


def _healthy_candidates_within_region(artifact, region, calib_snapshot, drifted_phys, prefer_far=False):
    occupied_by_others = set(artifact.layout.values()) - drifted_phys
    pool = set(region.physical_qubits) - occupied_by_others
    if not prefer_far:
        key = lambda q: (q in drifted_phys, calib_snapshot.qubit_error(q))
        return sorted(pool, key=key)

    # ALT_MAPPING tie-break: among qubits with the same drifted/healthy
    # status, prefer the one FURTHEST from the drifted set rather than the
    # lowest raw error -- a genuinely different mapping choice.
    coupling = artifact.coupling_graph

    def far_key(q):
        is_drifted = q in drifted_phys
        dist = min((nx.shortest_path_length(coupling, d, q) for d in drifted_phys), default=0)
        return (is_drifted, -dist, calib_snapshot.qubit_error(q))

    return sorted(pool, key=far_key)


def generate_relabel_candidate(artifact, drift_event, region, calib_snapshot,
                                candidate_type=PURE_RELABEL, prefer_far=False):
    """Candidates A (PURE_RELABEL) and C (ALT_MAPPING): a pure wire
    relabeling, restricted entirely to `region`."""
    if region.too_large:
        return None
    drifted_phys = set(drift_event.drifted_qubits)
    for (a, b) in drift_event.drifted_edges:
        drifted_phys.add(a)
        drifted_phys.add(b)
    drifted_phys &= set(artifact.layout.values())
    if not drifted_phys:
        return None

    affected_logical = [lq for lq, pq in artifact.layout.items() if pq in drifted_phys]
    pool = _healthy_candidates_within_region(artifact, region, calib_snapshot, drifted_phys, prefer_far=prefer_far)
    if len(pool) < len(affected_logical):
        return None  # not enough room in this region

    old_to_new = {artifact.layout[lq]: newp for lq, newp in zip(affected_logical, pool)}
    if len(set(old_to_new.values())) != len(old_to_new):
        return None
    # A candidate that leaves ANY drifted in-use qubit where it is (including an
    # identity relabel, which happens whenever the region offers no other free
    # qubit) does not repair the drift. It would pass verification trivially and
    # then be miscounted as a successful local patch, so it is never generated.
    if any(old == new for old, new in old_to_new.items()):
        return None

    n_phys = artifact.coupling_graph.number_of_nodes()
    perm = _build_full_permutation(old_to_new, n_phys)
    new_layout = {lq: perm[pq] for lq, pq in artifact.layout.items()}
    new_circuit = _relabel_circuit(artifact.compiled_circuit, perm)
    new_ops = relabel_operation_records(artifact.operations, perm, region_id=region.region_id)

    changed_ids = tuple(
        new.node_id for new, old in zip(new_ops, artifact.operations)
        if new.physical_qubits != old.physical_qubits
    )
    touched_ops = tuple(region.affected_operation_ids)

    return PatchCandidate(
        candidate_id=f"cand-g{artifact.generation}-s{drift_event.step}-{candidate_type}", candidate_type=candidate_type,
        touched_physical_qubits=tuple(sorted(set(old_to_new) | set(old_to_new.values()))),
        touched_logical_qubits=tuple(sorted(affected_logical)),
        touched_operation_ids=touched_ops, changed_operation_ids=changed_ids,
        new_layout=new_layout, physical_permutation=perm, inserted_swaps=(),
        added_two_qubit_ops=0, estimated_depth_delta=0,
        estimated_cost=float(len(affected_logical) * len(region.physical_qubits)),
        estimated_error=sum(calib_snapshot.qubit_error(p) for p in old_to_new.values()),
        compiled_circuit=new_circuit, operation_records=tuple(new_ops),
        new_input_layout={lq: perm[p] for lq, p in artifact.input_layout.items()},
    )


def generate_swap_candidate(artifact, drift_event, region, calib_snapshot, max_chain_length: int = 2):
    """
    Candidate B: LOCAL_SWAP, v1 safe subset only.

    Fires only when:
      - exactly one physical qubit (hosting exactly one logical qubit) has
        drifted -- simultaneous multi-qubit drift is explicitly out of
        scope for this candidate type in v1 (see README);
      - a direct relabel within the region is not already available
        (PURE_RELABEL covers that case more cheaply, with zero added
        gates);
      - a path of length <= max_chain_length exists, using only edges
        inside the region, from the drifted physical qubit to a target,
        where EVERY qubit on the path -- every bridge AND the target --
        is globally idle in the CURRENT compiled circuit. An occupied
        qubit is never treated as an acceptable target or bridge,
        regardless of what it is used for.
    """
    if region.too_large:
        return None
    drifted_phys = set(drift_event.drifted_qubits) & set(artifact.layout.values())
    if len(drifted_phys) != 1:
        return None
    old_p = next(iter(drifted_phys))
    affected_logical = [lq for lq, pq in artifact.layout.items() if pq == old_p]
    if len(affected_logical) != 1:
        return None
    lq = affected_logical[0]

    idle = _idle_physical_qubits(artifact)
    sub = artifact.coupling_graph.subgraph(region.physical_qubits)

    best_path = None
    for target in sorted(idle & set(region.physical_qubits)):
        if target == old_p:
            continue
        try:
            path = nx.shortest_path(sub, old_p, target)
        except nx.NetworkXNoPath:
            continue
        n_swaps = len(path) - 1
        if n_swaps < 1 or n_swaps > max_chain_length:
            continue
        bridges = path[1:-1]
        if not all(b in idle for b in bridges):
            continue  # a bridge is occupied -- reject, never assume it is safe
        if best_path is None or n_swaps < len(best_path) - 1:
            best_path = path
    if best_path is None:
        return None

    target_p = best_path[-1]
    swap_edges = [(best_path[i], best_path[i + 1]) for i in range(len(best_path) - 1)]

    n_phys = artifact.coupling_graph.number_of_nodes()
    perm = _build_full_permutation({old_p: target_p}, n_phys)
    relabelled_tail = _relabel_circuit(artifact.compiled_circuit, perm)

    new_circuit = relabelled_tail.copy_empty_like()
    swap_records = []
    for idx, (a, b) in enumerate(swap_edges):
        new_circuit.swap(a, b)
        swap_records.append(SwapInsertion(position=idx, physical_edge=(a, b), node_id=f"swap-g{artifact.generation}-s{drift_event.step}-{idx}"))
    for instr in relabelled_tail.data:
        new_circuit.append(instr.operation, instr.qubits, instr.clbits)

    new_layout = {lq2: perm[pq2] for lq2, pq2 in artifact.layout.items()}
    tail_ops = relabel_operation_records(artifact.operations, perm, region_id=region.region_id)
    swap_ops = tuple(
        OperationRecord(
            node_id=s.node_id, operation_index=s.position, op_type="swap",
            logical_qubits=(None, None), physical_qubits=s.physical_edge,
            region_id=region.region_id, affected_by_drift=True,
        )
        for s in swap_records
    )
    new_ops = swap_ops + tuple(tail_ops)

    changed_ids = tuple(
        new.node_id for new, old in zip(tail_ops, artifact.operations)
        if new.physical_qubits != old.physical_qubits
    )
    touched_ops = tuple(region.affected_operation_ids)

    return PatchCandidate(
        candidate_id=f"cand-g{artifact.generation}-s{drift_event.step}-LOCAL_SWAP", candidate_type=LOCAL_SWAP,
        touched_physical_qubits=tuple(sorted(set(best_path))),
        touched_logical_qubits=(lq,),
        touched_operation_ids=touched_ops, changed_operation_ids=changed_ids,
        new_layout=new_layout, physical_permutation=perm,
        inserted_swaps=tuple(swap_records), added_two_qubit_ops=len(swap_records),
        estimated_depth_delta=len(swap_records),
        estimated_cost=float(len(swap_records) * 3 + len(region.physical_qubits)),
        estimated_error=sum(calib_snapshot.edge_err(a, b) for (a, b) in swap_edges) * 3,
        compiled_circuit=new_circuit, operation_records=new_ops,
        # the SWAP prefix acts on the ORIGINAL wires, so inputs stay where they were
        new_input_layout=dict(artifact.input_layout),
    )
