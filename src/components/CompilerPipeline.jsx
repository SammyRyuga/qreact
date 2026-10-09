import {
  Check,
  CircleAlert,
  GitBranch,
  Layers3,
  ShieldCheck,
  Sparkles,
} from "lucide-react"
import "./CompilerPipeline.css"

function PipelineStage({ stage }) {
  const Icon = stage.icon

  const displayStatus =
    stage.status === "skipped" ? "pending" : stage.status

  return (
    <article
      className={`pipeline-stage ${displayStatus}`}
      style={
        stage.status === "failed"
          ? { borderColor: "rgba(249, 115, 22, 0.3)" }
          : undefined
      }
    >
      <div className="pipeline-stage-marker">
        <span>{stage.id}</span>

        <div
          className="pipeline-icon"
          style={
            stage.status === "failed"
              ? { color: "var(--orange)" }
              : undefined
          }
        >
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

      {stage.status === "failed" && (
        <div
          className="pipeline-check"
          style={{ color: "var(--orange)" }}
          title="This stage did not pass"
        >
          <CircleAlert size={12} />
        </div>
      )}
    </article>
  )
}

function CompilerPipeline({ result }) {
  const hasResult = Boolean(result?.ok)
  const config = result?.config
  const events = result?.events ?? []
  const repair = result?.repair ?? null

  const driftEvent = repair?.drift_event ?? null
  const region = repair?.region ?? null
  const candidates = repair?.candidates ?? []
  const selectedCandidate = repair?.selected_candidate ?? null
  const verification = repair?.verification ?? null
  const fallback = repair?.fallback ?? null

  const driftEvents = events.filter(
    (event) => event.event_type === "DRIFT_DETECTED"
  )

  const hasDrift =
    Boolean(driftEvent) || driftEvents.length > 0

  const noDrift = hasResult && !hasDrift

  const patchAccepted =
    selectedCandidate?.accepted === true

  const fallbackTriggered = Boolean(fallback)

  const driftStep =
    driftEvent?.step ?? driftEvents[0]?.step

  const driftedQubits =
    driftEvent?.drifted_qubits ?? []

  const regionQubits =
    region?.physical_qubits ?? []

  const candidateCount = candidates.length

  const formatQubits = (qubits) =>
    qubits.length > 0
      ? qubits.map((qubit) => `Q${qubit}`).join(" · ")
      : "Physical resources reported by detector"

  let pipelineState = "WAITING FOR EXPERIMENT"
  let finalDecision =
    "Start an experiment to evaluate a repair candidate."

  if (hasResult) {
    if (patchAccepted) {
      pipelineState = "LOCAL PATCH ACCEPTED"
      finalDecision =
        `Verified ${selectedCandidate.candidate_type} patch accepted.`
    } else if (fallbackTriggered) {
      pipelineState = "FULL RECOMPILE FALLBACK"
      finalDecision =
        `No local patch was accepted. Full recompilation was triggered${
          fallback.reason ? `: ${fallback.reason}` : "."
        }`
    } else if (noDrift) {
      pipelineState = "NO DRIFT DETECTED"
      finalDecision =
        "No qualifying drift was detected. Local repair was not required."
    } else {
      pipelineState = "EXPERIMENT COMPLETE"
      finalDecision =
        "The experiment completed without an accepted patch or reported fallback."
    }
  }

  const stages = hasResult
    ? [
        {
          id: "01",
          title: "COMPILE",
          description: `Initial circuit compiled for ${config.n_log} logical and ${config.n_phys} physical qubits.`,
          icon: Layers3,
          status: "complete",
        },
        {
          id: "02",
          title: "CALIBRATION",
          description: `${config.n_steps} calibration snapshots processed using the seeded synthetic trace.`,
          icon: GitBranch,
          status: "complete",
        },
        {
          id: "03",
          title: "DRIFT",
          description: noDrift
            ? "No qualifying calibration drift was detected."
            : `Detected ${driftEvents.length || 1} drift event(s)${
                driftStep !== undefined ? `; representative event at step ${driftStep}` : ""
              }${
                driftedQubits.length > 0
                  ? ` on ${formatQubits(driftedQubits)}`
                  : "."
              }`,
          icon: CircleAlert,
          status: "complete",
        },
        {
          id: "04",
          title: "LOCALIZE",
          description: noDrift
            ? "Skipped — no repair region was needed."
            : region
              ? region.too_large
                ? `Region contains ${region.region_size} qubits and exceeds the configured repair limit.`
                : `${region.region_size} qubits localized (${(region.region_fraction * 100).toFixed(1)}% of the device): ${formatQubits(regionQubits)}.`
              : "The backend did not report a repair region.",
          icon: Sparkles,
          status: noDrift
            ? "skipped"
            : region
              ? "complete"
              : "failed",
        },
        {
          id: "05",
          title: "REPAIR",
          description: noDrift
            ? "Skipped — there was no qualifying drift to repair."
            : patchAccepted
              ? `${selectedCandidate.candidate_type} candidate accepted at estimated cost ${Number(selectedCandidate.estimated_cost ?? 0).toFixed(1)}.`
              : fallbackTriggered
                ? `${candidateCount} candidate(s) evaluated; no local patch was accepted.`
                : candidateCount > 0
                  ? `${candidateCount} candidate(s) evaluated; none was accepted.`
                  : "No candidate was accepted or reported.",
          icon: GitBranch,
          status: noDrift
            ? "skipped"
            : patchAccepted || fallbackTriggered
              ? "complete"
              : "failed",
        },
        {
          id: "06",
          title: "VERIFY",
          description: noDrift
            ? "Skipped — no local patch required verification."
            : verification?.passed === true
              ? "All reported verification checks passed for the selected candidate."
              : verification?.passed === false
                ? `Verification failed${fallbackTriggered ? "; the system used the safety fallback." : "."}`
                : fallbackTriggered
                  ? "No candidate verification passed; the safety fallback was used."
                  : "No verification result was reported for this run.",
          icon: ShieldCheck,
          status: noDrift
            ? "skipped"
            : verification?.passed === true
              ? "complete"
              : verification?.passed === false
                ? "failed"
                : fallbackTriggered
                  ? "complete"
                  : "pending",
        },
      ]
    : [
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

  return (
    <section className="compiler-pipeline">
      <div className="pipeline-header">
        <div>
          <div className="section-kicker">
            COMPILATION PIPELINE
          </div>

          <h2>From drift to verified repair.</h2>
        </div>

        <div className="pipeline-state">
          <span className="pipeline-state-dot" />
          <span>{pipelineState}</span>
        </div>
      </div>

      <div className="pipeline-track">
        {stages.map((stage, index) => (
          <div className="pipeline-stage-slot" key={stage.id}>
            <PipelineStage stage={stage} />

            {index < stages.length - 1 && (
              <div className="pipeline-connector">
                <span />
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
          <strong>{finalDecision}</strong>
        </div>
      </div>
    </section>
  )
}

export default CompilerPipeline