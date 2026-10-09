import numpy as np, pytest
from calibration.synthetic import SyntheticCalibrationProvider
from calibration.provider import IBMCalibrationProvider

EDGES = [(0, 1), (1, 2), (2, 3), (0, 3)]


def test_same_seed_reproduces_exact_sequence():
    a = SyntheticCalibrationProvider(4, EDGES, seed=5).sequence(12)
    b = SyntheticCalibrationProvider(4, EDGES, seed=5).sequence(12)
    for x, y in zip(a, b):
        assert np.array_equal(x.readout_err, y.readout_err)
        assert dict(x.gate_err_2q) == dict(y.gate_err_2q)


def test_different_seed_differs():
    a = SyntheticCalibrationProvider(4, EDGES, seed=5).sequence(3)
    b = SyntheticCalibrationProvider(4, EDGES, seed=6).sequence(3)
    assert not np.array_equal(a[0].readout_err, b[0].readout_err)


def test_snapshot_is_immutable():
    snap = SyntheticCalibrationProvider(4, EDGES, seed=5).get_snapshot()
    with pytest.raises(ValueError):
        snap.readout_err[0] = 1.0
    with pytest.raises(TypeError):
        snap.gate_err_2q[(0, 1)] = 1.0


def test_old_snapshot_not_corrupted_by_advance():
    p = SyntheticCalibrationProvider(4, EDGES, seed=5)
    s0 = p.get_snapshot()
    before = s0.readout_err.copy()
    p.advance(); p.advance()
    assert np.array_equal(s0.readout_err, before)


def test_ibm_provider_is_an_unusable_stub():
    with pytest.raises(NotImplementedError):
        IBMCalibrationProvider(object())
