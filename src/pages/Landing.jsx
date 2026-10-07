import { ArrowDown, ArrowUpRight } from "lucide-react"
import { Link } from "react-router-dom"
import QuantumField from "../components/QuantumField"
import ProblemStatement from "../components/ProblemStatement"
import MethodFlow from "../components/MethodFlow"
import CompilerCTA from "../components/CompilerCTA"
import "./Landing.css"

function Landing() {
  return (
    <main className="landing">
      <section className="hero">
        <div className="hero-copy">
          <div className="hero-kicker">
            INCREMENTAL CALIBRATION-REACTIVE RECOMPILATION
          </div>

          <h1>
            When the hardware drifts,
            <br />
            <span>don't recompile everything.</span>
          </h1>

          <p>
            A topology-aware quantum compiler that detects calibration
            drift, isolates the affected region, verifies a local repair,
            and falls back to full recompilation when necessary.
          </p>

          <div className="hero-actions">
            <Link to="/dashboard" className="primary-action">
              <span>EXPLORE THE COMPILER</span>
              <ArrowUpRight size={16} />
            </Link>

            <a href="#method" className="secondary-action">
              <ArrowDown size={15} />
              <span>VIEW THE METHOD</span>
            </a>
          </div>

          <div className="hero-proof">
            <div>
              <span className="proof-dot violet"></span>
              BOUNDED LOCAL REPAIR
            </div>

            <div>
              <span className="proof-dot orange"></span>
              VERIFIED BEFORE ACCEPTANCE
            </div>

            <div>
              <span className="proof-dot mint"></span>
              SAFE FULL-RECOMPILE FALLBACK
            </div>
          </div>
        </div>

        <QuantumField />
      </section>

      <ProblemStatement />

      <MethodFlow />

      <CompilerCTA />
    </main>
  )
}

export default Landing