# Incremental Calibration-Reactive Recompilation — backend + local prototype

BCSE307P Compiler Design Lab, VIT Vellore.

**Calibration data is SYNTHETIC** (seeded random walk). Nothing here has been
validated on live IBM Quantum hardware; that is future work.

## Core mechanism

```
DRIFT -> AFFECTED RESOURCES -> BOUNDED REPAIR REGION -> LOCAL CANDIDATES -> SCORING
      -> DISRUPTION BUDGET -> TOPOLOGY CHECK -> SEMANTIC CHECK
      -> ACCEPT LOCAL PATCH   or   FULL RETRANSPILE FALLBACK
```

A local patch is deployed only if **every** verifier passes. Otherwise the
artifact is rebuilt by a real `transpile()` from the *original logical circuit*.

## Layout

| Package | Role |
|---|---|
| `calibration/` | immutable `CalibrationSnapshot`; `CalibrationProvider` seam; `SyntheticCalibrationProvider`; `IBMCalibrationProvider` (**stub that raises** — not implemented) |
| `compiler/` | logical circuit, twin-qubit topology, shared `compile_baseline`, `CompiledArtifact` + `OperationRecord` sidecar |
| `drift/` | `DriftDetector` (qubits **and** edges, separate thresholds) -> structured `DriftEvent` |
| `repair/` | `RepairRegionBuilder`, `DisruptionBudget`, candidate generators, `LocalRepairPlanner` (+ scoring), `RepairPatch` |
| `verification/` | topology, mapping, locality, preservation, semantic verifiers; `RepairVerifier` -> `VerificationResult` |
| `execution/` | `ExperimentRunner`, `FallbackController`, static/full strategies, noisy simulation |
| `events/`, `metrics/` | structured event log; all metrics |
| `app.py` | Flask API (`POST /api/run`), unchanged request shape |

`quantum_engine.py` is now a thin compatibility shim.

## Drift threshold vs. disruption budget (kept separate on purpose)

* `DriftDetector` threshold: *has the hardware changed enough to act?*
* `DisruptionBudget`: *is this repair small enough to count as incremental?*

## Repair region

Built from hardware locality (bounded BFS on the coupling graph) **and**
circuit locality. Every operation is classified **before any candidate exists**:
*interior* (all operands inside the region; the only operations a candidate may
change), *boundary* (touches the region and something outside; may **not**
change), or *outside*. Exceeding the qubit/operation/radius bound returns
`too_large` and goes straight to fallback. There is deliberately **no**
"retry with a bigger region" escalation.

## Candidates

* `PURE_RELABEL` — consistent renaming of physical wires inside the region.
* `LOCAL_SWAP` — **v1 safe subset only**: exactly one drifted logical qubit; a
  SWAP chain (<= 2) inside the region where **every bridge AND the target are
  globally idle**. An occupied target/bridge is never assumed safe. Built by
  direct instruction construction (never `transpile()`), SWAPs sit on real
  coupling edges, and the real Qiskit circuit is modified.
* `ALT_MAPPING` — same relabel mechanism, different deterministic tie-break.

A candidate that does not vacate every drifted in-use qubit (e.g. an identity
relabel) is **never generated** — it would pass verification trivially and be
miscounted as a repair. Scoring (`score = 1 - λ·cost - λ·depth - λ·swaps -
λ·changes - λ·region_fraction`, weights configurable) only orders candidates;
it never overrides verification.

## Verification (`RepairVerifier`)

1. topology — every 2Q op on a coupling edge
2. mapping — logical->physical is bijective
3. locality — candidate touches only region-interior operations/qubits
4. preservation — outside the region everything is structurally unchanged;
   inside it only `physical_qubits` may change (identity tracked by `node_id`,
   not list position). **Records must also match the real circuit** (a
   candidate cannot change the circuit while its metadata claims otherwise).
5. semantic — exact logical measurement distribution **and** randomized-input
   distributions (each circuit read through its own input/output layouts).
   Unavailable (e.g. too many qubits) = **fail**, never "assume equivalent".
6. disruption budget

## Fallback

`FallbackController` re-transpiles from the original logical circuit, extracts a
fresh layout, resets the calibration reference, bumps the generation. Reasons
are explicit (`region_too_large`, `no_feasible_candidate`, ...).

## Run

```
pip install -r requirements.txt
python app.py                  # http://localhost:5000
python -m pytest tests -q      # 51 tests
python run_evaluation.py       # qubit-only drift (original behaviour)
python run_evaluation.py --edges
```

## API

`POST /api/run` accepts `n_log, n_phys, n_steps, threshold, seed` plus optional
`demo_mode`, `detect_edges` (default **false**), `edge_threshold`. Original
response keys are unchanged (`config, summary, equivalence, log, charts,
example, circuit_png`); new additive keys: `events` (structured), `repair`
(`drift_event, region, candidates, selected_candidate, verification,
fallback`), `patches` (exact deltas incl. inserted SWAP positions), `metrics`.
Same seed => identical results (IDs and shot sampling are deterministic).

## Results of THIS version (5 seeds x 25 steps, 4 logical / 8 physical qubits)

Synthetic calibration, qubit-only drift detection:

| strategy | mean fidelity | mean cost (work units) | usage Gini |
|---|---|---|---|
| static | 0.9962 | 32 | 0.500 |
| full retranspile | 0.9962 | 339 | 0.137 |
| incremental | 0.9962 | 276 | 0.281 |

* 50 drift events: **9 local patches (18%)**, 41 full fallbacks.
* Cost saving vs full: **18.6%**. Fidelity: parity (differences are within shot noise).
* Accepted patches preserved on average **67%** of operations.
* Mean region (over all drift events, including ones that exceeded the bound) = 6.8 qubits = **84% of the chip** — on an 8-qubit device a
  6-qubit bound is barely "local". Locality is only meaningful on larger devices.
* **Usage concentration is WORSE for incremental (0.281) than full (0.137)** in this version.
  An earlier version of this project reported the opposite; that result did not
  survive the stricter implementation (no-op patches removed, records checked).

With `--edges`: 61 drift events, 3 local patches, 58 fallbacks, cost 377 vs full 339
(incremental reacts to edge drift; the full baseline remains qubit-only, so costs are not like-for-like).

## Known limitations

* Synthetic calibration only; no live-hardware validation.
* **Semantic equivalence = Z-basis measurement-outcome equivalence, not unitary
  equivalence.** This benchmark (H -> CX cascade -> RZ -> measure) is blind to
  phase-type (Z-type) errors: its output from |0..0> is exactly uniform, and
  Z-type Paulis commute to the measurement. The randomized-input check removes
  the uniformity blind spot, but phase-only errors (e.g. a dropped RZ) remain
  undetectable. A logical-unitary verifier is the natural next verifier.
* LOCAL_SWAP covers only single-qubit drift through idle qubits; no multi-qubit
  swap chains, no rerouting inside already-active regions.
* A patch resets the validated calibration snapshot for **all** resources, which
  can mask slow drift on qubits that were not flagged (full retranspile does the same).
* Edge detection uses a separate threshold (default 2x) because the synthetic
  model drifts 2Q error ~2x more volatile than qubit error; it is opt-in in the API.
* `OperationRecord.operation_index` is only meaningful at build time.
* Exact simulation is limited to <= 22 qubits (larger => verification unavailable => fallback).
* This code does not establish patentability.
