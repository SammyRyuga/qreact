import { Activity, ArrowLeft, Settings2 } from "lucide-react"
import { Link } from "react-router-dom"
import "./DashboardHeader.css"

function DashboardHeader() {
  return (
    <section className="dashboard-header">
      <div className="dashboard-header-left">
        <Link to="/" className="back-link">
          <ArrowLeft size={14} />
          <span>BACK TO Q//REACT</span>
        </Link>

        <div className="dashboard-title-row">
          <div>
            <div className="section-kicker" style={{marginBottom: '15px'}}>INTERACTIVE COMPILER</div>

            <h1>Compiler Dashboard</h1>
          </div>

          <div className="dashboard-live">
            <span className="live-indicator"></span>
            <Activity size={14} />
            <span>ENGINE READY</span>
          </div>
        </div>
      </div>

      <div className="dashboard-actions">
        <button className="dashboard-icon-button" type="button">
          <Settings2 size={16} />
        </button>
      </div>
    </section>
  )
}

export default DashboardHeader