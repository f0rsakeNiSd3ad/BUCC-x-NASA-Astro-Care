import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import math

class BaselineCalculator:
    """
    Calculates Earth baselines and Mission Adaptation baselines for astronauts.
    Ensures mathematical operations are deterministic and handle anomalous inputs cleanly.
    """

    @staticmethod
    def _clean_float(val: Any) -> Optional[float]:
        """Convert to float and return None if NaN or Inf."""
        if val is None:
            return None
        try:
            f_val = float(val)
            if math.isnan(f_val) or math.isinf(f_val):
                return None
            return f_val
        except (ValueError, TypeError):
            return None

    @staticmethod
    def calculate_earth_baseline(astronaut_id: str, pre_flight_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates the Earth Baseline from pre-flight medical data.
        
        Args:
            astronaut_id: The ID of the astronaut.
            pre_flight_data: A list of dictionaries containing pre-flight measurements.
                
        Returns:
            A dictionary representing the Earth Baseline profile.
        """
        if not pre_flight_data:
            raise ValueError("Pre-flight data cannot be empty.")

        df = pd.DataFrame(pre_flight_data)
        
        def get_stats(col: str):
            if col not in df.columns:
                return None, None
            series = pd.to_numeric(df[col], errors='coerce').dropna()
            if series.empty:
                return None, None
            return BaselineCalculator._clean_float(series.mean()), BaselineCalculator._clean_float(series.std(ddof=0))
            
        def get_median(col: str):
            if col not in df.columns:
                return None
            series = pd.to_numeric(df[col], errors='coerce').dropna()
            if series.empty:
                return None
            return BaselineCalculator._clean_float(series.median())

        hr_mean, hr_std = get_stats('heart_rate_resting')
        sys_mean, sys_std = get_stats('systolic_bp')
        dia_mean, dia_std = get_stats('diastolic_bp')
        spo2_mean, spo2_std = get_stats('spo2')
        
        rmssd_mean, rmssd_std = get_stats('rmssd')
        lf_hf_mean, lf_hf_std = get_stats('lf_hf_ratio')
        
        sleep_dur = get_median('sleep_duration')
        sleep_eff = get_median('sleep_efficiency')
        sleep_rem = get_median('rem_percentage')
        
        vo2_max = get_median('vo2_max')
        energy = get_median('daily_energy')
        
        fatigue = get_median('fatigue_scale')
        stress = get_median('stress_scale')
        
        current_date = datetime.utcnow().isoformat() + "Z"

        return {
            "astronaut_id": astronaut_id,
            "collection_date": current_date,
            "earth_baseline": {
                "vital_signs": {
                    "heart_rate_resting": {"value": hr_mean, "unit": "bpm", "std_dev": hr_std},
                    "blood_pressure": {"systolic": sys_mean, "diastolic": dia_mean, "unit": "mmHg"},
                    "spo2": {"value": spo2_mean, "unit": "%", "std_dev": spo2_std}
                },
                "hrv": {
                    "rmssd": {"value": rmssd_mean, "unit": "ms", "std_dev": rmssd_std},
                    "lf_hf_ratio": {"value": lf_hf_mean, "std_dev": lf_hf_std}
                },
                "sleep": {
                    "duration": {"value": sleep_dur, "unit": "hours"},
                    "efficiency": {"value": sleep_eff, "unit": "%"},
                    "rem_percentage": {"value": sleep_rem, "unit": "%"}
                },
                "activity": {
                    "vo2_max": {"value": vo2_max, "unit": "ml/kg/min"},
                    "daily_energy": {"value": energy, "unit": "kcal"}
                },
                "psychometrics": {
                    "fatigue_scale": {"value": fatigue, "scale": "1-10"},
                    "stress_scale": {"value": stress, "scale": "1-10"}
                }
            }
        }

    @staticmethod
    def calculate_mission_adaptation_baseline(
        astronaut_id: str,
        parameter: str,
        earth_value_median: Optional[float],
        mission_timeseries: List[Dict[str, Any]],
        mission_phase: str = "early_flight"
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates Mission Adaptation Baseline for a specific parameter over a 14-day window.
        
        Args:
            astronaut_id: ID of the astronaut.
            parameter: The physiological parameter being tracked (e.g., 'heart_rate').
            earth_value_median: The median value of the parameter on Earth.
            mission_timeseries: List of dicts with 'timestamp', 'value', 'acute_illness', 'medication_change'.
            mission_phase: The current mission phase string.
            
        Returns:
            A dictionary representing the Mission Adaptation Baseline, or None if stability criteria fail.
        """
        if not mission_timeseries:
            return None
            
        df = pd.DataFrame(mission_timeseries)
        
        if 'value' not in df.columns or df['value'].isnull().all():
            return None
            
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        valid_df = df.dropna(subset=['value'])
        
        if valid_df.empty:
            return None
            
        # Stability Criteria Checks
        if 'acute_illness' in df.columns and df['acute_illness'].any():
            return None
            
        if 'medication_change' in df.columns and df['medication_change'].any():
            return None
            
        completeness = len(valid_df) / len(df)
        if completeness < 0.8:
            return None
            
        mean_val = valid_df['value'].mean()
        std_val = valid_df['value'].std(ddof=0)
        
        if mean_val == 0 or pd.isna(mean_val):
            return None
            
        cv = (std_val / abs(mean_val))
        if cv >= 0.15:
            return None
            
        expected_median = BaselineCalculator._clean_float(valid_df['value'].median())
        q25 = BaselineCalculator._clean_float(valid_df['value'].quantile(0.25))
        q75 = BaselineCalculator._clean_float(valid_df['value'].quantile(0.75))
        
        adaptation_factor = None
        if earth_value_median is not None and earth_value_median != 0:
            adaptation_factor = BaselineCalculator._clean_float(expected_median / earth_value_median)
            
        confidence = min(1.0, completeness * (1.0 - cv))
        
        start_time = datetime.utcnow().isoformat() + "Z"
        if 'timestamp' in valid_df.columns and not pd.isna(valid_df['timestamp'].iloc[0]):
            start_time = str(valid_df['timestamp'].iloc[0])
            
        return {
            "astronaut_id": astronaut_id,
            "mission_phase": mission_phase,
            "learning_window_start": start_time,
            "mission_adaptation_baseline": {
                "parameter": parameter,
                "earth_value_median": BaselineCalculator._clean_float(earth_value_median),
                "mission_expected_median": expected_median,
                "mission_expected_iqr": {"lower": q25, "upper": q75},
                "adaptation_factor": adaptation_factor,
                "confidence": BaselineCalculator._clean_float(round(confidence, 4)),
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
        }
