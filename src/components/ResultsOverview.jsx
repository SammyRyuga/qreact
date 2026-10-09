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
    icon: Layers3,
  },
  {
    id: "full",
    name: "FULL",
    label: "RETRANSPILE",
    icon: Activity,
  },
  {
    id: "incremental",
    name: "INCREMENTAL",
    label: "Q//REACT",
    icon: ShieldCheck,
  },
]

function formatMetric(value, digits = 4) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "—"
  }

  return value.toFixed(digits)
}

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

function ResultsOverview({ result }) {
  const summary = result?.ok ? result.summary : null
  const hasResults = Boolean(
    summary?.static &&
    summary?.full &&
    summary?.incremental
  )

  return (
    <section className="results-overview">
      <div className="results-header">
        <div>
          <div
            className="section-kicker"
            style={{ marginBottom: "10px" }}
          >
            EXPERIMENT RESULTS
          </div>

          <h2>Strategy comparison.</h2>
        </div>

        <div className="results-context">
          <BarChart3 size={14} />
          <span>{hasResults ? "LIVE RUN OUTPUT" : "AWAITING RUN"}</span>
        </div>
      </div>

      <div className="strategy-results">
        {strategies.map((strategy) => {
          const Icon = strategy.icon
          const isIncremental = strategy.id === "incremental"
          const metrics = summary?.[strategy.id]

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
                  value={formatMetric(metrics?.mean_fidelity)}
                />

                <Metric
                  icon={Activity}
                  label="TOTAL RECOMPUTE COST"
                  value={formatMetric(metrics?.total_cost, 1)}
                />

                <Metric
                  icon={Layers3}
                  label="GINI / USAGE"
                  value={formatMetric(metrics?.gini_usage)}
                />
              </div>
            </article>
          )
        })}
      </div>

      <div className="results-note">
        <span className="results-note-dot"></span>

        <span>
          {hasResults
            ? "Metrics are computed from this experiment. Recompilation cost is measured in modeled compiler work units, not wall-clock time."
            : "Run an experiment to populate these cards with actual backend results."}
        </span>
      </div>
    </section>
  )
}

export default ResultsOverview