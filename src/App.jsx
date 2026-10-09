import { useState } from "react"
import { BrowserRouter, Routes, Route } from "react-router-dom"

import Navbar from "./components/Navbar"
import Landing from "./pages/Landing"
import Dashboard from "./pages/Dashboard"
import Analysis from "./pages/Analysis"
import About from "./pages/About"

function App() {
  const [result, setResult] = useState(null)

  return (
    <BrowserRouter>
      <div className="app">
        <Navbar />

        <Routes>
          <Route
            path="/"
            element={<Landing />}
          />

          <Route
            path="/dashboard"
            element={
              <Dashboard
                result={result}
                setResult={setResult}
              />
            }
          />

          <Route
            path="/analysis"
            element={
              <Analysis
                result={result}
              />
            }
          />

          <Route
            path="/about"
            element={<About />}
          />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App