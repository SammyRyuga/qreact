import { Play, SlidersHorizontal } from "lucide-react"
import "./ExperimentConfig.css"

function ExperimentConfig() {
  return (
    <section className="experiment-config">
      <div className="experiment-config-header">
        <div>
          <div className="section-kicker">EXPERIMENT CONFIGURATION</div>

          <h2>Configure the compiler run.</h2>
        </div>

        <div className="config-mode">
          <SlidersHorizontal size={14} />
          <span>LOCAL SIMULATION</span>
        </div>
      </div>

      <div className="config-grid">
        <div className="config-field">
          <label>LOGICAL QUBITS</label>

          <input
            type="number"
            defaultValue={4}
            min={3}
            max={5}
          />

          <span>Width of the input circuit</span>
        </div>

        <div className="config-field">
          <label>PHYSICAL QUBITS</label>

          <input
            type="number"
            defaultValue={8}
            min={6}
            max={10}
          />

          <span>Available hardware resources</span>
        </div>

        <div className="config-field">
          <label>DRIFT STEPS</label>

          <input
            type="number"
            defaultValue={15}
            min={5}
            max={30}
          />

          <span>Calibration snapshots</span>
        </div>

        <div className="config-field">
          <label>DRIFT THRESHOLD</label>

          <input
            type="number"
            defaultValue={0.35}
            min={0.1}
            max={0.6}
            step={0.05}
          />

          <span>Trigger threshold</span>
        </div>

        <div className="config-field">
          <label>SEED</label>

          <input
            type="number"
            defaultValue={11}
            min={0}
            max={999}
          />

          <span>Reproducible drift trace</span>
        </div>
      </div>

      <div className="config-footer">
        <div className="config-note">
          <span className="config-dot"></span>

          <span>
            All three recompilation strategies will use the same
            calibration trace.
          </span>
        </div>

        <button className="run-button" type="button">
          <Play size={14} fill="currentColor" />
          <span>RUN EXPERIMENT</span>
        </button>
      </div>
    </section>
  )
}

export default ExperimentConfig