import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Terminal,
} from "lucide-react"
import "./EventLog.css"

const initialEvents = [
  {
    step: null,
    event_type: "SYSTEM",
    message: "Compiler initialized and waiting for experiment.",
    severity: "info",
  },
  {
    step: null,
    event_type: "CALIBRATION",
    message: "Baseline calibration state ready.",
    severity: "success",
  },
  {
    step: null,
    event_type: "DRIFT",
    message: "No drift event detected yet.",
    severity: "info",
  },
]

const eventLabels = {
  CALIBRATION_SNAPSHOT: "CALIBRATION",
  DRIFT_DETECTED: "DRIFT",
  REGION_BUILT: "REGION",
  CANDIDATE_GENERATED: "CANDIDATE",
  CANDIDATE_REJECTED: "REJECTED",
  CANDIDATE_VERIFIED: "VERIFIED",
  LOCAL_PATCH_ACCEPTED: "PATCH ACCEPTED",
  FALLBACK_TRIGGERED: "FALLBACK",
  FULL_RECOMPILE: "RECOMPILE",
  EXPERIMENT_STEP: "EXPERIMENT",
  VERIFICATION_FAILED: "VERIFY FAILED",
}

function getEventStatus(event) {
  const type = event.event_type

  if (
    type === "LOCAL_PATCH_ACCEPTED" ||
    type === "CANDIDATE_VERIFIED"
  ) {
    return "success"
  }

  if (
    type === "DRIFT_DETECTED" ||
    type === "CANDIDATE_REJECTED" ||
    type === "FALLBACK_TRIGGERED" ||
    type === "VERIFICATION_FAILED"
  ) {
    return "warning"
  }

  if (event.severity === "warning") {
    return "warning"
  }

  if (event.severity === "success") {
    return "success"
  }

  return "info"
}

function EventIcon({ status }) {
  if (status === "success") {
    return <CheckCircle2 size={13} />
  }

  if (status === "warning") {
    return <AlertTriangle size={13} />
  }

  return <Activity size={13} />
}

function formatStep(step) {
  if (step === null || step === undefined) {
    return "—"
  }

  return `S${String(step).padStart(2, "0")}`
}

function EventLog({ result }) {
  const hasResult = Boolean(result?.ok)

  const events = hasResult
    ? result.events ?? []
    : initialEvents

  return (
    <section className="event-log">
      <div className="event-log-header">
        <div>
          <div
            className="section-kicker"
            style={{ marginBottom: "10px" }}
          >
            EVENT STREAM
          </div>

          <h2>Compiler activity</h2>
        </div>

        <div className="event-log-live">
          <Terminal size={13} />
          <span>{hasResult ? "RUN TRACE" : "AWAITING RUN"}</span>
        </div>
      </div>

      <div className="event-list">
        {events.length === 0 ? (
          <div className="event-row pending">
            <div className="event-time">—</div>

            <div className="event-icon">
              <Activity size={13} />
            </div>

            <div className="event-type">SYSTEM</div>

            <div className="event-message">
              No structured events were returned for this run.
            </div>
          </div>
        ) : (
          events.map((event, index) => {
            const status = getEventStatus(event)

            const label =
              eventLabels[event.event_type] ??
              event.event_type ??
              "EVENT"

            return (
              <div
                className={`event-row ${status}`}
                key={`${event.event_type}-${event.step}-${index}`}
                title={[
                  event.region_id && `Region: ${event.region_id}`,
                  event.candidate_id &&
                    `Candidate: ${event.candidate_id}`,
                  event.reason && `Reason: ${event.reason}`,
                ]
                  .filter(Boolean)
                  .join(" | ")}
              >
                <div className="event-time">
                  {formatStep(event.step)}
                </div>

                <div className="event-icon">
                  <EventIcon status={status} />
                </div>

                <div className="event-type">{label}</div>

                <div className="event-message">
                  {event.message}
                </div>
              </div>
            )
          })
        )}
      </div>

      <div className="event-log-footer">
        <span className="event-footer-dot"></span>

        <span>
          {hasResult
            ? `${events.length} STRUCTURED EVENTS · SEED ${result.config.seed}`
            : "EVENTS WILL APPEAR HERE DURING EXECUTION"}
        </span>
      </div>
    </section>
  )
}

export default EventLog