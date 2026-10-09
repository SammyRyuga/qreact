import {
  CheckCircle2,
  CircleAlert,
  GitBranch,
  ShieldCheck,
  XCircle,
} from "lucide-react"
import "./RepairDecision.css"

function formatQubits(qubits) {
  if (!Array.isArray(qubits) || qubits.length === 0) {
    return "NONE REPORTED"
  }

  return qubits.map((q) => `Q${q}`).join(" · ")
}

function getCheckStatus(value, verificationExists) {
  if (value === true) return "pass"
  if (value === false) return "fail"
  return verificationExists ? "unavailable" : "pending"
}

function CheckIcon({ status }) {
  if (status === "pass") return <CheckCircle2 size={14} />
  if (status === "fail") return <XCircle size={14} />
  return <CircleAlert size={14} />
}

function RepairDecision({ result }) {
  const hasResult = Boolean(result?.ok)
  const repair = hasResult ? result.repair : null

  const driftEvent = repair?.drift_event ?? null
  const region = repair?.region ?? null
  const candidates = repair?.candidates ?? []
  const selectedCandidate = repair?.selected_candidate ?? null
  const verification = repair?.verification ?? null
  const fallback = repair?.fallback ?? null

  const accepted = selectedCandidate?.accepted === true
  const fallbackTriggered = Boolean(fallback)
  const noDrift = hasResult && !driftEvent

  const displayedCandidate =
    selectedCandidate ?? candidates[0] ?? null

  const driftedQubits = driftEvent?.drifted_qubits ?? []
  const driftedEdges = driftEvent?.drifted_edges ?? []
  const regionQubits = region?.physical_qubits ?? []

  const driftSource =
    driftedQubits.length > 0
      ? formatQubits(driftedQubits)
      : driftedEdges.length > 0
        ? driftedEdges
            .map(([a, b]) => `EDGE ${a}–${b}`)
            .join(" · ")
        : noDrift
          ? "NO DRIFT DETECTED"
          : "AWAITING EXPERIMENT"

  const verificationStatus =
    !hasResult
      ? "NOT RUN"
      : noDrift
        ? "NOT REQUIRED"
        : accepted
          ? "ALL CHECKS PASSED"
          : verification?.passed === false
            ? "CANDIDATE REJECTED"
            : verification
              ? "VERIFICATION UNAVAILABLE"
              : fallbackTriggered
                ? "NO CANDIDATE VERIFIED"
                : "NOT RUN"

  const decisionStatus =
    accepted
      ? "PATCH ACCEPTED"
      : fallbackTriggered
        ? "FALLBACK TRIGGERED"
        : noDrift
          ? "NO DRIFT DETECTED"
          : hasResult
            ? "NO PATCH ACCEPTED"
            : "WAITING FOR CANDIDATE"

  const decisionColor = accepted
    ? "var(--mint)"
    : fallbackTriggered
      ? "var(--orange)"
      : "var(--text-muted)"

  const checks = [
    {
      key: "topology_ok",
      label: "TOPOLOGY VALID",
      description: "All two-qubit operations remain on coupling edges.",
    },
    {
      key: "mapping_ok",
      label: "MAPPING VALID",
      description: "Logical qubits map to distinct physical qubits.",
    },
    {
      key: "locality_ok",
      label: "LOCALITY BOUNDED",
      description: "All candidate changes remain inside the declared region.",
    },
    {
      key: "preservation_ok",
      label: "PRESERVATION INTACT",
      description: "Operations outside the repair region remain unchanged.",
    },
    {
      key: "semantic_ok",
      label: "SEMANTIC VERIFICATION",
      description: "The backend's logical-equivalence checks must pass.",
    },
    {
      key: "disruption_ok",
      label: "DISRUPTION BUDGET",
      description: "The candidate must satisfy the configured repair limits.",
    },
  ]

  function checkLabel(status) {
    if (status === "pass") return "PASS"
    if (status === "fail") return "FAIL"
    if (status === "unavailable") return "UNAVAILABLE"
    return "PENDING"
  }

  const localOutcome = accepted
    ? "ACCEPTED"
    : fallbackTriggered
      ? "REJECTED"
      : noDrift
        ? "NOT REQUIRED"
        : "AWAITING"

  const fallbackOutcome = fallbackTriggered
    ? "TRIGGERED"
    : noDrift
      ? "NOT REQUIRED"
      : accepted
        ? "STANDBY"
        : "AWAITING"

  return (
    <section className="repair-decision">
      <div className="repair-header">
        <div>
          <div
            className="section-kicker"
            style={{ marginBottom: "10px" }}
          >
            LOCAL REPAIR ANALYSIS
          </div>

          <h2>Patch verification.</h2>
        </div>

        <div
          className="repair-header-status"
          style={{ color: decisionColor }}
        >
          <span
            className="repair-status-dot"
            style={{ background: decisionColor }}
          />
          {decisionStatus}
        </div>
      </div>

      <div className="repair-flow">
        <div className="repair-step">
          <div className="repair-step-number">01</div>

          <div className="repair-step-icon drift-icon">
            <CircleAlert size={16} />
          </div>

          <div className="repair-step-content">
            <span>DRIFT SOURCE</span>

            <strong>{driftSource}</strong>

            <p>
              {driftEvent
                ? `Calibration change detected at step ${driftEvent.step}.`
                : noDrift
                  ? "No drift event was reported for this run."
                  : "Run an experiment to identify drift."}
            </p>
          </div>
        </div>

        <div className="repair-flow-line" />

        <div className="repair-step">
          <div className="repair-step-number">02</div>

          <div className="repair-step-icon region-icon">
            <GitBranch size={16} />
          </div>

          <div className="repair-step-content">
            <span>REPAIR REGION</span>

            <strong>
              {region
                ? formatQubits(regionQubits)
                : "NOT AVAILABLE"}
            </strong>

            <p>
              {region
                ? `${region.region_size} qubits · ${(
                    region.region_fraction * 100
                  ).toFixed(1)}% of the device${
                    region.too_large ? " · region limit exceeded" : ""
                  }`
                : "The bounded repair region has not been reported."}
            </p>
          </div>
        </div>

        <div className="repair-flow-line" />

        <div className="repair-step">
          <div className="repair-step-number">03</div>

          <div className="repair-step-icon verify-icon">
            <ShieldCheck size={16} />
          </div>

          <div className="repair-step-content">
            <span>VERIFICATION</span>

            <strong>{verificationStatus}</strong>

            <p>
              {displayedCandidate
                ? `Candidate: ${displayedCandidate.candidate_type}.`
                : fallbackTriggered
                  ? `Fallback reason: ${fallback.reason}.`
                  : noDrift
                    ? "No local patch was required."
                    : "Waiting for a verifiable candidate."}
            </p>
          </div>
        </div>
      </div>

      <div className="repair-gate">
        <div className="repair-gate-heading">
          <div>
            <span>ACCEPTANCE GATE</span>

            <strong>
              {accepted
                ? "All required checks passed for the accepted candidate."
                : fallbackTriggered
                  ? "No local patch was accepted; full retranspilation was triggered."
                  : noDrift
                    ? "No repair decision was required."
                    : "Every local patch must pass all required checks."}
            </strong>
          </div>
        </div>

        <div className="repair-checks">
          {checks.map((check) => {
            const status = getCheckStatus(
              verification?.[check.key],
              Boolean(verification)
            )

            const color =
              status === "pass"
                ? "var(--mint)"
                : status === "fail"
                  ? "var(--orange)"
                  : "var(--text-muted)"

            return (
              <div className="repair-check" key={check.key}>
                <div
                  className={`repair-check-icon check-${status}`}
                  style={{ color }}
                >
                  <CheckIcon status={status} />
                </div>

                <div>
                  <span>{check.label}</span>
                  <small>{check.description}</small>
                </div>

                <strong
                  className={`check-${status}`}
                  style={{ color }}
                >
                  {checkLabel(status)}
                </strong>
              </div>
            )
          })}
        </div>
      </div>

      {fallbackTriggered && (
        <div
          role="status"
          style={{
            marginTop: "18px",
            color: "var(--orange)",
            fontSize: "0.8rem",
            fontFamily: "var(--font-mono)",
          }}
        >
          FALLBACK REASON: {fallback.reason}
        </div>
      )}

      {displayedCandidate && (
        <div
          style={{
            marginTop: "18px",
            color: "var(--text-muted)",
            fontSize: "0.75rem",
            fontFamily: "var(--font-mono)",
          }}
        >
          CANDIDATE TYPE: {displayedCandidate.candidate_type}
          {" · "}
          ESTIMATED COST:{" "}
          {typeof displayedCandidate.estimated_cost === "number"
            ? displayedCandidate.estimated_cost.toFixed(1)
            : "—"}
          {displayedCandidate.inserted_swaps?.length > 0 &&
            ` · INSERTED SWAPS: ${displayedCandidate.inserted_swaps.length}`}
        </div>
      )}

      <div className="repair-outcome">
        <div
          className="outcome-card accepted"
          style={{ opacity: accepted ? 1 : 0.55 }}
        >
          <div className="outcome-icon">
            <CheckCircle2 size={17} />
          </div>

          <div>
            <span>LOCAL PATCH</span>
            <strong>{localOutcome}</strong>
          </div>
        </div>

        <div className="outcome-or">OR</div>

        <div
          className="outcome-card fallback"
          style={{ opacity: fallbackTriggered ? 1 : 0.55 }}
        >
          <div className="outcome-icon">
            <XCircle size={17} />
          </div>

          <div>
            <span>SAFETY FALLBACK</span>
            <strong>{fallbackOutcome}</strong>
          </div>
        </div>
      </div>
    </section>
  )
}

export default RepairDecision