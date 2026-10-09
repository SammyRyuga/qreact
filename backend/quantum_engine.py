"""
Compatibility shim. The original monolithic quantum_engine.py has been
split into the compiler/, calibration/, drift/, repair/, verification/,
execution/, events/ and metrics/ packages. Names that external scripts
commonly imported are re-exported here; CalibrationSource is now
calibration.synthetic.SyntheticCalibrationProvider (immutable snapshots
instead of a mutable, deep-copied object) and run_incremental is now
execution.experiment.ExperimentRunner.run_incremental_strategy.
"""
from compiler.circuits import build_logical_circuit            # noqa: F401
from compiler.topology import build_topology, pinned_initial_layout  # noqa: F401
from compiler.compilation import extract_layout as _extract_layout   # noqa: F401
from execution.strategies import run_static, run_full_retranspile    # noqa: F401
from execution.simulation import circuit_png_base64                  # noqa: F401
from calibration.synthetic import SyntheticCalibrationProvider as CalibrationSource  # noqa: F401
