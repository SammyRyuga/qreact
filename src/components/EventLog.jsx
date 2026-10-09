import { Activity, AlertTriangle, CheckCircle2, Terminal } from "lucide-react"
import "./EventLog.css"

const events = [
  {
    time: "00:00.0",
    type: "SYSTEM",
    message: "Compiler initialized and waiting for experiment.",
    status: "info",
  },
  {
    time: "00:00.0",
    type: "CALIBRATION",
    message: "Baseline calibration state ready.",
    status: "success",
  },
  {
    time: "—",
    type: "DRIFT",
    message: "No drift event detected yet.",
    status: "pending",
  },
]

function EventIcon({ status }) {
  if (status === "success") {
    return <CheckCircle2 size={13} />
  }

  if (status === "warning") {
    return <AlertTriangle size={13} />
  }

  return <Activity size={13} />
}

function EventLog() {
  return (
    <section className="event-log">
      <div className="event-log-header">
        <div>
          <div className="section-kicker" style={{marginBottom: '10px'}}>EVENT STREAM</div>

          <h2>Compiler activity</h2>
        </div>

        <div className="event-log-live">
          <Terminal size={13} />
          <span>LIVE OUTPUT</span>
        </div>
      </div>

      <div className="event-list">
        {events.map((event, index) => (
          <div className={`event-row ${event.status}`} key={index}>
            <div className="event-time">{event.time}</div>

            <div className="event-icon">
              <EventIcon status={event.status} />
            </div>

            <div className="event-type">{event.type}</div>

            <div className="event-message">{event.message}</div>
          </div>
        ))}
      </div>

      <div className="event-log-footer">
        <span className="event-footer-dot"></span>
        <span>EVENTS WILL APPEAR HERE DURING EXECUTION</span>
      </div>
    </section>
  )
}

export default EventLog