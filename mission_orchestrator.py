import sys
import os
import random
from datetime import datetime, timedelta

# Ensure the modules can be imported
sys.path.append("g:/NASA")

from baseline_calculator import BaselineCalculator
from health_summarizer import HealthSummarizer
from osdr_client import OSDRClient

def run_30_day_mission():
    print("--- Starting 30-Day Mission Simulation ---")
    
    # 1. Generate Pre-flight Data
    pre_flight_data = []
    for _ in range(14):
        pre_flight_data.append({
            "heart_rate_resting": random.uniform(55, 65),
            "systolic_bp": random.uniform(115, 125),
            "diastolic_bp": random.uniform(75, 85),
            "spo2": random.uniform(97, 100),
            "rmssd": random.uniform(35, 45),
            "lf_hf_ratio": random.uniform(1.0, 1.5),
            "sleep_duration": random.uniform(7.0, 8.5),
            "sleep_efficiency": random.uniform(80, 95),
            "rem_percentage": random.uniform(20, 25),
            "vo2_max": random.uniform(40, 50),
            "daily_energy": random.uniform(2400, 2800),
            "fatigue_scale": random.randint(1, 3),
            "stress_scale": random.randint(1, 3)
        })
    
    # 2. Calculate Earth Baseline
    earth_baseline = BaselineCalculator.calculate_earth_baseline("ASTRO-1", pre_flight_data)
    earth_hr_median = earth_baseline["earth_baseline"]["vital_signs"]["heart_rate_resting"]["value"]
    print(f"Earth Baseline Calculated. Resting HR Median: {earth_hr_median:.1f} bpm")
    
    # 3. Simulate 30 Days of In-Flight Data
    summarizer = HealthSummarizer()
    mission_timeseries = []
    start_date = datetime.utcnow()
    
    for day in range(1, 31):
        # Inject an anomaly on Day 15 (e.g., elevated stress / environmental factor)
        if day == 15:
            hr_val = 98.0
            bp_sys = 145.0
        else:
            hr_val = random.uniform(62, 72)
            bp_sys = random.uniform(118, 128)
            
        timestamp_str = (start_date + timedelta(days=day)).isoformat() + "Z"
        
        mission_timeseries.append({
            "timestamp": timestamp_str,
            "value": hr_val,
            "acute_illness": False,
            "medication_change": False
        })
        
        # 4. Calculate Mission Adaptation Baseline (14-day rolling window)
        adaptation = None
        if day >= 14:
            adaptation = BaselineCalculator.calculate_mission_adaptation_baseline(
                astronaut_id="ASTRO-1",
                parameter="heart_rate",
                earth_value_median=earth_hr_median,
                mission_timeseries=mission_timeseries[-14:],
                mission_phase="mid_flight"
            )
            
        # 5. Evaluate Health Status for the day
        deviations = []
        # Calculate z-score using standard deviation from Earth baseline (assumed ~1.0 for HR)
        expected_hr = adaptation["mission_adaptation_baseline"]["mission_expected_median"] if adaptation else earth_hr_median
        z_score_hr = (hr_val - expected_hr) / 1.5 
        
        if abs(z_score_hr) >= 1.5:
            deviations.append({
                "parameter": "heart_rate",
                "current_value": hr_val,
                "z_score": z_score_hr,
                "severity": "elevated" if z_score_hr > 0 else "depressed"
            })
            
        health_report = summarizer.summarize(
            astronaut_id="ASTRO-1",
            mission_phase="mid_flight",
            deviations=deviations
        )
        
        # Report out every 5 days + anomalies
        if day % 5 == 0 or day == 15:
            print(f"\nDay {day} Report:")
            print(f"  HR: {hr_val:.1f} bpm (Expected: {expected_hr:.1f})")
            print(f"  Status: {health_report['overall_status']}")
            print(f"  Summary: {health_report['status_explanation']['summary']}")
            if health_report['recommended_actions']:
                print(f"  Action: {health_report['recommended_actions'][0]['action']}")

    print("\n--- 30-Day Mission Simulation Completed ---")

if __name__ == "__main__":
    run_30_day_mission()
