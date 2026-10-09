import pytest
from app import app

BODY = {"n_log": 4, "n_phys": 8, "n_steps": 12, "threshold": 0.35, "seed": 11}


@pytest.fixture(scope="module")
def resp():
    r = app.test_client().post("/api/run", json=BODY)
    assert r.status_code == 200
    return r.get_json()


def test_legacy_keys_preserved(resp):
    assert resp["ok"] is True
    for k in ("config", "summary", "equivalence", "log", "charts", "example", "circuit_png"):
        assert k in resp
    for s in ("static", "full", "incremental"):
        assert set(resp["summary"][s]) == {"mean_fidelity", "total_cost", "num_recompiles", "gini_usage"}
        assert isinstance(resp["summary"][s]["total_cost"], int)
    assert set(resp["equivalence"]) == {"passed", "failed_fallback"}
    assert set(resp["charts"]) == {"fidelity", "cost", "gini"}
    assert all(isinstance(l, str) for l in resp["log"])
    assert resp["config"]["seed"] == 11 and resp["config"]["n_log"] == 4


def test_new_keys_present_and_structured(resp):
    assert isinstance(resp["events"], list) and resp["events"]
    assert {"event_type", "message", "step", "severity"} <= set(resp["events"][0])
    for k in ("drift_event", "region", "candidates", "selected_candidate", "verification", "fallback"):
        assert k in resp["repair"]
    inc = resp["metrics"]["incremental_repair"]
    for k in ("patch_acceptance_rate", "local_patch_count", "full_fallback_count", "drift_event_count",
              "mean_region_size", "mean_region_fraction", "mean_preservation_ratio", "verification_pass_rate",
              "fallback_rate"):
        assert k in inc
    for k in ("fidelity_delta_vs_static", "fidelity_delta_vs_full", "cost_savings_vs_full"):
        assert k in resp["metrics"]["comparative"]
    assert "synthetic" in resp["metrics"]["notes"]["calibration_source"]


def test_metrics_are_internally_consistent(resp):
    inc = resp["metrics"]["incremental_repair"]
    assert inc["local_patch_count"] + inc["full_fallback_count"] == inc["drift_event_count"]
    assert resp["summary"]["incremental"]["num_recompiles"] == 1 + inc["drift_event_count"]


def test_endpoint_is_deterministic_for_a_seed():
    c = app.test_client()
    a, b = c.post("/api/run", json=BODY).get_json(), c.post("/api/run", json=BODY).get_json()
    assert a["summary"] == b["summary"] and a["log"] == b["log"] and a["events"] == b["events"]


def test_old_minimal_request_still_works_and_demo_mode_accepted():
    r = app.test_client().post("/api/run", json={"seed": 7, "n_steps": 8, "demo_mode": True})
    assert r.status_code == 200 and r.get_json()["config"]["demo_mode"] is True


def test_edge_detection_opt_in():
    r = app.test_client().post("/api/run", json={**BODY, "detect_edges": True, "n_steps": 10}).get_json()
    assert r["ok"] and r["config"]["detect_edges"] is True


def test_index_page_served():
    assert app.test_client().get("/").status_code == 200
