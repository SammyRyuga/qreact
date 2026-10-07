import {
  Activity,
  ArrowUpRight,
  Code2,
  Cpu,
  GitBranch,
  Mail,
  ShieldCheck,
  Terminal,
} from "lucide-react"
import "./About.css"

function About() {
  return (
    <main className="about-page">
      <section className="about-hero">
        <div className="about-hero-copy">
          <div className="section-kicker">ABOUT Q//REACT</div>

          <h1>
            Compilation that
            <br />
            <span>responds to hardware change.</span>
          </h1>

          <p className="about-lead">
            Q//REACT explores a different response to calibration drift in
            quantum processors: preserve the compiled work that remains valid,
            isolate what has changed, and repair only the affected region when
            a safe correction exists.
          </p>
        </div>

        <div className="about-system-card">
          <div className="about-system-header">
            <span>SYSTEM</span>
            <span className="about-live-dot" />
          </div>

          <div className="about-system-line">
            <span>COMPILER</span>
            <strong>Q//REACT</strong>
          </div>

          <div className="about-system-line">
            <span>MODE</span>
            <strong>CALIBRATION-REACTIVE</strong>
          </div>

          <div className="about-system-line">
            <span>REPAIR</span>
            <strong>BOUNDED / VERIFIED</strong>
          </div>

          <div className="about-system-line">
            <span>FAILSAFE</span>
            <strong>FULL RETRANSPILE</strong>
          </div>
        </div>
      </section>

      <section className="about-section">
        <div className="about-section-label">
          <span>01</span>
          <span>THE PROBLEM</span>
        </div>

        <div className="about-section-content">
          <h2>
            Quantum hardware does not
            <br />
            stay perfectly still.
          </h2>

          <p>
            Calibration characteristics can change while a previously compiled
            circuit is still relevant. A conventional response is to treat
            that change as a reason to reconsider the entire compilation.
          </p>

          <p>
            Q//REACT investigates whether that response can be made more
            selective: identify the resources affected by drift, localize the
            corresponding region of the compiled circuit, and determine
            whether a constrained repair can preserve the rest of the
            compilation.
          </p>
        </div>
      </section>

      <section className="about-section about-section-alt">
        <div className="about-section-label">
          <span>02</span>
          <span>THE APPROACH</span>
        </div>

        <div className="about-method-grid">
          <article className="about-method-card">
            <div className="about-method-icon">
              <Activity size={18} />
            </div>

            <span>01 / DETECT</span>

            <h3>Observe drift</h3>

            <p>
              Track changes in calibration data and identify the physical
              resources whose characteristics have crossed the configured
              threshold.
            </p>
          </article>

          <article className="about-method-card">
            <div className="about-method-icon">
              <GitBranch size={18} />
            </div>

            <span>02 / LOCALIZE</span>

            <h3>Bound the repair</h3>

            <p>
              Construct a constrained region around the affected resources
              rather than treating the entire compiled circuit as invalid.
            </p>
          </article>

          <article className="about-method-card">
            <div className="about-method-icon">
              <ShieldCheck size={18} />
            </div>

            <span>03 / VERIFY</span>

            <h3>Prove before accepting</h3>

            <p>
              Candidate repairs are checked against topology, locality,
              preservation, semantics, and disruption constraints.
            </p>
          </article>

          <article className="about-method-card">
            <div className="about-method-icon">
              <Cpu size={18} />
            </div>

            <span>04 / FALL BACK</span>

            <h3>Recompile when necessary</h3>

            <p>
              When a safe local repair cannot be established, the system falls
              back to a fresh full recompilation instead of accepting an
              unverified modification.
            </p>
          </article>
        </div>
      </section>

      <section className="about-section">
        <div className="about-section-label">
          <span>03</span>
          <span>IMPLEMENTATION</span>
        </div>

        <div className="about-implementation">
          <div>
            <h2>
              Built as a compiler
              <br />
              system, not a visual mockup.
            </h2>

            <p>
              The project is implemented around a real quantum compilation
              pipeline and an interactive experimental interface. The browser
              layer visualizes the decisions made by the underlying compiler
              rather than replacing them with a simulated presentation.
            </p>
          </div>

          <div className="about-stack">
            <div className="about-stack-row">
              <span>QUANTUM COMPILER</span>
              <strong>QISKIT</strong>
            </div>

            <div className="about-stack-row">
              <span>SIMULATION</span>
              <strong>AER</strong>
            </div>

            <div className="about-stack-row">
              <span>TOPOLOGY / GRAPH</span>
              <strong>NETWORKX</strong>
            </div>

            <div className="about-stack-row">
              <span>SERVER</span>
              <strong>FLASK</strong>
            </div>

            <div className="about-stack-row">
              <span>INTERFACE</span>
              <strong>REACT</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="about-principles">
        <div className="about-principles-inner">
          <div className="about-principles-heading">
            <div className="section-kicker">DESIGN PRINCIPLES</div>

            <h2>
              Locality is useful.
              <br />
              <span>Verification is mandatory.</span>
            </h2>
          </div>

          <div className="about-principles-list">
            <div className="about-principle">
              <Terminal size={16} />
              <span>CHANGE ONLY WHAT CAN BE JUSTIFIED</span>
            </div>

            <div className="about-principle">
              <ShieldCheck size={16} />
              <span>NEVER DEPLOY AN UNVERIFIED LOCAL PATCH</span>
            </div>

            <div className="about-principle">
              <GitBranch size={16} />
              <span>KEEP LOCAL REPAIR MEASURABLE AND BOUNDED</span>
            </div>
          </div>
        </div>
      </section>

      <section className="about-footer">
        <div>
          <span className="about-footer-kicker">Q//REACT</span>
          <p>
            An experimental compiler architecture for reacting to changing
            quantum hardware without immediately discarding everything that
            still works.
          </p>
        </div>

        <span className="about-footer-mark">Q//R</span>
      </section>

      <section className="about-creators">
        <div className="about-creators-header">
          <div>
            <div className="section-kicker">THE PEOPLE BEHIND IT</div>

            <h2>
              Built together.
              <br />
              <span>Two co-creators.</span>
            </h2>
          </div>

          <p>
            Q//REACT is a collaborative compiler research project developed
            around the study of calibration-reactive compilation for quantum
            hardware.
          </p>
        </div>

        <div className="about-creators-grid">
          <article className="creator-card">
            <div className="creator-content">
              <div className="creator-top">
                <div>
                  <span className="creator-role">CO-CREATOR</span>
                  <h3>Samanyu Pattanayak</h3>
                </div>

                <span className="creator-symbol">Q//R</span>
              </div>

              <div className="creator-divider"></div>

              <div className="creator-links">
                <a
                  href="https://www.linkedin.com/in/samanyu-pattanayak-8757551a9/"
                  target="_blank"
                  rel="noreferrer"
                  className="creator-link"
                >
                  <ArrowUpRight size={16} />
                  <span>LINKEDIN</span>
                </a>

                <a
                  href="mailto:samanyupattanayak@gmail.com"
                  className="creator-link"
                >
                  <Mail size={16} />
                  <span>GMAIL</span>
                </a>

                <a
                  href="https://github.com/sammyryuga"
                  target="_blank"
                  rel="noreferrer"
                  className="creator-link"
                >
                  <Code2 size={16} />
                  <span>GITHUB</span>
                </a>
              </div>
            </div>
          </article>

          <article className="creator-card">
            <div className="creator-content">
              <div className="creator-top">
                <div>
                  <span className="creator-role">CO-CREATOR</span>
                  <h3>Ashita Singh</h3>
                </div>

                <span className="creator-symbol">Q//R</span>
              </div>

              <div className="creator-divider"></div>

              <div className="creator-links">
                <a
                  href="https://www.linkedin.com/in/ashita-singh-5828a9257/"
                  target="_blank"
                  rel="noreferrer"
                  className="creator-link"
                >
                  <ArrowUpRight size={16} />
                  <span>LINKEDIN</span>
                </a>

                <a
                  href="mailto:ashita2825@gmail.com"
                  className="creator-link"
                >
                  <Mail size={16} />
                  <span>GMAIL</span>
                </a>

                <a
                  href="https://github.com/ash28git"
                  target="_blank"
                  rel="noreferrer"
                  className="creator-link"
                >
                  <Code2 size={16} />
                  <span>GITHUB</span>
                </a>
              </div>
            </div>
          </article>
        </div>
      </section>
    </main>
  )
}

export default About