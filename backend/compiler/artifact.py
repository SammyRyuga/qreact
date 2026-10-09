"""
Sidecar metadata tracked alongside a compiled Qiskit circuit.

Qiskit's own QuantumCircuit/DAGCircuit remains the actual, executable
representation -- this module does NOT replace it or stuff metadata into
its internal objects (explicitly ruled out as fragile in this project's
design principles). Instead, CompiledArtifact keeps an ordered list of
OperationRecord "receipts" alongside the real circuit, so that "only this
part of the compiled artifact is invalid" has an explicit, inspectable
representation.

node_id is the stable identity, tracked independently of list position:
  - A pure relabel (see repair/candidates.py) preserves operation COUNT
    and ORDER exactly, so every node_id carries over unchanged; only a
    record's `physical_qubits` field may differ.
  - A SWAP-chain patch inserts new operations, so new OperationRecords are
    minted only for the newly-inserted SWAPs; every pre-existing record
    keeps its own node_id even though its position in the list shifts.
  - A full retranspile starts an entirely new artifact generation with
    entirely new node_ids -- nothing from a discarded circuit is
    meaningful to carry forward across a full recompile.
"""
from __future__ import annotations
from dataclasses import dataclass, field, replace
import uuid


def _new_node_id() -> str:
    return f"op-{uuid.uuid4().hex[:12]}"


@dataclass
class OperationRecord:
    node_id: str
    operation_index: int          # position in the circuit's operation list AT THE TIME this was built
    op_type: str                  # e.g. "h", "cx", "rz", "measure", "swap"
    logical_qubits: tuple
    physical_qubits: tuple
    region_id: str | None = None
    dirty: bool = False
    calibration_ref_step: int | None = None
    affected_by_drift: bool = False


@dataclass
class CompiledArtifact:
    generation: int
    logical_circuit: object            # qiskit QuantumCircuit (logical, uncompiled)
    compiled_circuit: object           # qiskit QuantumCircuit (compiled, physical)
    coupling_graph: object             # networkx Graph
    layout: dict                       # logical -> physical
    baseline_snapshot: object = None   # CalibrationSnapshot this artifact's logical circuit was FIRST compiled against
    validated_snapshot: object = None  # CalibrationSnapshot each physical qubit is currently validated against
    operations: list = field(default_factory=list)
    input_layout: dict = None          # logical -> physical wire where each logical qubit's INPUT state lives
    physical_to_logical: dict = field(init=False)

    def __post_init__(self):
        self.physical_to_logical = {p: l for l, p in self.layout.items()}
        if self.input_layout is None:
            # compile_baseline pins the initial layout to physical 0..n_log-1
            self.input_layout = {i: i for i in range(len(self.layout))}

    def operation_by_id(self, node_id: str):
        for op in self.operations:
            if op.node_id == node_id:
                return op
        return None

    def operations_touching_physical(self, physical_qubits: set) -> list:
        return [op for op in self.operations if physical_qubits.intersection(op.physical_qubits)]


def build_operation_records(compiled_circuit, layout: dict, calibration_ref_step: int | None = None,
                             generation: int = 0) -> list:
    """
    Build a fresh, freshly-identified operation list for a NEWLY compiled
    circuit (initial compile or full retranspile -- i.e. a new artifact
    generation, where no prior node_id is meaningful to preserve).

    logical_qubits is built POSITIONALLY matched to physical_qubits (index
    i of one corresponds to index i of the other), which matters for
    multi-qubit gates where operand order is meaningful (e.g. CX
    control/target).
    """
    phys_to_log = {p: l for l, p in layout.items()}
    records = []
    for idx, instr in enumerate(compiled_circuit.data):
        phys = tuple(compiled_circuit.find_bit(q).index for q in instr.qubits)
        logical = tuple(phys_to_log.get(p) for p in phys)
        records.append(OperationRecord(
            node_id=f"g{generation}-op{idx}", operation_index=idx, op_type=instr.operation.name,
            logical_qubits=logical, physical_qubits=phys,
            calibration_ref_step=calibration_ref_step,
        ))
    return records


def relabel_operation_records(old_records, perm: dict, region_id: str | None = None) -> list:
    """
    Build the operation-record list for a pure relabel: same node_ids, same
    order, only physical_qubits (via perm) updated. Records whose physical
    qubits actually changed are tagged with `region_id` and
    `affected_by_drift=True`; everything else is returned byte-identical.
    """
    new_records = []
    for rec in old_records:
        new_phys = tuple(perm.get(p, p) for p in rec.physical_qubits)
        changed = new_phys != rec.physical_qubits
        if changed:
            new_records.append(replace(
                rec, physical_qubits=new_phys, region_id=region_id, affected_by_drift=True,
            ))
        else:
            new_records.append(rec)
    return new_records


def make_artifact(generation, logical_circuit, compiled_circuit, coupling_graph, layout,
                   baseline_snapshot, validated_snapshot, input_layout=None) -> CompiledArtifact:
    ops = build_operation_records(
        compiled_circuit, layout,
        calibration_ref_step=validated_snapshot.step if validated_snapshot is not None else None,
        generation=generation,
    )
    return CompiledArtifact(
        generation=generation, logical_circuit=logical_circuit, compiled_circuit=compiled_circuit,
        coupling_graph=coupling_graph, layout=layout, baseline_snapshot=baseline_snapshot,
        validated_snapshot=validated_snapshot, operations=ops, input_layout=input_layout,
    )
