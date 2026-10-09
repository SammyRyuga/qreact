import {
  ArrowRight,
  CheckCircle2,
  GitCompareArrows,
  Layers3,
  ShieldCheck,
  CircleAlert,
} from "lucide-react"
import "./CircuitComparison.css"

function formatQubits(qubits) {
  if (!Array.isArray(qubits) || qubits.length === 0) {
    return "NOT AVAILABLE"
  }

  return qubits.map((qubit) => `Q${qubit}`).join(" · ")
}

function getImageSource(image) {
  if (typeof image !== "string" || !image) {
    return null
  }

  return image.startsWith("data:image/")
    ? image
    : `data:image/png;base64,${image}`
}

function CircuitImage({ image, alt, variant }) {
  const imageSource = getImageSource(image)

  return (
    <div
      className={`circuit-placeholder ${variant}`}
      style={{
        minHeight: "230px",
        height: "auto",
        padding: "12px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
        background: "#08080b",
      }}
    >
      {imageSource ? (
        <img
          className="circuit-real-image"
          src={imageSource}
          alt={alt}
          loading="lazy"
          style={{
            display: "block",
            width: "100%",
            maxHeight: "300px",
            objectFit: "contain",
            objectPosition: "center",
          }}
        />
      ) : (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "12px",
            padding: "30px 20px",
            textAlign: "center",
            color: "var(--text-muted)",
          }}
        >
          <CircleAlert size={22} strokeWidth={1.3} />

          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "9px",
              letterSpacing: "0.08em",
            }}
          >
            CIRCUIT IMAGE UNAVAILABLE
          </span>
        </div>
      )}
    </div>
  )
}

function SummaryItem({ icon: Icon, label, value, status }) {
  const color =
    status === true
      ? "var(--mint)"
      : status === false
        ? "var(--orange)"
        : "var(--text-soft)"

  return (
    <div className="circuit-summary-item">
      <Icon size={14} />

      <div>
        <span>{label}</span>

        <strong style={{ color }}>{value}</strong>
      </div>
    </div>
  )
}

function CircuitComparison({ result }) {
  const hasResult = Boolean(result?.ok)

  const example = hasResult ? result.example : null
  const repair = hasResult ? result.repair : null

  const selectedCandidate = repair?.selected_candidate ?? null
  const verification = repair?.verification ?? null
  const region = repair?.region ?? null

  const regionQubits =
    example?.region ??
    region?.physical_qubits ??
    []

  const driftedQubits =
    example?.drifted_phys ??
    repair?.drift_event?.drifted_qubits ??
    []

  const hasBeforeImage = Boolean(example?.before_png)
  const hasAfterImage = Boolean(example?.after_png)

  const hasExample = hasBeforeImage && hasAfterImage

  const patchAccepted =
    selectedCandidate?.accepted === true

  const verificationPassed =
    verification?.passed === true

  const preservationPassed =
    verification?.preservation_ok === true

  const preservationFailed =
    verification?.preservation_ok === false

  const circuitStatus = !hasResult
    ? "AWAITING RUN"
    : hasExample
      ? "LIVE CIRCUIT DELTA"
      : patchAccepted
        ? "IMAGE UNAVAILABLE"
        : "NO ACCEPTED PATCH"

  const verificationLabel = !hasResult
    ? "AWAITING RUN"
    : verificationPassed
      ? "ALL CHECKS PASSED"
      : verification?.passed === false
        ? "CHECKS FAILED"
        : repair?.drift_event
          ? "NOT VERIFIED"
          : "NOT REQUIRED"

  const preservationLabel = !hasResult
    ? "AWAITING RUN"
    : preservationPassed
      ? "VERIFIED"
      : preservationFailed
        ? "FAILED"
        : patchAccepted
          ? "NOT VERIFIED"
          : repair?.drift_event
            ? "NOT ESTABLISHED"
            : "NOT REQUIRED"

  const nPhysical =
    result?.config?.n_phys ??
    result?.topology?.n_qubits

  const regionLabel =
    regionQubits.length > 0
      ? `${regionQubits.length} / ${nPhysical ?? "?"} QUBITS`
      : hasResult
        ? "NOT AVAILABLE"
        : "AWAITING RUN"

  const regionPercentage =
    typeof region?.region_fraction === "number"
      ? ` · ${(region.region_fraction * 100).toFixed(1)}%`
      : ""

  const candidateType =
    selectedCandidate?.candidate_type ??
    (hasResult ? "NO ACCEPTED CANDIDATE" : "AWAITING RUN")

  const footerMessage = !hasResult
    ? "Run an experiment to inspect the actual compiled circuit and any accepted repair."
    : hasExample && patchAccepted
      ? preservationPassed
        ? "The backend reports that operations outside the declared repair region were preserved, and all candidate verification checks passed."
        : "Circuit images are available, but preservation must be assessed using the reported verification result."
      : patchAccepted
        ? "A candidate was accepted, but the backend did not return both circuit images for comparison."
        : repair?.fallback
          ? "No local candidate was accepted. The experiment reports a full-recompilation fallback instead of an accepted local circuit patch."
          : repair?.drift_event
            ? "No accepted local patch was reported for this run. The original and repaired circuit comparison is therefore unavailable."
            : "No qualifying drift was reported, so a local repair comparison was not required."

  return (
    <section className="circuit-comparison">
      <div className="circuit-header">
        <div>
          <div
            className="section-kicker"
            style={{ marginBottom: "10px" }}
          >
            CIRCUIT DELTA
          </div>

          <h2>Before and after the repair.</h2>
        </div>

        <div className="circuit-header-state">
          <GitCompareArrows size={14} />
          <span>{circuitStatus}</span>
        </div>
      </div>

      <div className="circuit-summary">
        <SummaryItem
          icon={Layers3}
          label="REPAIR SCOPE"
          value={`${regionLabel}${regionPercentage}`}
        />

        <SummaryItem
          icon={CheckCircle2}
          label="UNCHANGED REGION"
          value={preservationLabel}
          status={
            preservationPassed
              ? true
              : preservationFailed
                ? false
                : null
          }
        />

        <SummaryItem
          icon={ShieldCheck}
          label="VERIFICATION"
          value={verificationLabel}
          status={
            verificationPassed
              ? true
              : verification?.passed === false
                ? false
                : null
          }
        />
      </div>

      {hasExample ? (
        <>
          <div className="circuit-pair">
            <article className="circuit-card">
              <div className="circuit-card-header">
                <div>
                  <span>BEFORE</span>
                  <strong>Existing compiled circuit</strong>
                </div>

                <span className="circuit-card-index">A</span>
              </div>

              <CircuitImage
                variant="before"
                image={example.before_png}
                alt="Original compiled quantum circuit before the local repair"
              />
            </article>

            <div className="circuit-transition">
              <ArrowRight size={17} />

              <span>
                {patchAccepted
                  ? selectedCandidate?.candidate_type ?? "LOCAL PATCH"
                  : "CIRCUIT DELTA"}
              </span>
            </div>

            <article className="circuit-card">
              <div className="circuit-card-header">
                <div>
                  <span>AFTER</span>
                  <strong>Resulting compiled circuit</strong>
                </div>

                <span className="circuit-card-index">B</span>
              </div>

              <CircuitImage
                variant="after"
                image={example.after_png}
                alt="Resulting quantum circuit after the candidate repair"
              />
            </article>
          </div>

          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "center",
              gap: "12px 24px",
              marginTop: "20px",
              color: "var(--text-muted)",
              fontFamily: "var(--font-mono)",
              fontSize: "9px",
              lineHeight: 1.8,
            }}
          >
            <span>
              DRIFT SOURCE: {formatQubits(driftedQubits)}
            </span>

            <span>
              REPAIR REGION: {formatQubits(regionQubits)}
            </span>

            {example.step !== undefined && example.step !== null && (
              <span>CALIBRATION STEP: {example.step}</span>
            )}
          </div>
        </>
      ) : (
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "16px",
            padding: "28px 22px",
            marginTop: "24px",
            border: "1px solid var(--border)",
            background: "rgba(255,255,255,0.01)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flex: "0 0 auto",
              width: "38px",
              height: "38px",
              border: "1px solid var(--border)",
              color: "var(--violet-soft)",
            }}
          >
            <GitCompareArrows size={17} />
          </div>

          <div>
            <strong
              style={{
                display: "block",
                marginBottom: "8px",
                fontFamily: "var(--font-display)",
                fontSize: "15px",
                fontWeight: 500,
                color: "var(--text)",
              }}
            >
              {!hasResult
                ? "Waiting for an experiment"
                : patchAccepted
                  ? "Circuit images not available"
                  : repair?.fallback
                    ? "Full recompilation used"
                    : repair?.drift_event
                      ? "No accepted local patch"
                      : "No repair required"}
            </strong>

            <p
              style={{
                margin: 0,
                maxWidth: "680px",
                color: "var(--text-muted)",
                fontFamily: "var(--font-editorial)",
                fontSize: "11px",
                lineHeight: 1.7,
              }}
            >
              {!hasResult
                ? "Run an experiment to populate this section from the backend."
                : patchAccepted
                  ? "The backend reports an accepted candidate, but it did not provide both before and after circuit images."
                  : repair?.fallback
                    ? "The backend did not accept a local patch and reports a safety fallback. No verified local before/after pair is available for this run."
                    : repair?.drift_event
                      ? "The backend did not report an accepted local patch for this run. This panel will not substitute a fabricated diagram."
                      : "The backend did not report a qualifying drift event, so there is no local repair to compare."}
            </p>
          </div>
        </div>
      )}

      <div className="circuit-footer">
        <span className="circuit-footer-dot" />

        <span>{footerMessage}</span>
      </div>

      {hasResult && (
        <div
          style={{
            marginTop: "12px",
            color: "var(--text-muted)",
            fontFamily: "var(--font-mono)",
            fontSize: "8px",
            letterSpacing: "0.07em",
          }}
        >
          CANDIDATE: {candidateType}
          {selectedCandidate &&
            typeof selectedCandidate.estimated_cost === "number" &&
            ` · ESTIMATED COST: ${selectedCandidate.estimated_cost.toFixed(1)}`}
          {selectedCandidate?.inserted_swaps?.length > 0 &&
            ` · INSERTED SWAPS: ${selectedCandidate.inserted_swaps.length}`}
        </div>
      )}
    </section>
  )
}

export default CircuitComparison