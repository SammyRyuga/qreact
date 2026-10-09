import { ArrowRight, ShieldCheck, Zap, RefreshCw, LocateFixed } from "lucide-react"
import "./MethodFlow.css"

const stages = [
  {
    number: "01",
    title: "DRIFT",
    description:
      "Calibration changes invalidate specific physical resources.",
    icon: Zap,
    accent: "orange",
  },
  {
    number: "02",
    title: "LOCALIZE",
    description:
      "Only the affected topology region enters the repair path.",
    icon: LocateFixed,
    accent: "violet",
  },
  {
    number: "03",
    title: "VERIFY",
    description:
      "Candidate repairs must pass hard hardware and semantic checks.",
    icon: ShieldCheck,
    accent: "mint",
  },
  {
    number: "04",
    title: "FALLBACK",
    description:
      "Unsafe repairs are rejected and fully recompiled.",
    icon: RefreshCw,
    accent: "pink",
  },
]

function MethodFlow() {
  return (
    <section id="method" className="method-flow">
      <div className="method-header">
        <div>
          <div className="section-kicker" style={{marginBottom: '15px'}}>THE CORE IDEA</div>

          <h2>
            Repair what drifted.
            <br />
            <span>Preserve what didn't.</span>
          </h2>
        </div>

        <p className="method-intro">
          The compiler does not blindly trust a local rewrite. Every
          candidate must survive the verification gate before it can
          replace the existing compiled solution.
        </p>
      </div>

      <div className="method-grid">
        {stages.map((stage, index) => {
          const Icon = stage.icon

          return (
            <div className="method-stage-wrapper" key={stage.number}>
              <article className={`method-stage ${stage.accent}`}>
                <div className="method-stage-top">
                  <span className="method-number">{stage.number}</span>

                  <div className="method-icon">
                    <Icon size={17} strokeWidth={1.6} />
                  </div>
                </div>

                <div className="method-stage-body">
                  <h3>{stage.title}</h3>

                  <p>{stage.description}</p>
                </div>
              </article>

              {index < stages.length - 1 && (
                <div className="method-arrow">
                  <ArrowRight size={15} strokeWidth={1.4} />
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="method-bottom">
        <div className="method-bottom-line"></div>

        <div className="method-bottom-label">
          <span className="method-pulse"></span>
          TRUST, BUT VERIFY
        </div>

        <div className="method-bottom-line"></div>
      </div>
    </section>
  )
}

export default MethodFlow