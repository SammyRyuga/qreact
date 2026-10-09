import { Activity, CircleDot, Network } from "lucide-react"
import "./TopologyPanel.css"

const PLACEHOLDER_EDGES = [
  [0, 1],
  [1, 2],
  [2, 3],
  [0, 4],
  [4, 2],
  [2, 6],
  [6, 5],
  [4, 5],
  [5, 6],
  [7, 4],
]


function getNodePositions(count, requestedMainCount) {
  const mainCount = Math.max(
    1,
    Math.min(
      count - 1,
      requestedMainCount ?? Math.floor(count / 2)
    )
  )

  const twinCount = count - mainCount

  const centerX = 50
  const centerY = 49

  const innerRadiusX = 21
  const innerRadiusY = 23
  const outerRadiusX = 36
  const outerRadiusY = 35

  return Array.from({ length: count }, (_, id) => {
    const isTwin = id >= mainCount
    const index = isTwin ? id - mainCount : id
    const ringCount = isTwin ? twinCount : mainCount

    const angle =
      -Math.PI / 2 + (2 * Math.PI * index) / ringCount

    return {
      id,
      x:
        centerX +
        (isTwin ? outerRadiusX : innerRadiusX) *
          Math.cos(angle),
      y:
        centerY +
        (isTwin ? outerRadiusY : innerRadiusY) *
          Math.sin(angle),
    }
  })
}


function normalizeEdge(edge) {
  return [...edge].sort((a, b) => a - b).join("-")
}

function TopologyNode({ qubit }) {
  return (
    <div
      className={[
        "topology-node",
        qubit.status,
        qubit.inRegion ? "in-region" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={{
        left: `${qubit.x}%`,
        top: `${qubit.y}%`,
      }}
      title={`Physical qubit Q${qubit.id}${
        qubit.status === "drift" ? " — drift detected" : ""
      }${qubit.inRegion ? " — in repair region" : ""}`}
    >
      <div className="topology-node-glow" />
      <div className="topology-node-core" />
      <span>Q{qubit.id}</span>
    </div>
  )
}

function TopologyPanel({ result }) {
  const hasResult = Boolean(result?.ok)

  const nQubits = hasResult
    ? result.topology?.n_qubits ?? result.config?.n_phys ?? 8
    : 8

const mainCount = hasResult
  ? Math.max(
      3,
      Number(result.config?.n_log ?? 0),
      Math.floor(nQubits / 2)
    )
  : Math.floor(nQubits / 2)

const positions = getNodePositions(nQubits, mainCount)


  // Use real backend edges after a successful run.
  // The placeholder graph is only for the initial, pre-run display.
  const connections = hasResult
    ? result.topology?.edges ?? []
    : PLACEHOLDER_EDGES

  const driftEvent = hasResult ? result.repair?.drift_event : null
  const region = hasResult ? result.repair?.region : null

  const driftedQubits = new Set(driftEvent?.drifted_qubits ?? [])
  const regionQubits = new Set(region?.physical_qubits ?? [])

  const driftedEdges = new Set(
    (driftEvent?.drifted_edges ?? []).map(normalizeEdge)
  )

  const qubits = positions.map((position) => {
    const isDrifted = driftedQubits.has(position.id)
    const inRegion = regionQubits.has(position.id)

    return {
      ...position,
      inRegion,
      status: isDrifted
        ? "drift"
        : inRegion
          ? "region"
          : "healthy",
    }
  })

  const hasDrift =
    driftedQubits.size > 0 || driftedEdges.size > 0

  const driftLabel =
    driftedQubits.size > 0
      ? [...driftedQubits].map((id) => `Q${id}`).join(", ") + " DRIFT"
      : driftedEdges.size > 0
        ? `EDGE (${[...driftedEdges][0].replace("-", ", ")}) DRIFT`
        : "NO DRIFT EVENT"

  const calloutDetail =
    regionQubits.size > 0
      ? `${regionQubits.size} QUBITS IN REPAIR REGION`
      : hasResult
        ? "NO REPAIR REGION REPORTED"
        : "RUN AN EXPERIMENT TO INSPECT DRIFT"

  return (
    <section className="topology-panel">
      <div className="topology-header">
        <div>
          <div
            className="section-kicker"
            style={{ marginBottom: "10px" }}
          >
            HARDWARE STATE
          </div>
          <h2>Physical topology</h2>
        </div>

        <div className="topology-status">
          <Activity size={13} />
          <span>{hasResult ? "LIVE DATA" : "AWAITING RUN"}</span>
        </div>
      </div>

      <div className="topology-meta">
        <div>
          <Network size={13} />
          <span>COUPLING GRAPH</span>
        </div>

        <div>
          <CircleDot size={12} />
          <span>{nQubits} PHYSICAL QUBITS</span>
        </div>
      </div>

      <div className="topology-canvas">
        <div className="topology-grid" />

        <svg
          className="topology-edges"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          role="img"
          aria-label="Physical qubit coupling graph"
          style={{
            position: "absolute",
            inset: 0,
            display: "block",
            width: "100%",
            height: "100%",
            zIndex: 2,
            overflow: "hidden",
            pointerEvents: "none",
          }}
        >
          {connections.map(([from, to], index) => {
            const start = positions[from]
            const end = positions[to]

            if (!start || !end) return null

            const edgeKey = normalizeEdge([from, to])
            const isDrifted = driftedEdges.has(edgeKey)

            return (
              <line
                key={`${edgeKey}-${index}`}
                x1={start.x}
                y1={start.y}
                x2={end.x}
                y2={end.y}
                style={{
                  stroke: isDrifted
                    ? "var(--orange)"
                    : "rgba(167, 139, 250, 0.65)",
                  strokeWidth: isDrifted ? 1.5 : 1.1,
                  opacity: 1,
                  vectorEffect: "non-scaling-stroke",
                  filter: isDrifted
                    ? "drop-shadow(0 0 2px rgba(249, 115, 22, 0.55))"
                    : "none",
                }}
              />
            )
          })}
        </svg>

        {qubits.map((qubit) => (
          <TopologyNode key={qubit.id} qubit={qubit} />
        ))}

        <div className="drift-callout">
          <span className="drift-indicator" />

          <div>
            <strong>{driftLabel}</strong>
            <span>{calloutDetail}</span>
          </div>
        </div>
      </div>

      <div className="topology-legend">
        <div>
          <span className="legend-dot healthy" />
          <span>HEALTHY</span>
        </div>

        <div>
          <span className="legend-dot drifted" />
          <span>DRIFTED</span>
        </div>

        <div>
          <span className="legend-region" />
          <span>REPAIR REGION</span>
        </div>
      </div>
    </section>
  )
}

export default TopologyPanel