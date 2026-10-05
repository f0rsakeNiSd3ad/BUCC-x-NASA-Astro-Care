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
    print("--- Starting 30-Day Mission Simulation (Real OSDR Cohort) ---")
    client = OSDRClient()
    dataset = client.fetch_osdr_dataset("379")
    if not dataset:
        print("Failed to fetch OSDR dataset.")
        return None
        
    cohort = client.extract_baseline_cohort(dataset, mission_type="ISS")
    if not cohort:
        print("No flight missions found in cohort.")
        return None
        
    summarizer = HealthSummarizer()
    
    # Let's process the first subject in the flight cohort
    subject_data = cohort[0]
    astronaut_id = subject_data['astronaut_id']
    
    # 1. Calculate Earth Baseline
    pre_flight_data = []
    for vs in subject_data['preflights'].get('vital_signs', []):
        pre_flight_data.append({
            "heart_rate_resting": vs.get('hr'),
            "systolic_bp": vs.get('bp_sys'),
            "diastolic_bp": vs.get('bp_dia'),
            "spo2": vs.get('spo2')
        })
        
    earth_baseline = BaselineCalculator.calculate_earth_baseline(astronaut_id, pre_flight_data)
    earth_hr_median = earth_baseline["earth_baseline"]["vital_signs"]["heart_rate_resting"]["value"]
    
    # 2. Simulate 30 Days of In-Flight Data
    inflight_vitals = subject_data['inflight'].get('vital_signs', [])
    mission_timeseries = []
    
    results = []
    
    for day, vs in enumerate(inflight_vitals, start=1):
        # --- NEW TEST SCENARIO ---
        if day in [16, 17]:
            # 48-hour complete data dropout
            vs = {}
        elif day == 18:
            # Corrupted data point
            vs = {'hr': 'CORRUPT_STRING_NaN', 'timestamp': 'INVALID_TIMESTAMP'}
            
        hr_val = vs.get('hr')
        
        mission_timeseries.append({
            "timestamp": vs.get('timestamp'),
            "value": hr_val,
            "acute_illness": False,
            "medication_change": False
        })
        
        # 3. Calculate Mission Adaptation Baseline (14-day rolling window)
        adaptation = None
        if day >= 14:
            adaptation = BaselineCalculator.calculate_mission_adaptation_baseline(
                astronaut_id=astronaut_id,
                parameter="heart_rate",
                earth_value_median=earth_hr_median,
                mission_timeseries=mission_timeseries[-14:],
                mission_phase="mid_flight"
            )
            
        # 4. Evaluate Health Status for the day
        deviations = []
        expected_hr = adaptation["mission_adaptation_baseline"]["mission_expected_median"] if adaptation else earth_hr_median
        
        # Safely handle potentially missing or corrupted hr_val
        hr_float = None
        try:
            if hr_val is not None:
                hr_float = float(hr_val)
                z_score_hr = (hr_float - expected_hr) / 1.5 
                
                if abs(z_score_hr) >= 1.5:
                    deviations.append({
                        "parameter": "heart_rate",
                        "current_value": hr_float,
                        "z_score": z_score_hr,
                        "severity": "elevated" if z_score_hr > 0 else "depressed"
                    })
        except (ValueError, TypeError):
            # Graceful degradation - unable to parse float
            pass
            
        # Evaluate data completeness metric based on data availability
        completeness = 0.98 if hr_float is not None else 0.0
        
        health_report = summarizer.summarize(
            astronaut_id=astronaut_id,
            mission_phase="mid_flight",
            deviations=deviations,
            data_completeness=completeness
        )
        
        # Formulate fallback strings for the dashboard display
        display_hr = hr_float if hr_float is not None else hr_val
        
        results.append({
            "day": day,
            "timestamp": vs.get('timestamp', 'MISSING'),
            "hr_val": hr_float, # Give None to Streamlit line_chart for gaps
            "expected_hr": expected_hr,
            "status": health_report['overall_status'],
            "summary": health_report['status_explanation']['summary'] if hr_float is not None else "Data missing or corrupted. Unable to verify parameters.",
            "action": health_report['recommended_actions'][0]['action'] if health_report['recommended_actions'] else "NONE"
        })

    return {
        "astronaut_id": astronaut_id,
        "earth_hr_median": earth_hr_median,
        "daily_results": results
    }

if __name__ == "__main__":
    run_30_day_mission()
