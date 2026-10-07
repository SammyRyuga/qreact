import { Activity, CircleDot, Network } from "lucide-react"
import "./TopologyPanel.css"

const qubits = [
  { id: 0, x: 16, y: 52 },
  { id: 1, x: 35, y: 30 },
  { id: 2, x: 53, y: 52, status: "drift" },
  { id: 3, x: 73, y: 30 },
  { id: 4, x: 34, y: 72 },
  { id: 5, x: 53, y: 86 },
  { id: 6, x: 71, y: 69 },
  { id: 7, x: 16, y: 86 },
]

const connections = [
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

function TopologyNode({ qubit }) {
  return (
    <div
      className={`topology-node ${qubit.status === "drift" ? "drift" : ""}`}
      style={{
        left: `${qubit.x}%`,
        top: `${qubit.y}%`,
      }}
    >
      <div className="topology-node-glow" />
      <div className="topology-node-core" />
      <span>Q{qubit.id}</span>
    </div>
  )
}

function TopologyEdge({ from, to }) {
  const start = qubits[from]
  const end = qubits[to]

  const dx = end.x - start.x
  const dy = end.y - start.y
  const length = Math.sqrt(dx * dx + dy * dy)
  const angle = Math.atan2(dy, dx) * (180 / Math.PI)

  return (
    <div
      className="topology-edge"
      style={{
        left: `${start.x}%`,
        top: `${start.y}%`,
        width: `${length}%`,
        transform: `rotate(${angle}deg)`,
      }}
    />
  )
}

function TopologyPanel() {
  return (
    <section className="topology-panel">
      <div className="topology-header">
        <div>
          <div className="section-kicker">HARDWARE STATE</div>

          <h2>Physical topology</h2>
        </div>

        <div className="topology-status">
          <Activity size={13} />
          <span>MONITORING</span>
        </div>
      </div>

      <div className="topology-meta">
        <div>
          <Network size={13} />
          <span>COUPLING GRAPH</span>
        </div>

        <div>
          <CircleDot size={12} />
          <span>8 PHYSICAL QUBITS</span>
        </div>
      </div>

      <div className="topology-canvas">
        <div className="topology-grid" />

        {connections.map(([from, to], index) => (
          <TopologyEdge key={`${from}-${to}-${index}`} from={from} to={to} />
        ))}

        <div className="affected-region" />

        {qubits.map((qubit) => (
          <TopologyNode key={qubit.id} qubit={qubit} />
        ))}

        <div className="drift-callout">
          <span className="drift-indicator" />

          <div>
            <strong>Q2 DRIFT</strong>
            <span>REPAIR CANDIDATE REGION</span>
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