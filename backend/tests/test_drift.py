import numpy as np
from calibration.models import CalibrationSnapshot
from drift.detector import DriftDetector

EDGES = [(0, 1), (1, 2), (2, 3)]


def snap(ro, g1=None, g2=None, step=0):
    return CalibrationSnapshot(step, 4, EDGES, ro, g1 or [0.001] * 4, g2 or {e: 0.01 for e in EDGES})


def test_below_threshold_is_no_drift():
    base = snap([0.02] * 4)
    cur = snap([0.02 * 1.1] * 4)
    ev = DriftDetector(threshold=0.35).detect(cur, base, [0, 1, 2, 3], [], step=1)
    assert not ev.has_drift and ev.trigger_reason == "none"


def test_above_threshold_reports_reason_and_delta():
    base = snap([0.02] * 4)
    cur = snap([0.02, 0.02, 0.05, 0.02])
    ev = DriftDetector(threshold=0.35).detect(cur, base, [0, 1, 2, 3], [], step=3)
    assert ev.drifted_qubits == (2,)
    assert ev.qubit_delta_by_resource[2] > 0.35
    assert ev.trigger_reason == "relative_calibration_change" and ev.step == 3


def test_multi_qubit_drift():
    base = snap([0.02] * 4)
    cur = snap([0.06, 0.02, 0.06, 0.06])
    ev = DriftDetector(threshold=0.35).detect(cur, base, [0, 1, 2, 3], [], step=1)
    assert set(ev.drifted_qubits) == {0, 2, 3}


def test_only_in_use_qubits_considered():
    base = snap([0.02] * 4)
    cur = snap([0.02, 0.02, 0.02, 0.09])
    ev = DriftDetector(threshold=0.35).detect(cur, base, [0, 1, 2], [], step=1)
    assert not ev.has_drift


def test_edge_drift_detected_when_enabled():
    base = snap([0.02] * 4)
    cur = snap([0.02] * 4, g2={(0, 1): 0.01, (1, 2): 0.05, (2, 3): 0.01})
    ev = DriftDetector(threshold=0.35, detect_edges=True, edge_threshold=0.35).detect(
        cur, base, [0, 1, 2, 3], [(0, 1), (1, 2), (2, 3)], step=1)
    assert ev.drifted_edges == ((1, 2),) and ev.drifted_qubits == ()
    assert (1, 2) in ev.affected_resources


def test_edge_drift_ignored_when_disabled():
    base = snap([0.02] * 4)
    cur = snap([0.02] * 4, g2={(0, 1): 0.01, (1, 2): 0.05, (2, 3): 0.01})
    ev = DriftDetector(threshold=0.35, detect_edges=False).detect(
        cur, base, [0, 1, 2, 3], [(1, 2)], step=1)
    assert not ev.has_drift


def test_edge_threshold_is_separate_and_defaults_to_double():
    assert DriftDetector(threshold=0.3).edge_threshold == 0.6
    assert DriftDetector(threshold=0.3, edge_threshold=0.4).edge_threshold == 0.4
