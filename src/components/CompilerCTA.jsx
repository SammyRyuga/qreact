import { ArrowUpRight, Terminal } from "lucide-react"
import { Link } from "react-router-dom"
import "./CompilerCTA.css"

function CompilerCTA() {
  return (
    <section className="compiler-cta">
      <div className="cta-shell">
        <div className="cta-meta">
          <Terminal size={15} />
          <span>INTERACTIVE COMPILER</span>
        </div>

        <div className="cta-content">
          <div>
            <div className="section-kicker" style={{marginBottom: '15px'}}>RUN THE SYSTEM</div>

            <h2>
              Compile against
              <br />
              <span>changing hardware.</span>
            </h2>
          </div>

          <div className="cta-side">
            <p>
              Configure a circuit, introduce calibration drift, and
              observe how static, full-recompile, and incremental
              strategies respond.
            </p>

            <Link to="/dashboard" className="cta-button">
              <span>OPEN COMPILER</span>
              <ArrowUpRight size={16} />
            </Link>
          </div>
        </div>

        <div className="cta-footer">
          <span>LOCAL SIMULATION</span>
          <span className="cta-separator">/</span>
          <span>QISKIT + AER</span>
          <span className="cta-separator">/</span>
          <span>VERIFIED LOCAL REPAIR</span>
        </div>
      </div>
    </section>
  )
}

export default CompilerCTA