import {
  Check,
  CircleAlert,
  GitBranch,
  Layers3,
  ShieldCheck,
  Sparkles,
} from "lucide-react"
import "./CompilerPipeline.css"

const stages = [
  {
    id: "01",
    title: "COMPILE",
    description: "Initial circuit mapped to physical hardware.",
    icon: Layers3,
    status: "complete",
  },
  {
    id: "02",
    title: "CALIBRATION",
    description: "Monitor the current hardware state.",
    icon: GitBranch,
    status: "complete",
  },
  {
    id: "03",
    title: "DRIFT",
    description: "Waiting for calibration changes.",
    icon: CircleAlert,
    status: "pending",
  },
  {
    id: "04",
    title: "LOCALIZE",
    description: "Construct the bounded repair region.",
    icon: Sparkles,
    status: "pending",
  },
  {
    id: "05",
    title: "REPAIR",
    description: "Generate constrained local candidates.",
    icon: GitBranch,
    status: "pending",
  },
  {
    id: "06",
    title: "VERIFY",
    description: "Check topology and logical equivalence.",
    icon: ShieldCheck,
    status: "pending",
  },
]

function PipelineStage({ stage }) {
  const Icon = stage.icon

  return (
    <article className={`pipeline-stage ${stage.status}`}>
      <div className="pipeline-stage-marker">
        <span>{stage.id}</span>

        <div className="pipeline-icon">
          <Icon size={14} strokeWidth={1.7} />
        </div>
      </div>

      <div className="pipeline-stage-content">
        <h3>{stage.title}</h3>
        <p>{stage.description}</p>
      </div>

      {stage.status === "complete" && (
        <div className="pipeline-check">
          <Check size={12} />
        </div>
      )}
    </article>
  )
}

function CompilerPipeline() {
  return (
    <section className="compiler-pipeline">
      <div className="pipeline-header">
        <div>
          <div className="section-kicker">COMPILATION PIPELINE</div>

          <h2>From drift to verified repair.</h2>
        </div>

        <div className="pipeline-state">
          <span className="pipeline-state-dot" />
          <span>WAITING FOR EXPERIMENT</span>
        </div>
      </div>

      <div className="pipeline-track">
        {stages.map((stage, index) => (
          <div className="pipeline-stage-slot" key={stage.id}>
            <PipelineStage stage={stage} />

            {index < stages.length - 1 && (
              <div className="pipeline-connector">
                <span></span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="pipeline-result">
        <div className="pipeline-result-icon">
          <ShieldCheck size={16} />
        </div>

        <div>
          <span>FINAL DECISION</span>
          <strong>
            Start an experiment to evaluate a repair candidate.
          </strong>
        </div>
      </div>
    </section>
  )
}

export default CompilerPipeline