import {
  Activity,
  BarChart3,
  CheckCircle2,
  Cpu,
  Gauge,
  Layers3,
  ShieldCheck,
  Zap,
} from "lucide-react"
import "./Analysis.css"

function formatNumber(value, digits = 4) {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toFixed(digits)
    : "—"
}

function MetricCard({ label, value, detail, icon: Icon }) {
  return (
    <article className="analysis-metric-card">
      <div className="analysis-metric-top">
        <span>{label}</span>
        <Icon size={16} />
      </div>

      <strong>{value}</strong>

      <p>{detail}</p>
    </article>
  )
}

function StrategyChart({ title, description, image }) {
  return (
    <article className="analysis-chart-card">
      <div className="analysis-chart-heading">
        <div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
      </div>

      {image ? (
        <img
          src={`data:image/png;base64,${image}`}
          alt={title}
          loading="lazy"
        />
      ) : (
        <div className="analysis-chart-empty">
          Chart unavailable for this run.
        </div>
      )}
    </article>
  )
}

function Analysis({ result }) {
  const hasResult = Boolean(result?.ok)
  const summary = result?.summary ?? {}
  const metrics = result?.metrics ?? {}
  const comparative = metrics.comparative ?? {}
  const repairMetrics = metrics.incremental_repair ?? {}
  const config = result?.config ?? {}
  const charts = result?.charts ?? {}

  const staticMetrics = summary.static ?? {}
  const fullMetrics = summary.full ?? {}
  const incrementalMetrics = summary.incremental ?? {}

  const fidelityDelta =
    comparative.fidelity_delta_vs_full

  const costSavings =
    comparative.cost_savings_vs_full

  const calibrationSource =
    metrics.notes?.calibration_source ??
    "Not reported by the backend."

  const costUnit =
    metrics.notes?.total_cost_unit ??
    "Modelled compiler work units; not wall-clock time."

  return (
    <main className="analysis-page">
      <section className="analysis-hero">
        <div className="section-kicker">SYSTEM ANALYSIS</div>

        <div className="analysis-hero-heading">
          <div>
            <h1>Experimental analysis.</h1>

            <p>
              Compare compilation strategies, inspect repair outcomes,
              and evaluate the behavior of Q//REACT using results returned
              by the backend.
            </p>
          </div>

          <div className="analysis-run-status">
            <span className="analysis-status-dot" />
            {hasResult ? "RESULT AVAILABLE" : "AWAITING EXPERIMENT"}
          </div>
        </div>

        {hasResult && (
          <div className="analysis-run-meta">
            <span>
              <Cpu size={13} />
              {config.n_log} LOGICAL QUBITS
            </span>

            <span>
              <Layers3 size={13} />
              {config.n_phys} PHYSICAL QUBITS
            </span>

            <span>
              <Activity size={13} />
              {config.n_steps} CALIBRATION STEPS
            </span>

            <span>SEED {config.seed}</span>
          </div>
        )}
      </section>

      {!hasResult ? (
        <section className="analysis-empty">
          <div className="analysis-empty-icon">
            <BarChart3 size={22} />
          </div>

          <h2>No experiment results yet.</h2>

          <p>
            Run an experiment from the Dashboard first. Its results will
            appear here automatically, and you can return to this page
            without running the experiment a second time.
          </p>

          <a href="/dashboard" className="analysis-link">
            OPEN COMPILER DASHBOARD
          </a>
        </section>
      ) : (
        <>
          <section className="analysis-section">
            <div className="analysis-section-heading">
              <div>
                <div className="section-kicker">01 / PERFORMANCE</div>
                <h2>Strategy comparison.</h2>
              </div>

              <span>BACKEND METRICS</span>
            </div>

            <div className="analysis-strategy-grid">
              {[
                {
                  id: "static",
                  title: "STATIC",
                  description: "No calibration reaction",
                  data: staticMetrics,
                  icon: Layers3,
                },
                {
                  id: "full",
                  title: "FULL RETRANSPILE",
                  description: "Full recompilation strategy",
                  data: fullMetrics,
                  icon: Activity,
                },
                {
                  id: "incremental",
                  title: "Q//REACT",
                  description: "Incremental repair strategy",
                  data: incrementalMetrics,
                  icon: ShieldCheck,
                },
              ].map((strategy) => (
                <article
                  className={`analysis-strategy-card ${
                    strategy.id === "incremental" ? "featured" : ""
                  }`}
                  key={strategy.id}
                >
                  <div className="analysis-strategy-header">
                    <div>
                      <h3>{strategy.title}</h3>
                      <p>{strategy.description}</p>
                    </div>

                    <strategy.icon size={17} />
                  </div>

                  <div className="analysis-strategy-metric">
                    <span>MEAN FIDELITY</span>
                    <strong>
                      {formatNumber(strategy.data.mean_fidelity)}
                    </strong>
                  </div>

                  <div className="analysis-strategy-metric">
                    <span>RECOMPILATION COST</span>
                    <strong>
                      {formatNumber(strategy.data.total_cost, 1)}
                    </strong>
                  </div>

                  <div className="analysis-strategy-metric">
                    <span>USAGE GINI</span>
                    <strong>
                      {formatNumber(strategy.data.gini_usage)}
                    </strong>
                  </div>

                  <div className="analysis-strategy-metric">
                    <span>RECOMPILATIONS</span>
                    <strong>
                      {strategy.data.num_recompiles ?? "—"}
                    </strong>
                  </div>
                </article>
              ))}
            </div>

            <div className="analysis-comparative-strip">
              <div>
                <span>FIDELITY DELTA VS FULL</span>
                <strong>
                  {formatNumber(fidelityDelta, 6)}
                </strong>
              </div>

              <div>
                <span>COST SAVINGS VS FULL</span>
                <strong>
                  {typeof costSavings === "number"
                    ? `${(costSavings * 100).toFixed(2)}%`
                    : "—"}
                </strong>
              </div>
            </div>
          </section>

          <section className="analysis-section">
            <div className="analysis-section-heading">
              <div>
                <div className="section-kicker">02 / CHARTS</div>
                <h2>Measured experiment output.</h2>
              </div>

              <span>GENERATED BY BACKEND</span>
            </div>

            <div className="analysis-chart-grid">
              <StrategyChart
                title="Mean fidelity"
                description="Noisy AerSimulator fidelity by strategy."
                image={charts.fidelity}
              />

              <StrategyChart
                title="Recompilation cost"
                description="Modelled compiler work units by strategy."
                image={charts.cost}
              />

              <StrategyChart
                title="Qubit-usage concentration"
                description="Gini coefficient across compilation strategies."
                image={charts.gini}
              />
            </div>
          </section>

          <section className="analysis-section">
            <div className="analysis-section-heading">
              <div>
                <div className="section-kicker">03 / REPAIR EVALUATION</div>
                <h2>Locality and verification.</h2>
              </div>

              <span>INCREMENTAL STRATEGY</span>
            </div>

            <div className="analysis-metric-grid">
              <MetricCard
                label="DRIFT EVENTS"
                value={repairMetrics.drift_event_count ?? "—"}
                detail="Qualifying drift events detected."
                icon={Activity}
              />

              <MetricCard
                label="LOCAL PATCHES"
                value={repairMetrics.local_patch_count ?? "—"}
                detail="Accepted local repairs."
                icon={CheckCircle2}
              />

              <MetricCard
                label="FULL FALLBACKS"
                value={repairMetrics.full_fallback_count ?? "—"}
                detail="Full recompilations triggered."
                icon={Zap}
              />

              <MetricCard
                label="VERIFICATION PASS RATE"
                value={
                  typeof repairMetrics.verification_pass_rate === "number"
                    ? `${(
                        repairMetrics.verification_pass_rate * 100
                      ).toFixed(1)}%`
                    : "—"
                }
                detail="Reported candidate verification outcomes."
                icon={ShieldCheck}
              />

              <MetricCard
                label="MEAN REGION SIZE"
                value={formatNumber(repairMetrics.mean_region_size, 2)}
                detail="Physical qubits per repair region."
                icon={Layers3}
              />

              <MetricCard
                label="MEAN REGION FRACTION"
                value={
                  typeof repairMetrics.mean_region_fraction === "number"
                    ? `${(
                        repairMetrics.mean_region_fraction * 100
                      ).toFixed(1)}%`
                    : "—"
                }
                detail="Average fraction of device qubits covered."
                icon={Gauge}
              />

              <MetricCard
                label="PRESERVATION RATIO"
                value={
                  typeof repairMetrics.mean_preservation_ratio === "number"
                    ? `${(
                        repairMetrics.mean_preservation_ratio * 100
                      ).toFixed(1)}%`
                    : "—"
                }
                detail="Average unchanged operation ratio."
                icon={CheckCircle2}
              />

              <MetricCard
                label="PATCH ACCEPTANCE RATE"
                value={
                  typeof repairMetrics.patch_acceptance_rate === "number"
                    ? `${(
                        repairMetrics.patch_acceptance_rate * 100
                      ).toFixed(1)}%`
                    : "—"
                }
                detail="Reported accepted patches over the defined denominator."
                icon={ShieldCheck}
              />
            </div>
          </section>

          <section className="analysis-section">
            <div className="analysis-section-heading">
              <div>
                <div className="section-kicker">04 / REPRODUCIBILITY</div>
                <h2>Experiment conditions.</h2>
              </div>

              <span>RUN CONFIGURATION</span>
            </div>

            <div className="analysis-config-grid">
              <div>
                <span>LOGICAL QUBITS</span>
                <strong>{config.n_log}</strong>
              </div>

              <div>
                <span>PHYSICAL QUBITS</span>
                <strong>{config.n_phys}</strong>
              </div>

              <div>
                <span>CALIBRATION STEPS</span>
                <strong>{config.n_steps}</strong>
              </div>

              <div>
                <span>DRIFT THRESHOLD</span>
                <strong>{config.threshold}</strong>
              </div>

              <div>
                <span>RANDOM SEED</span>
                <strong>{config.seed}</strong>
              </div>
            </div>

            <div className="analysis-research-note">
              <div>
                <strong>Calibration source</strong>
                <p>{calibrationSource}</p>
              </div>

              <div>
                <strong>Cost interpretation</strong>
                <p>{costUnit}</p>
              </div>

              <div>
                <strong>Interpretation note</strong>
                <p>
                  Results describe this configured experimental run. A
                  single run does not establish general performance or
                  patent novelty; comparative claims require repeated,
                  reproducible evaluation across varied seeds and settings.
                </p>
              </div>
            </div>
          </section>
        </>
      )}
    </main>
  )
}

export default Analysis