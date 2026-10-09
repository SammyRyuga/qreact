"""
Local prototype server for:
  Incremental Calibration-Reactive Recompilation: Localized, Verified
  Circuit Rewriting on Drift-Prone Quantum Processors
  (BCSE307P Compiler Design Lab, VIT Vellore)

    pip install -r requirements.txt
    python app.py        ->  http://localhost:5000

POST /api/run keeps its original request fields (n_log, n_phys, n_steps,
threshold, seed) and every original response key (config, summary,
equivalence, log, charts, example, circuit_png). New keys are purely
additive: events, repair, metrics. Calibration is SYNTHETIC (seeded random
walk); no live IBM hardware data is used anywhere.
"""
import base64
import io
from math import isfinite, isclose
from werkzeug.exceptions import BadRequest
import traceback

from flask import Flask, render_template, request, jsonify
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from compiler.circuits import build_logical_circuit
from compiler.topology import build_topology
from calibration.synthetic import SyntheticCalibrationProvider
from execution.experiment import ExperimentRunner
from execution.strategies import run_static, run_full_retranspile
from execution.simulation import circuit_png_base64
from metrics.metrics import (
    compute_strategy_metrics, compute_incremental_metrics, compute_comparative_metrics)

app = Flask(__name__)


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def _comparison_chart(title, ylabel, values, fmt="{:.4f}") -> str:
    labels = ["Static", "Full\nRetranspile", "Incremental\n(this work)"]
    colors = ["#9aa5b1", "#e0793c", "#2f6f4f"]
    fig, ax = plt.subplots(figsize=(5, 3.6))
    bars = ax.bar(labels, values, color=colors, width=0.55)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    top = max(values) if max(values) > 0 else 1
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + top * 0.02, fmt.format(v), ha="center", fontsize=9)
    ax.set_ylim(0, top * 1.25)
    fig.tight_layout()
    return _fig_to_base64(fig)


def _repair_bundle(repair_records) -> dict:
    """One representative drift event (the first one that produced an
    accepted patch, else the first drift event), in the structure a
    frontend needs to visualize drift -> region -> candidates ->
    verification -> decision/fallback."""
    if not repair_records:
        return {"step": None, "drift_event": None, "region": None, "candidates": [],
                "selected_candidate": None, "verification": None, "fallback": None}
    rec = next((r for r in repair_records if r["selected_candidate"]), repair_records[0])
    selected = next((c for c in rec["candidates"] if c["candidate_id"] == rec["selected_candidate"]), None)
    shown = selected or (rec["candidates"][0] if rec["candidates"] else None)
    return {
        "step": rec["step"], "drift_event": rec["drift_event"], "region": rec["region"],
        "candidates": rec["candidates"], "selected_candidate": selected,
        "verification": shown["verification"] if shown else None, "fallback": rec["fallback"],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/run", methods=["POST"])
def api_run():

    try:
        # Parse JSON safely. Malformed JSON should be a client error.
        try:
            cfg = request.get_json(force=True)
        except BadRequest:
            return jsonify({
                "ok": False,
                "error": "Request body must contain valid JSON."
            }), 400

        # Only JSON objects are valid request bodies.
        if not isinstance(cfg, dict):
            return jsonify({
                "ok": False,
                "error": "Request body must be a JSON object."
            }), 400

        def read_integer(name, default, minimum, maximum):
            value = cfg.get(name, default)

            # bool is a subclass of int in Python, so reject it explicitly.
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(
                    f"'{name}' must be an integer."
                )

            if not minimum <= value <= maximum:
                raise ValueError(
                    f"'{name}' must be between "
                    f"{minimum} and {maximum}."
                )

            return value


        def read_finite_number(name, default):
            value = cfg.get(name, default)

            if isinstance(value, bool) or not isinstance(
                value, (int, float)
            ):
                raise ValueError(
                    f"'{name}' must be a finite number."
                )

            try:
                value = float(value)
            except (OverflowError, ValueError):
                raise ValueError(
                    f"'{name}' must be a finite number."
                )
            if not isfinite(value):
                raise ValueError(
                    f"'{name}' must be a finite number."
                )

            return value



        def read_boolean(name, default):
            value = cfg.get(name, default)

            if not isinstance(value, bool):
                raise ValueError(
                    f"'{name}' must be true or false."
                )

            return value

        # Validate all input fields before running the experiment.
        try:
            n_log = read_integer("n_log", 4, 3, 5)

            n_phys = read_integer(
                "n_phys", 8, n_log + 2, 16
            )

            n_steps = read_integer(
                "n_steps", 15, 5, 30
            )

            threshold = read_finite_number(
                "threshold", 0.35
            )

            if not 0.10 <= threshold <= 0.60:
                raise ValueError(
                    "'threshold' must be between 0.10 and 0.60."
                )

            grid_index = round((threshold - 0.10) / 0.05)
            grid_value = 0.10 + grid_index * 0.05

            if not isclose(
                threshold, grid_value,
                rel_tol=0.0, abs_tol=1e-9
            ):
                raise ValueError(
                    "'threshold' must use increments of 0.05."
                )

            seed = read_integer("seed", 7, 0, 999)

            demo_mode = read_boolean("demo_mode", False)
            detect_edges = read_boolean("detect_edges", False)

            edge_threshold_value = cfg.get(
                "edge_threshold", None
            )

            if edge_threshold_value is None:
                edge_threshold = None
            else:
                edge_threshold = read_finite_number(
                    "edge_threshold", None
                )

                if edge_threshold < 0:
                    raise ValueError(
                        "'edge_threshold' must be non-negative."
                    )

        except ValueError as exc:
            return jsonify({
                "ok": False,
                "error": str(exc)
            }), 400

        # Build and verify the requested topology.
        qc = build_logical_circuit(n_log)

        n_main = max(3, n_log, n_phys // 2)
        coupling, edges = build_topology(
            n_phys, n_main=n_main
        )

        if set(coupling.nodes()) != set(range(n_phys)):
            raise RuntimeError(
                f"Topology node mismatch: requested {n_phys}, "
                f"got {sorted(coupling.nodes())}"
            )

        if coupling.number_of_nodes() != n_phys:
            raise RuntimeError(
                f"Topology has {coupling.number_of_nodes()} nodes; "
                f"expected {n_phys}"
            )

        if any(a not in coupling or b not in coupling for a, b in edges):
            raise RuntimeError(
                "Topology edge references an unknown physical qubit"
            )

        provider = SyntheticCalibrationProvider(
            coupling.number_of_nodes(), edges, seed=seed
        )

        calib_sequence = provider.sequence(n_steps)

        runner = ExperimentRunner(threshold=threshold, detect_edges=detect_edges, edge_threshold=edge_threshold)
        r_static = run_static(qc, coupling, calib_sequence, seed)
        r_full = run_full_retranspile(qc, coupling, calib_sequence, seed, threshold=threshold)
        r_inc = runner.run_incremental_strategy(qc, coupling, calib_sequence, seed, capture_example=True)

        m_static = compute_strategy_metrics(r_static)
        m_full = compute_strategy_metrics(r_full)
        m_inc = compute_strategy_metrics(r_inc)

        def legacy_summary(m):
            # original keys, original types
            return {"mean_fidelity": m["mean_fidelity"], "total_cost": int(round(m["total_cost"])),
                    "num_recompiles": m["num_recompiles"], "gini_usage": m["gini_usage"]}

        summary = {"static": legacy_summary(m_static), "full": legacy_summary(m_full),
                   "incremental": legacy_summary(m_inc)}

        eq = r_inc["equivalence_checks"]
        n_pass = sum(1 for c in eq if c)
        equivalence = {"passed": n_pass, "failed_fallback": len(eq) - n_pass}

        metrics = {
            "static": m_static, "full": m_full, "incremental": m_inc,
            "incremental_repair": compute_incremental_metrics(r_inc, n_steps),
            "comparative": compute_comparative_metrics(m_static, m_full, m_inc),
            "notes": {
                "calibration_source": "synthetic seeded random walk (not live IBM telemetry)",
                "total_cost_unit": "compiler_work_units (modelled, NOT wall-clock milliseconds)",
                "gini_usage": "Gini coefficient of physical-qubit usage across the experiment",
            },
        }

        charts = {
            "fidelity": _comparison_chart(
                "Mean Fidelity by Strategy",
                "Fidelity (noisy AerSimulator)",
                [
                    m_static["mean_fidelity"],
                    m_full["mean_fidelity"],
                    m_inc["mean_fidelity"],
                ],
            ),
            "cost": _comparison_chart(
                "Recompilation Cost by Strategy",
                "compiler work units",
                [
                    m_static["total_cost"],
                    m_full["total_cost"],
                    m_inc["total_cost"],
                ],
                fmt="{:.0f}",
            ),
            "gini": _comparison_chart(
                "Qubit-Usage Concentration by Strategy",
                "Gini coefficient",
                [
                    m_static["gini_usage"],
                    m_full["gini_usage"],
                    m_inc["gini_usage"],
                ],
            ),
        }

        return jsonify({
            "ok": True,

            "config": {
                "n_log": n_log,
                "n_phys": coupling.number_of_nodes(),
                "n_steps": n_steps,
                "threshold": threshold,
                "seed": seed,
                "demo_mode": demo_mode,
                "detect_edges": detect_edges,
                "edge_threshold": edge_threshold,
            },

            # Actual physical topology used by this experiment.
            "topology": {
                "n_qubits": coupling.number_of_nodes(),
                "edges": [
                    list(edge)
                    for edge in coupling.edges()
                ],
            },

            "summary": summary,
            "equivalence": equivalence,
            "events": r_inc["events"].as_list(),
            "log": r_inc["log"],
            "repair": _repair_bundle(r_inc["repair_records"]),
            "patches": r_inc["patches"],
            "metrics": metrics,
            "charts": charts,
            "example": r_inc["example"],
            "circuit_png": circuit_png_base64(qc),
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(e),
        }), 500


if __name__ == "__main__":
    print("\n  Incremental Calibration-Reactive Recompilation -- local prototype")
    print("  Open http://localhost:5000 in your browser\n")
    app.run(host="127.0.0.1", port=5000, debug=False)