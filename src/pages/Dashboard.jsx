import DashboardHeader from "../components/DashboardHeader"
import ExperimentConfig from "../components/ExperimentConfig"
import TopologyPanel from "../components/TopologyPanel"
import CompilerPipeline from "../components/CompilerPipeline"
import RepairDecision from "../components/RepairDecision"
import EventLog from "../components/EventLog"
import ResultsOverview from "../components/ResultsOverview"
import CircuitComparison from "../components/CircuitComparison"
import "./Dashboard.css"

function Dashboard() {
  return (
    <main className="dashboard-page">
      <DashboardHeader />

      <section className="dashboard-content">
        <ExperimentConfig />

        <TopologyPanel />

        <CompilerPipeline />

        <RepairDecision />

        <EventLog />

        <ResultsOverview />

        <CircuitComparison />
      </section>
    </main>
  )
}

export default Dashboard