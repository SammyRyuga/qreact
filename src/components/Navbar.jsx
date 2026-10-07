import { Activity, Cpu, Code2 } from "lucide-react"
import { Link } from "react-router-dom"
import "./Navbar.css"

function Navbar() {
  return (
    <header className="navbar">
      <Link to="/" className="brand">
        <div className="brand-mark">
          <span></span>
          <span></span>
          <span></span>
        </div>

        <div className="brand-copy">
          <div className="brand-name">Q//REACT</div>
          <div className="brand-subtitle">
            CALIBRATION-REACTIVE COMPILER
          </div>
        </div>
      </Link>

      <nav className="nav-center">
        <Link to="/" className="nav-link">
          HOME
        </Link>

        <Link to="/dashboard" className="nav-link">
          DASHBOARD
        </Link>

        <Link to="/analysis" className="nav-link">
          ANALYSIS
        </Link>

        <Link to="/about" className="nav-link">
          ABOUT
        </Link>
      </nav>

      <div className="nav-status">
        <div className="status-item status-online">
          <Activity size={14} />
          <span>ENGINE ONLINE</span>
        </div>

        <div className="status-item">
          <Cpu size={14} />
          <span>QISKIT</span>
        </div>

        <div className="status-item">
          <Code2 size={14} />
        </div>
      </div>
    </header>
  )
}

export default Navbar