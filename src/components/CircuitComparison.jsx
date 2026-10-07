import {
  ArrowRight,
  CheckCircle2,
  GitCompareArrows,
  Layers3,
} from "lucide-react"
import "./CircuitComparison.css"

function CircuitPlaceholder({ variant }) {
  const isAfter = variant === "after"

  return (
    <div className={`circuit-placeholder ${isAfter ? "after" : "before"}`}>
      <div className="circuit-grid-lines"></div>

      {[0, 1, 2, 3].map((qubit) => (
        <div className="circuit-row" key={qubit}>
          <span className="qubit-label">q{qubit}</span>

          <div className="wire"></div>

          <div className="gate gate-a">
            H
          </div>

          <div className="gate gate-b">
            X
          </div>

          <div className="wire"></div>

          {qubit === 2 && (
            <div className={`circuit-highlight ${isAfter ? "changed" : ""}`}>
              {isAfter ? "PATCH" : "DRIFT"}
            </div>
          )}

          <div className="wire"></div>
        </div>
      ))}

      <div className="circuit-end-label">
        {isAfter ? "VERIFIED" : "ORIGINAL"}
      </div>
    </div>
  )
}

function CircuitComparison() {
  return (
    <section className="circuit-comparison">
      <div className="circuit-header">
        <div>
          <div className="section-kicker">CIRCUIT DELTA</div>

          <h2>Before and after the repair.</h2>
        </div>

        <div className="circuit-header-state">
          <GitCompareArrows size={14} />
          <span>LOCAL CHANGE VIEW</span>
        </div>
      </div>

      <div className="circuit-summary">
        <div className="circuit-summary-item">
          <Layers3 size={14} />
          <div>
            <span>REPAIR SCOPE</span>
            <strong>BOUNDED REGION</strong>
          </div>
        </div>

        <div className="circuit-summary-item">
          <CheckCircle2 size={14} />
          <div>
            <span>UNCHANGED REGION</span>
            <strong>PRESERVED</strong>
          </div>
        </div>

        <div className="circuit-summary-item">
          <GitCompareArrows size={14} />
          <div>
            <span>VERIFICATION</span>
            <strong>PENDING</strong>
          </div>
        </div>
      </div>

      <div className="circuit-pair">
        <article className="circuit-card">
          <div className="circuit-card-header">
            <div>
              <span>BEFORE</span>
              <strong>Existing compiled circuit</strong>
            </div>

            <span className="circuit-card-index">A</span>
          </div>

          <CircuitPlaceholder variant="before" />
        </article>

        <div className="circuit-transition">
          <ArrowRight size={17} />
          <span>LOCAL PATCH</span>
        </div>

        <article className="circuit-card">
          <div className="circuit-card-header">
            <div>
              <span>AFTER</span>
              <strong>Candidate repaired circuit</strong>
            </div>

            <span className="circuit-card-index">B</span>
          </div>

          <CircuitPlaceholder variant="after" />
        </article>
      </div>

      <div className="circuit-footer">
        <span className="circuit-footer-dot"></span>
        <span>
          Only the verified repair region should differ from the original
          compiled solution.
        </span>
      </div>
    </section>
  )
}

export default CircuitComparison