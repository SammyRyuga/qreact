import {
  Activity,
  BarChart3,
  Gauge,
  Layers3,
  ShieldCheck,
} from "lucide-react"
import "./ResultsOverview.css"

const strategies = [
  {
    id: "static",
    name: "STATIC",
    label: "NO REACTION",
    fidelity: "0.9964",
    cost: "32.0",
    gini: "0.5000",
    icon: Layers3,
  },
  {
    id: "full",
    name: "FULL",
    label: "RETRANSPILE",
    fidelity: "0.9961",
    cost: "339.2",
    gini: "0.1370",
    icon: Activity,
  },
  {
    id: "incremental",
    name: "INCREMENTAL",
    label: "Q//REACT",
    fidelity: "0.9963",
    cost: "312.8",
    gini: "0.1240",
    icon: ShieldCheck,
  },
]

function Metric({ icon: Icon, label, value }) {
  return (
    <div className="result-metric">
      <div className="result-metric-icon">
        <Icon size={14} strokeWidth={1.6} />
      </div>

      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  )
}

function ResultsOverview() {
  return (
    <section className="results-overview">
      <div className="results-header">
        <div>
          <div className="section-kicker" style={{marginBottom: '10px'}}>EXPERIMENT RESULTS</div>

          <h2>Strategy comparison.</h2>
        </div>

        <div className="results-context">
          <BarChart3 size={14} />
          <span>MEASURED OUTPUT</span>
        </div>
      </div>

      <div className="strategy-results">
        {strategies.map((strategy) => {
          const Icon = strategy.icon
          const isIncremental = strategy.id === "incremental"

          return (
            <article
              className={`strategy-result ${
                isIncremental ? "featured" : ""
              }`}
              key={strategy.id}
            >
              <div className="strategy-result-top">
                <div>
                  <div className="strategy-name">{strategy.name}</div>
                  <div className="strategy-label">{strategy.label}</div>
                </div>

                <div className="strategy-icon">
                  <Icon size={17} strokeWidth={1.5} />
                </div>
              </div>

              <div className="strategy-metrics">
                <Metric
                  icon={Gauge}
                  label="MEAN FIDELITY"
                  value={strategy.fidelity}
                />

                <Metric
                  icon={Activity}
                  label="TOTAL RECOMPUTE COST"
                  value={strategy.cost}
                />

                <Metric
                  icon={Layers3}
                  label="Gini / USAGE"
                  value={strategy.gini}
                />
              </div>
            </article>
          )
        })}
      </div>

      <div className="results-note">
        <span className="results-note-dot"></span>

        <span>
          Lower recomputation cost and lower usage concentration indicate
          less global disruption.
        </span>
      </div>
    </section>
  )
}

export default ResultsOverview