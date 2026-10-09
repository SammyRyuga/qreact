import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from compiler.circuits import build_logical_circuit
from compiler.topology import build_topology
from compiler.compilation import compile_baseline, extract_layout
from compiler.artifact import make_artifact
from calibration.synthetic import SyntheticCalibrationProvider


@pytest.fixture
def setup():
    qc = build_logical_circuit(4)
    coupling, edges = build_topology(8)
    compiled, _ = compile_baseline(qc, coupling, seed=11)
    layout = extract_layout(compiled, 4)
    seq = SyntheticCalibrationProvider(coupling.number_of_nodes(), edges, seed=11).sequence(15)
    artifact = make_artifact(0, qc, compiled, coupling, layout, seq[0], seq[0])
    return {"qc": qc, "coupling": coupling, "edges": edges, "artifact": artifact, "seq": seq}
