import {
  CheckCircle2,
  CircleAlert,
  GitBranch,
  ShieldCheck,
  XCircle,
} from "lucide-react"
import "./RepairDecision.css"

function RepairDecision() {
  return (
    <section className="repair-decision">
      <div className="repair-header">
        <div>
          <div className="section-kicker">LOCAL REPAIR ANALYSIS</div>

          <h2>Patch verification.</h2>
        </div>

        <div className="repair-header-status">
          <span className="repair-status-dot"></span>
          WAITING FOR CANDIDATE
        </div>
      </div>

      <div className="repair-flow">
        <div className="repair-step">
          <div className="repair-step-number">01</div>

          <div className="repair-step-icon drift-icon">
            <CircleAlert size={16} />
          </div>

          <div className="repair-step-content">
            <span>DRIFT SOURCE</span>
            <strong>Q2</strong>
            <p>Calibration threshold exceeded.</p>
          </div>
        </div>

        <div className="repair-flow-line"></div>

        <div className="repair-step">
          <div className="repair-step-number">02</div>

          <div className="repair-step-icon region-icon">
            <GitBranch size={16} />
          </div>

          <div className="repair-step-content">
            <span>REPAIR REGION</span>
            <strong>Q1 · Q2 · Q4</strong>
            <p>Bounded topology neighborhood.</p>
          </div>
        </div>

        <div className="repair-flow-line"></div>

        <div className="repair-step">
          <div className="repair-step-number">03</div>

          <div className="repair-step-icon verify-icon">
            <ShieldCheck size={16} />
          </div>

          <div className="repair-step-content">
            <span>VERIFICATION</span>
            <strong>NOT RUN</strong>
            <p>Candidate must pass all hard constraints.</p>
          </div>
        </div>
      </div>

      <div className="repair-gate">
        <div className="repair-gate-heading">
          <div>
            <span>ACCEPTANCE GATE</span>
            <strong>Every local patch must be proven safe.</strong>
          </div>
        </div>

        <div className="repair-checks">
          <div className="repair-check">
            <div className="repair-check-icon">
              <CheckCircle2 size={14} />
            </div>

            <div>
              <span>TOPOLOGY VALID</span>
              <small>All two-qubit operations remain executable.</small>
            </div>

            <strong className="check-pending">PENDING</strong>
          </div>

          <div className="repair-check">
            <div className="repair-check-icon">
              <CheckCircle2 size={14} />
            </div>

            <div>
              <span>SEMANTICALLY EQUIVALENT</span>
              <small>
                Logical measurement distribution must be preserved.
              </small>
            </div>

            <strong className="check-pending">PENDING</strong>
          </div>

          <div className="repair-check">
            <div className="repair-check-icon">
              <CheckCircle2 size={14} />
            </div>

            <div>
              <span>DISRUPTION BUDGET</span>
              <small>Repair must remain inside the allowed region.</small>
            </div>

            <strong className="check-pending">PENDING</strong>
          </div>
        </div>
      </div>

      <div className="repair-outcome">
        <div className="outcome-card accepted">
          <div className="outcome-icon">
            <CheckCircle2 size={17} />
          </div>

          <div>
            <span>LOCAL PATCH</span>
            <strong>ACCEPT</strong>
          </div>
        </div>

        <div className="outcome-or">OR</div>

        <div className="outcome-card fallback">
          <div className="outcome-icon">
            <XCircle size={17} />
          </div>

          <div>
            <span>SAFETY FALLBACK</span>
            <strong>FULL RETRANSPILE</strong>
          </div>
        </div>
      </div>
    </section>
  )
}

export default RepairDecision