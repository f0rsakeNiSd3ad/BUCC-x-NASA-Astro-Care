"""
test_health_summarizer.py

Unit tests for health_summarizer.py ensuring thresholds and output formats 
adhere to mission requirements (no diagnostics, correct JSON structure).
"""

import pytest
from health_summarizer import HealthSummarizer

@pytest.fixture
def summarizer():
    return HealthSummarizer()

def test_nominal_status(summarizer):
    report = summarizer.summarize(
        astronaut_id="AST-001",
        mission_phase="mid_mission",
        deviations=[]
    )
    
    assert "GREEN" in report["status_codes"]
    assert report["overall_status"] == "NOMINAL"
    assert "nominal" in report["status_explanation"]["summary"]
    assert report["recommended_actions"][0]["action"] == "MONITOR"

def test_yellow_caution_status(summarizer):
    deviations = [{
        "parameter": "heart_rate",
        "current_value": 105,
        "expected_range": {"lower": 70, "upper": 82},
        "z_score": 1.8,
        "severity": "moderate_elevation",
        "contributing_factors": [{"factor": "elevated_co2", "confidence": 0.8}]
    }]
    
    report = summarizer.summarize(
        astronaut_id="AST-001",
        mission_phase="mid_mission",
        deviations=deviations
    )
    
    assert "YELLOW" in report["status_codes"]
    assert report["overall_status"] == "NOMINAL_WITH_CAUTION"
    assert "heart rate" in report["status_explanation"]["summary"]
    assert any(a["action"] == "OPTIONAL_FSE_CONSULT" for a in report["recommended_actions"])

def test_orange_concern_status_single_significant(summarizer):
    deviations = [{
        "parameter": "hrv_rmssd",
        "current_value": 20,
        "expected_range": "40±8",
        "z_score": -2.5,
        "severity": "significant_reduction"
    }]
    
    report = summarizer.summarize(
        astronaut_id="AST-002",
        mission_phase="adaptation",
        deviations=deviations
    )
    
    assert "ORANGE" in report["status_codes"]
    assert report["overall_status"] == "CONCERN"
    
def test_orange_concern_status_multiple_moderate(summarizer):
    deviations = [
        {"parameter": "hr", "z_score": 1.6},
        {"parameter": "bp", "z_score": 1.7},
        {"parameter": "spo2", "z_score": -1.5}
    ]
    
    report = summarizer.summarize("AST-003", "late_mission", deviations)
    assert "ORANGE" in report["status_codes"]
    assert report["overall_status"] == "CONCERN"

def test_red_alert_status(summarizer):
    deviations = [{
        "parameter": "spo2",
        "current_value": 88,
        "expected_range": "95-100",
        "z_score": -3.2,
        "severity": "critical"
    }]
    
    report = summarizer.summarize("AST-001", "early_flight", deviations)
    assert "RED" in report["status_codes"]
    assert report["overall_status"] == "ALERT"
    
    actions = [a["action"] for a in report["recommended_actions"]]
    assert "IMMEDIATE_FSE_CONSULT" in actions

def test_no_medical_diagnosis(summarizer):
    deviations = [{"parameter": "heart_rate", "z_score": 3.0}]
    report = summarizer.summarize("AST-001", "mid_mission", deviations)
    
    summary = report["status_explanation"]["summary"].lower()
    # Ensure diagnostic words are NOT used
    assert "infection" not in summary
    assert "disease" not in summary
    assert "tachycardia" not in summary
