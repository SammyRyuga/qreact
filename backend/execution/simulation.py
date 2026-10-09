"""Noisy simulation and circuit rendering -- unchanged mathematically from
the original prototype's _simulate_fidelity / circuit_png_base64."""
from __future__ import annotations
import base64
import io

from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError
from qiskit.quantum_info import hellinger_fidelity


def build_noise_model(snapshot, active_qubits) -> NoiseModel:
    nm = NoiseModel()
    for q in active_qubits:
        p1 = snapshot.gate_err_1q[q]
        nm.add_quantum_error(depolarizing_error(p1, 1), ['u1', 'u2', 'u3', 'rz', 'sx', 'x', 'h'], [q])
        ro = snapshot.readout_err[q]
        nm.add_readout_error(ReadoutError([[1 - ro, ro], [ro, 1 - ro]]), [q])
    for (a, b), p2 in snapshot.gate_err_2q.items():
        if a in active_qubits and b in active_qubits:
            nm.add_quantum_error(depolarizing_error(p2, 2), ['cx'], [a, b])
    return nm


def simulate_fidelity(compiled_circ, snapshot, layout, shots: int = 2048) -> float:
    active = sorted(set(layout.values()))
    nm = build_noise_model(snapshot, active)
    sim = AerSimulator(noise_model=nm)
    counts = sim.run(compiled_circ, shots=shots, seed_simulator=1234 + snapshot.step).result().get_counts()

    ideal_sim = AerSimulator()
    ideal_counts = ideal_sim.run(compiled_circ, shots=shots, seed_simulator=4321 + snapshot.step).result().get_counts()

    def normalize(c):
        total = sum(c.values())
        return {k: v / total for k, v in c.items()}

    return hellinger_fidelity(normalize(counts), normalize(ideal_counts))


def circuit_png_base64(circ, fold: int = -1) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = circ.draw(output="mpl", fold=fold)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")
