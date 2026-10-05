import logging
import requests
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

OSDR_API_BASE = "https://osdr.nasa.gov/api/v2"

# --- Data Validation Schemas ---
# Validates structural integrity and type safety as per system-prompt.md

class VitalSigns(BaseModel):
    timestamp: str
    hr: Optional[float] = Field(None, description="Heart rate in bpm")
    bp_sys: Optional[float] = Field(None, description="Systolic blood pressure in mmHg")
    bp_dia: Optional[float] = Field(None, description="Diastolic blood pressure in mmHg")
    spo2: Optional[float] = Field(None, ge=0, le=100, description="Oxygen saturation in %")
    temp: Optional[float] = Field(None, description="Body temperature in °C")

class HRV(BaseModel):
    timestamp: str
    rmssd_ms: Optional[float] = None
    lf_hf_ratio: Optional[float] = None
    sample_count: Optional[int] = None

class Sleep(BaseModel):
    date: str
    duration: Optional[float] = Field(None, description="Sleep duration in hours")
    efficiency: Optional[float] = Field(None, ge=0, le=100)
    rem_percentage: Optional[float] = Field(None, ge=0, le=100, alias="rem%")
    nrem_percentage: Optional[float] = Field(None, ge=0, le=100, alias="nrem%")
    wake_count: Optional[int] = None
    restlessness: Optional[float] = None

class Activity(BaseModel):
    date: str
    steps: Optional[int] = None
    intensity_minutes: Optional[float] = None
    vo2_estimated: Optional[float] = None
    kcal_burned: Optional[float] = None

class Psychometrics(BaseModel):
    timestamp: str
    fatigue_1_10: Optional[int] = Field(None, ge=1, le=10)
    stress_1_10: Optional[int] = Field(None, ge=1, le=10)
    mood: Optional[str] = None
    notes: Optional[str] = None

class Environment(BaseModel):
    timestamp: str
    co2_ppm: Optional[float] = None
    temp_c: Optional[float] = None
    humidity_percentage: Optional[float] = Field(None, ge=0, le=100, alias="humidity%")
    radiation_dose_uSv: Optional[float] = Field(None, alias="radiation_dose_μSv")

class MissionEvent(BaseModel):
    timestamp: str
    event_type: str
    duration: Optional[float] = None
    description: Optional[str] = None

class TimeseriesData(BaseModel):
    vital_signs: List[VitalSigns] = []
    hrv: List[HRV] = []
    sleep: List[Sleep] = []
    activity: List[Activity] = []
    psychometrics: List[Psychometrics] = []
    environment: List[Environment] = []
    mission_events: List[MissionEvent] = []

class Mission(BaseModel):
    subject_id: str
    type: str
    duration: int
    preflights: Optional[TimeseriesData] = None
    inflight_timeseries: Optional[TimeseriesData] = None
    postflights: Optional[TimeseriesData] = None
    health_events: Optional[List[Dict[str, Any]]] = []

class OSDRDataset(BaseModel):
    dataset_id: str
    missions: List[Mission] = []

# --- OSDR Client ---

class OSDRClient:
    """
    Client to connect to the NASA OSDR API and fetch datasets with strict validation.
    """
    def __init__(self, base_url: str = OSDR_API_BASE, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout

    def fetch_osdr_dataset(self, dataset_id: str, filters: Optional[Dict[str, Any]] = None) -> Optional[OSDRDataset]:
        """
        Fetch study data from OSDR by study ID and validate its structure.
        """
        url = f"{self.base_url}/studies/{dataset_id}/datasets"
        params = {
            "filters": filters or {},
            "format": "json"
        }
        
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            raw_data = response.json()
            
            # Inject dataset_id into the response payload if missing for validation purposes
            if 'dataset_id' not in raw_data:
                raw_data['dataset_id'] = dataset_id

            # Validate structural integrity and type safety
            validated_data = OSDRDataset(**raw_data)
            logger.info(f"Successfully fetched and validated dataset {dataset_id}.")
            return validated_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching dataset {dataset_id}: {e}")
            # Graceful degradation: return None on network failure
            return None
        except ValidationError as e:
            logger.error(f"Data validation failed for dataset {dataset_id}. Schema mismatch:\n{e}")
            # Graceful degradation: return None on invalid structural integrity
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching dataset {dataset_id}: {e}")
            return None

    def extract_baseline_cohort(self, osdr_data: OSDRDataset, mission_type: str = "ISS") -> List[Dict[str, Any]]:
        """
        From OSDR data, extract pre-flight and in-flight measurements
        for astronauts on similar missions.
        """
        cohort = []
        if not osdr_data or not osdr_data.missions:
            logger.warning("Empty OSDR data provided to extract_baseline_cohort.")
            return cohort

        for mission in osdr_data.missions:
            if mission.type == mission_type:
                cohort.append({
                    'astronaut_id': mission.subject_id,
                    'mission_duration_days': mission.duration,
                    'preflights': mission.preflights.model_dump(by_alias=True, exclude_none=True) if mission.preflights else {},
                    'inflight': mission.inflight_timeseries.model_dump(by_alias=True, exclude_none=True) if mission.inflight_timeseries else {},
                    'postflights': mission.postflights.model_dump(by_alias=True, exclude_none=True) if mission.postflights else {},
                    'health_events': mission.health_events
                })
        return cohort

    def validate_deviation_thresholds(self, osdr_cohort: List[Dict[str, Any]], deviation_algorithm: Any) -> Dict[str, Any]:
        """
        Retrospectively run deviation detection on OSDR timeseries.
        Compare flagged deviations to actual flight surgeon notes.
        """
        validation_results = {
            'sensitivity': 0.0,
            'specificity': 0.0,
            'false_positive_rate': 0.0,
            'recommended_z_score_thresholds': {}
        }
        
        if not osdr_cohort:
            logger.warning("Empty cohort provided for validation.")
            return validation_results
        
        for mission in osdr_cohort:
            inflight_series = mission.get('inflight', {})
            try:
                # Stub: execution of deviation detection algorithm
                anomaly_flags = deviation_algorithm.run(inflight_series)
            except Exception as e:
                logger.error(f"Error running deviation algorithm on mission for {mission.get('astronaut_id')}: {e}")
                continue
                
            actual_health_events = mission.get('health_events', [])
            
            # TODO: Implementation of evaluation metrics computing confusion matrix
            pass
            
        return validation_results
