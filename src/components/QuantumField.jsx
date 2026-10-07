import "./QuantumField.css"

function QuantumNode({ label, className = "" }) {
  return (
    <div className={`quantum-node ${className}`}>
      <div className="node-glow" />
      <div className="node-core" />
      <span>{label}</span>
    </div>
  )
}

function QuantumField() {
  return (
    <div className="quantum-visual">
      <div className="visual-label">
        <span>PHYSICAL TOPOLOGY</span>
        <span>8 QUBITS</span>
      </div>

      <div className="quantum-field">
        <div className="connection connection-1" />
        <div className="connection connection-2" />
        <div className="connection connection-3" />
        <div className="connection connection-4" />
        <div className="connection connection-5" />
        <div className="connection connection-6" />

        <QuantumNode label="Q0" className="q1" />
        <QuantumNode label="Q1" className="q2" />
        <QuantumNode label="Q2" className="q3 drift" />
        <QuantumNode label="Q3" className="q4" />
        <QuantumNode label="Q4" className="q5" />
        <QuantumNode label="Q5" className="q6" />
        <QuantumNode label="Q6" className="q7" />
        <QuantumNode label="Q7" className="q8" />

        <div className="region-ring" />

        <div className="drift-label">
          <span className="drift-dot" />
          DRIFT DETECTED
        </div>
      </div>
    </div>
  )
}

export default QuantumField