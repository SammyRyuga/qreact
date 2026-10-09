import { ArrowRight, RotateCcw, ShieldCheck } from "lucide-react"
import "./ProblemStatement.css"

function ProblemStatement() {
  return (
    <section className="problem-statement">
      <div className="problem-header">
        <div>
          <div className="section-kicker" style={{marginBottom: '15px'}}>WHY THIS EXISTS</div>

          <h2>
            A local hardware problem
            <br />
            <span>shouldn't invalidate a global solution.</span>
          </h2>
        </div>

        <p>
          A compiled quantum circuit can contain many valid routing and
          placement decisions. When calibration drift affects only a small
          part of the physical device, discarding that entire solution is
          often unnecessarily expensive.
        </p>
      </div>

      <div className="problem-contrast">
        <article className="problem-card conventional">
          <div className="problem-card-top">
            <span className="problem-index">01</span>
            <RotateCcw size={17} />
          </div>

          <div className="problem-card-content">
            <div className="problem-label">CONVENTIONAL RESPONSE</div>

            <h3>Recompile everything.</h3>

            <div className="problem-flow">
              <span>DRIFT</span>
              <ArrowRight size={14} />
              <span>DISCARD</span>
              <ArrowRight size={14} />
              <span>FULL COMPILE</span>
            </div>

            <p>
              A new hardware condition can cause the entire compiled
              circuit to be discarded, even when most of its mapping
              remains perfectly usable.
            </p>
          </div>
        </article>

        <article className="problem-card proposed">
          <div className="problem-card-top">
            <span className="problem-index">02</span>
            <ShieldCheck size={17} />
          </div>

          <div className="problem-card-content">
            <div className="problem-label">Q//REACT</div>

            <h3>Repair what changed.</h3>

            <div className="problem-flow">
              <span>DRIFT</span>
              <ArrowRight size={14} />
              <span>LOCALIZE</span>
              <ArrowRight size={14} />
              <span>VERIFY</span>
            </div>

            <p>
              The affected physical region is isolated, a bounded repair
              is evaluated, and the patch is accepted only when it passes
              the verification gate.
            </p>
          </div>
        </article>
      </div>

      <div className="problem-footnote">
        <span className="problem-footnote-dot"></span>
        <span>UNSAFE LOCAL REPAIRS NEVER BYPASS VERIFICATION</span>
      </div>
    </section>
  )
}

export default ProblemStatement