"""
Calibration provider abstraction.

The rest of the system depends only on `CalibrationProvider.get_snapshot()`
/ `.advance()` returning CalibrationSnapshot objects -- it does not care
whether they came from a synthetic random walk or a real device. This is
the seam described in the project report: swapping
SyntheticCalibrationProvider for a real backend-backed provider requires
no change anywhere else in the codebase.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from .models import CalibrationSnapshot


class CalibrationProvider(ABC):
    @abstractmethod
    def get_snapshot(self) -> CalibrationSnapshot:
        """Return the current calibration snapshot without advancing time."""
        raise NotImplementedError

    @abstractmethod
    def advance(self) -> CalibrationSnapshot:
        """Advance to the next calibration state and return its snapshot."""
        raise NotImplementedError


class IBMCalibrationProvider(CalibrationProvider):
    """
    STUB ONLY. Not implemented, not used anywhere in this codebase, and not
    required for the current demo or evaluation -- constructing it raises
    immediately rather than silently returning fake data, so it can never
    be accidentally mistaken for a working integration.

    Intended future shape: `IBMCalibrationProvider(backend)` wrapping a
    qiskit_ibm_runtime backend, reading `backend.properties()` (readout
    error, 1Q/2Q gate error, T1/T2, coupling map, calibration timestamp)
    into CalibrationSnapshot objects. No other module would need to change
    to support this once implemented.
    """

    def __init__(self, backend):
        raise NotImplementedError(
            "IBMCalibrationProvider is an interface stub for future live-hardware "
            "integration and is intentionally not implemented in this version. "
            "See calibration/provider.py and the README's 'Future Work' section."
        )

    def get_snapshot(self) -> CalibrationSnapshot:
        raise NotImplementedError

    def advance(self) -> CalibrationSnapshot:
        raise NotImplementedError
