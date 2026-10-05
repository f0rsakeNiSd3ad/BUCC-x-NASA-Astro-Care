import pytest
import pandas as pd
import numpy as np
from baseline_calculator import BaselineCalculator

def test_earth_baseline_normal():
    data = [
        {"heart_rate_resting": 60, "systolic_bp": 120, "diastolic_bp": 80, "spo2": 98, "rmssd": 40, "lf_hf_ratio": 1.2, "sleep_duration": 7.5, "sleep_efficiency": 85, "rem_percentage": 20, "vo2_max": 45, "daily_energy": 2500, "fatigue_scale": 2, "stress_scale": 3},
        {"heart_rate_resting": 62, "systolic_bp": 122, "diastolic_bp": 82, "spo2": 99, "rmssd": 42, "lf_hf_ratio": 1.3, "sleep_duration": 8.0, "sleep_efficiency": 88, "rem_percentage": 22, "vo2_max": 46, "daily_energy": 2600, "fatigue_scale": 3, "stress_scale": 2}
    ]
    result = BaselineCalculator.calculate_earth_baseline("ASTRO-1", data)
    assert result["astronaut_id"] == "ASTRO-1"
    assert result["earth_baseline"]["vital_signs"]["heart_rate_resting"]["value"] == 61.0
    assert result["earth_baseline"]["vital_signs"]["heart_rate_resting"]["std_dev"] == 1.0

def test_earth_baseline_missing_data():
    data = [
        {"heart_rate_resting": 60},
        {"heart_rate_resting": None, "systolic_bp": 120},
        {}
    ]
    result = BaselineCalculator.calculate_earth_baseline("ASTRO-2", data)
    assert result["earth_baseline"]["vital_signs"]["heart_rate_resting"]["value"] == 60.0
    assert result["earth_baseline"]["vital_signs"]["heart_rate_resting"]["std_dev"] == 0.0
    assert result["earth_baseline"]["vital_signs"]["blood_pressure"]["systolic"] == 120.0
    assert result["earth_baseline"]["vital_signs"]["spo2"]["value"] is None

def test_earth_baseline_empty_input():
    with pytest.raises(ValueError, match="Pre-flight data cannot be empty"):
        BaselineCalculator.calculate_earth_baseline("ASTRO-3", [])

def test_mission_adaptation_normal():
    timeseries = [
        {"timestamp": "2026-01-01T00:00:00Z", "value": 70, "acute_illness": False, "medication_change": False},
        {"timestamp": "2026-01-02T00:00:00Z", "value": 72, "acute_illness": False, "medication_change": False},
        {"timestamp": "2026-01-03T00:00:00Z", "value": 71, "acute_illness": False, "medication_change": False},
        {"timestamp": "2026-01-04T00:00:00Z", "value": 73, "acute_illness": False, "medication_change": False},
        {"timestamp": "2026-01-05T00:00:00Z", "value": 70, "acute_illness": False, "medication_change": False},
    ]
    
    result = BaselineCalculator.calculate_mission_adaptation_baseline(
        astronaut_id="ASTRO-1",
        parameter="heart_rate",
        earth_value_median=60,
        mission_timeseries=timeseries
    )
    
    assert result is not None
    assert result["mission_adaptation_baseline"]["parameter"] == "heart_rate"
    assert result["mission_adaptation_baseline"]["mission_expected_median"] == 71.0
    assert result["mission_adaptation_baseline"]["adaptation_factor"] == 71.0 / 60.0

def test_mission_adaptation_high_cv():
    # CV > 15% should return None
    timeseries = [
        {"value": 70}, {"value": 100}, {"value": 50}, {"value": 120}, {"value": 60}
    ]
    result = BaselineCalculator.calculate_mission_adaptation_baseline("ASTRO-1", "hr", 60, timeseries)
    assert result is None

def test_mission_adaptation_illness():
    timeseries = [
        {"value": 70, "acute_illness": False},
        {"value": 72, "acute_illness": True},
    ]
    result = BaselineCalculator.calculate_mission_adaptation_baseline("ASTRO-1", "hr", 60, timeseries)
    assert result is None

def test_mission_adaptation_incomplete_data():
    # Less than 80% completeness
    timeseries = [{"value": 70}, {"value": None}, {"value": None}, {"value": None}, {"value": None}]
    result = BaselineCalculator.calculate_mission_adaptation_baseline("ASTRO-1", "hr", 60, timeseries)
    assert result is None
    
def test_clean_float():
    assert BaselineCalculator._clean_float("12.5") == 12.5
    assert BaselineCalculator._clean_float(None) is None
    assert BaselineCalculator._clean_float(np.nan) is None
    assert BaselineCalculator._clean_float("invalid") is None
