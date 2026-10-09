import { useState } from "react"
import {
  Play,
  SlidersHorizontal,
  LoaderCircle,
  CheckCircle2,
  AlertCircle,
} from "lucide-react"
import { runExperiment } from "../lib/api"
import "./ExperimentConfig.css"

function ExperimentConfig({ onResult }) {
  const [config, setConfig] = useState({
    n_log: 4,
    n_phys: 8,
    n_steps: 15,
    threshold: 0.35,
    seed: 11,
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  function updateConfig(event) {
    const { name, value } = event.target

    setConfig((previous) => ({
      ...previous,
      [name]: value === "" ? "" : Number(value),
    }))

    setError("")
    setSuccess("")
  }

  async function handleRun() {
    if (loading) return

    if (
      !Number.isInteger(config.n_log) ||
      config.n_log < 3 ||
      config.n_log > 5
    ) {
      setError("Logical qubits must be between 3 and 5.")
      return
    }

    if (
      !Number.isInteger(config.n_phys) ||
      config.n_phys < config.n_log + 2 ||
      config.n_phys > 10
    ) {
      setError(
        `Physical qubits must be between ${config.n_log + 2} and 10.`
      )
      return
    }

    if (
      !Number.isInteger(config.n_steps) ||
      config.n_steps < 5 ||
      config.n_steps > 30
    ) {
      setError("Drift steps must be between 5 and 30.")
      return
    }

    if (
      typeof config.threshold !== "number" ||
      config.threshold < 0.1 ||
      config.threshold > 0.6 ||
      Math.round(config.threshold * 100) % 5 !== 0
    ) {
      setError("Threshold must be between 0.1 and 0.6, in increments of 0.05.")
      return
    }

    if (
      !Number.isInteger(config.seed) ||
      config.seed < 0 ||
      config.seed > 999
    ) {
      setError("Seed must be an integer between 0 and 999.")
      return
    }

    try {
      setLoading(true)
      setError("")
      setSuccess("")

      const result = await runExperiment(config)

      if (typeof onResult === "function") {
        onResult(result)
      }

      setSuccess(
        `Experiment completed successfully · ${result.config.n_steps} calibration steps`
      )
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "The experiment could not be completed."
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="experiment-config">
      <div className="experiment-config-header">
        <div>
          <div
            className="section-kicker"
            style={{ marginBottom: "10px" }}
          >
            EXPERIMENT CONFIGURATION
          </div>

          <h2>Configure the compiler run.</h2>
        </div>

        <div className="config-mode">
          <SlidersHorizontal size={14} />
          <span>LOCAL SIMULATION</span>
        </div>
      </div>

      <div className="config-grid">
        <div className="config-field">
          <label htmlFor="n_log">LOGICAL QUBITS</label>

          <input
            id="n_log"
            name="n_log"
            type="number"
            value={config.n_log}
            onChange={updateConfig}
            min={3}
            max={5}
            disabled={loading}
          />

          <span>Width of the input circuit</span>
        </div>

        <div className="config-field">
          <label htmlFor="n_phys">PHYSICAL QUBITS</label>

          <input
            id="n_phys"
            name="n_phys"
            type="number"
            value={config.n_phys}
            onChange={updateConfig}
            min={config.n_log + 2}
            max={10}
            disabled={loading}
          />

          <span>Available hardware resources</span>
        </div>

        <div className="config-field">
          <label htmlFor="n_steps">DRIFT STEPS</label>

          <input
            id="n_steps"
            name="n_steps"
            type="number"
            value={config.n_steps}
            onChange={updateConfig}
            min={5}
            max={30}
            disabled={loading}
          />

          <span>Calibration snapshots</span>
        </div>

        <div className="config-field">
          <label htmlFor="threshold">DRIFT THRESHOLD</label>

          <input
            id="threshold"
            name="threshold"
            type="number"
            value={config.threshold}
            onChange={updateConfig}
            min={0.1}
            max={0.6}
            step={0.05}
            disabled={loading}
          />

          <span>Trigger threshold</span>
        </div>

        <div className="config-field">
          <label htmlFor="seed">SEED</label>

          <input
            id="seed"
            name="seed"
            type="number"
            value={config.seed}
            onChange={updateConfig}
            min={0}
            max={999}
            disabled={loading}
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

        <button
          className="run-button"
          type="button"
          onClick={handleRun}
          disabled={loading}
        >
          {loading ? (
            <LoaderCircle className="run-spinner" size={14} />
          ) : (
            <Play size={14} fill="currentColor" />
          )}

          <span>{loading ? "RUNNING EXPERIMENT..." : "RUN EXPERIMENT"}</span>
        </button>
      </div>

      {error && (
        <div
          role="alert"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "9px",
            marginTop: "18px",
            color: "#ff8f8f",
            fontSize: "0.85rem",
          }}
        >
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div
          role="status"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "9px",
            marginTop: "18px",
            color: "var(--mint)",
            fontSize: "0.85rem",
          }}
        >
          <CheckCircle2 size={16} />
          <span>{success}</span>
        </div>
      )}
    </section>
  )
}

export default ExperimentConfig