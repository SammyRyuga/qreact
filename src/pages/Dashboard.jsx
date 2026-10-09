import DashboardHeader from "../components/DashboardHeader"
import ExperimentConfig from "../components/ExperimentConfig"
import TopologyPanel from "../components/TopologyPanel"
import CompilerPipeline from "../components/CompilerPipeline"
import RepairDecision from "../components/RepairDecision"
import EventLog from "../components/EventLog"
import ResultsOverview from "../components/ResultsOverview"
import CircuitComparison from "../components/CircuitComparison"

import "./Dashboard.css"

function Dashboard({ result, setResult }) {
  return (
    <main className="dashboard-page">
      <DashboardHeader />

      <section className="dashboard-content">
        <ExperimentConfig onResult={setResult} />

        <TopologyPanel result={result} />

        <CompilerPipeline result={result} />

        <RepairDecision result={result} />

        <EventLog result={result} />

        <ResultsOverview result={result} />

        <CircuitComparison result={result} />
      </section>
    </main>
  )
}

export default Dashboard