"""
Preservation verification.

The invariant (per explicit correction to the Phase 2 plan) is NOT
"byte-identical" in the sense of list position: once a candidate can
insert new operations (the LOCAL_SWAP candidate type), a preserved
operation's position in the circuit's operation list can shift even
though the operation itself is untouched. Identity is tracked via
OperationRecord.node_id, not position.

The actual invariant:
    Operations OUTSIDE the declared repair region remain
    structurally/semantically unchanged; only explicitly permitted
    fields of operations INSIDE the region may change.

Permitted mutation, for an operation whose node_id is inside the region's
`affected_operation_ids` (interior):
  - physical_qubits (reassigned via the accepted permutation)
A region operation may NOT have its op_type or logical_qubits changed by
any candidate type currently implemented -- a candidate that does so is
not a bug to patch around, it is rejected outright.

A brand-new operation (freshly minted node_id, e.g. an inserted SWAP) is
only permitted if its physical qubits lie entirely inside the region's
declared physical qubits.

Operations classified as `boundary` (touch the region but also touch a
qubit outside it -- see repair/region.py) are treated exactly like
outside/unaffected operations here: they may NOT change. Only
`affected_operation_ids` (interior) are eligible for permitted mutation.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PreservationResult:
    passed: bool
    changed_operation_ids: tuple
    unchanged_operation_ids: tuple
    inserted_operation_ids: tuple
    unexpected_changes: tuple     # human-readable strings; non-empty => passed is False


def check_preservation(before_ops, after_ops, region) -> PreservationResult:
    """
    before_ops, after_ops: list[OperationRecord]
    region: RepairRegion (must expose `affected_operation_ids` and
            `physical_qubits`; boundary ops are treated as non-modifiable)
    """
    before_by_id = {op.node_id: op for op in before_ops}
    after_by_id = {op.node_id: op for op in after_ops}
    interior_ids = set(region.affected_operation_ids)
    region_phys = set(region.physical_qubits)

    changed, unchanged, inserted, unexpected = [], [], [], []

    for node_id, before in before_by_id.items():
        after = after_by_id.get(node_id)
        if after is None:
            unexpected.append(f"operation {node_id} ({before.op_type}) was removed")
            continue
        if _structurally_equal(before, after):
            unchanged.append(node_id)
            continue
        # Something differs. Permitted ONLY if the op is declared interior
        # to the region (never for a boundary-classified op), and ONLY if
        # the sole difference is physical_qubits.
        if node_id not in interior_ids:
            classification = "boundary" if node_id in getattr(region, "boundary_operation_ids", ()) else "outside"
            unexpected.append(
                f"operation {node_id} ({before.op_type}) changed but is classified {classification} "
                f"the declared region, not interior"
            )
            continue
        if before.op_type != after.op_type:
            unexpected.append(f"operation {node_id} changed op_type ({before.op_type} -> {after.op_type})")
            continue
        if before.logical_qubits != after.logical_qubits:
            unexpected.append(
                f"operation {node_id} changed logical_qubits ({before.logical_qubits} -> {after.logical_qubits})"
            )
            continue
        # physical_qubits differs, op is interior, nothing else differs: permitted.
        changed.append(node_id)

    for node_id, after in after_by_id.items():
        if node_id in before_by_id:
            continue
        # Brand new operation (e.g. an inserted SWAP). Only permitted
        # entirely inside the region's declared physical qubits.
        if not set(after.physical_qubits).issubset(region_phys):
            unexpected.append(
                f"new operation {node_id} ({after.op_type}) on physical {after.physical_qubits} "
                f"lies outside the declared region {sorted(region_phys)}"
            )
            continue
        inserted.append(node_id)

    return PreservationResult(
        passed=(len(unexpected) == 0),
        changed_operation_ids=tuple(changed),
        unchanged_operation_ids=tuple(unchanged),
        inserted_operation_ids=tuple(inserted),
        unexpected_changes=tuple(unexpected),
    )


def _structurally_equal(a, b) -> bool:
    return (a.op_type == b.op_type and a.logical_qubits == b.logical_qubits
            and a.physical_qubits == b.physical_qubits)


def check_records_match_circuit(records, circuit) -> tuple:
    """The sidecar OperationRecords a candidate supplies are only metadata. The
    verifier must not trust them: they have to describe the circuit that would
    actually be deployed, operation by operation (same count, same op_type, same
    physical operands, same order). Without this, a candidate could change the
    real circuit while its records claimed nothing changed -- and the
    preservation check, which diffs records, would pass it."""
    violations = []
    if len(records) != len(circuit.data):
        violations.append(
            f"operation records ({len(records)}) do not match the circuit ({len(circuit.data)} operations)")
        return (False, violations)
    for idx, (rec, instr) in enumerate(zip(records, circuit.data)):
        phys = tuple(circuit.find_bit(q).index for q in instr.qubits)
        if rec.op_type != instr.operation.name or tuple(rec.physical_qubits) != phys:
            violations.append(
                f"record {rec.node_id} at position {idx} claims {rec.op_type}{tuple(rec.physical_qubits)} "
                f"but the circuit has {instr.operation.name}{phys}")
    return (len(violations) == 0, violations)
