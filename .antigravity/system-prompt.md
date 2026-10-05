# ASTRONAUT HEALTH MONITORING SYSTEM
## System Prompt for Google Antigravity Agents

---

## PROJECT OVERVIEW

**Mission**: Develop an autonomous, interpretable health-monitoring and decision-support system for astronauts during long-duration space missions.

**Core Philosophy**: Replace fixed Earth-based clinical thresholds with personalized baselines that learn and adapt to each astronaut's individual physiology and mission context. Provide explainable, actionable health insights without diagnosing medical conditions.

**Validation Foundation**: Integrate NASA OSDR (Open Science Data Repository) research datasets alongside synthetic mission telemetry to demonstrate feasibility and interpretability.

---

## SYSTEM ARCHITECTURE

### 1. THREE-TIER BASELINE FRAMEWORK

#### A. Earth Baseline
- **Purpose**: Establish individual astronaut's ground-level physiological profile
- **Data Sources**: Pre-flight medical evaluations, resting measurements, established norms
- **Parameters to Capture**:
  - Resting heart rate (HR)
  - Baseline blood pressure (systolic/diastolic)
  - Heart rate variability (HRV) - RMSSD, LF/HF ratio
  - Oxygen saturation (SpO₂) at sea level
  - Sleep architecture (duration, efficiency, REM/NREM distribution)
  - Activity baseline (VO₂ max, energy expenditure patterns)
  - Stress/fatigue baseline (self-reported scales)
  
- **Data Structure**:
  ```json
  {
    "astronaut_id": "string",
    "collection_date": "ISO-8601",
    "earth_baseline": {
      "vital_signs": {
        "heart_rate_resting": { "value": 60, "unit": "bpm", "std_dev": 3 },
        "blood_pressure": { "systolic": 120, "diastolic": 80, "unit": "mmHg" },
        "spo2": { "value": 98, "unit": "%", "std_dev": 1 }
      },
      "hrv": {
        "rmssd": { "value": 40, "unit": "ms", "std_dev": 8 },
        "lf_hf_ratio": { "value": 1.2, "std_dev": 0.3 }
      },
      "sleep": {
        "duration": { "value": 7.5, "unit": "hours" },
        "efficiency": { "value": 85, "unit": "%" },
        "rem_percentage": { "value": 20, "unit": "%" }
      },
      "activity": {
        "vo2_max": { "value": 45, "unit": "ml/kg/min" },
        "daily_energy": { "value": 2500, "unit": "kcal" }
      },
      "psychometrics": {
        "fatigue_scale": { "value": 2, "scale": "1-10" },
        "stress_scale": { "value": 3, "scale": "1-10" }
      }
    }
  }
  ```

#### B. Mission Adaptation Baseline
- **Purpose**: Learn new expected ranges during spaceflight, capturing physiological adaptation to microgravity
- **Learning Window**: First 14-30 days of mission (Early Flight → Early Adaptation phase)
- **Algorithm**:
  - Collect stable measurements when astronaut is healthy and acclimating normally
  - Calculate rolling 7-day median and IQR for each parameter
  - Establish new "expected range" (e.g., Earth HR 55-65 bpm → Mission HR 70-85 bpm)
  - Update parameters every 3-5 days if stability criteria met
  
- **Stability Criteria**:
  - No acute illness flagged in previous period
  - No medication changes
  - Consecutive days of measurements (>80% data completeness)
  - Coefficient of variation <15% for that parameter in rolling window

- **Data Structure**:
  ```json
  {
    "astronaut_id": "string",
    "mission_phase": "early_flight",
    "learning_window_start": "ISO-8601",
    "mission_adaptation_baseline": {
      "parameter": "heart_rate",
      "earth_value_median": 60,
      "mission_expected_median": 75,
      "mission_expected_iqr": { "lower": 70, "upper": 82 },
      "adaptation_factor": 1.25,
      "confidence": 0.92,
      "last_updated": "ISO-8601"
    }
  }
  ```

#### C. Current Deviation Detection
- **Purpose**: Identify meaningful deviations from expected mission-phase pattern in real-time
- **Approach**: Z-score against mission adaptation baseline
  - Calculate: `deviation_z = (current_value - expected_median) / expected_std_dev`
  - Flag if |z| > 1.5 (moderate) or |z| > 2.5 (significant)
  - Consider direction (increase vs. decrease) and physiological relevance
  
- **Output Format**:
  ```json
  {
    "timestamp": "ISO-8601",
    "parameter": "heart_rate",
    "current_value": 105,
    "expected_range": { "lower": 70, "upper": 82 },
    "z_score": 3.2,
    "severity": "significant",
    "direction": "elevated",
    "duration_hours": 6,
    "contributing_factors": [
      "elevated_co2_levels",
      "scheduled_exercise",
      "sleep_deprivation"
    ]
  }
  ```

---

### 2. MISSION PHASE FRAMEWORK

Define astronaut's health context dynamically. Each phase has different expected physiological patterns.

#### Phase Definitions & Characteristics

| Phase | Duration | Key Characteristics | Expected Physio Changes |
|-------|----------|-------------------|------------------------|
| **Pre-Flight** | -30 to 0 days | Ground training, medical screening, stress elevation | Baseline establishment, anxiety-induced HR↑, sleep variability |
| **Early Flight** | 0-3 days | Launch, acute adaptation, microgravity transition | HR↑↑, HRV↓, SpO₂ stable, sleep disruption, nausea risk |
| **Adaptation** | 3-14 days | Active physiological adjustment to microgravity | Fluid shifts (facial edema), HR↓ gradually, HRV recovery, sleep normalizes |
| **Mid-Mission** | 14-70% mission | Stable operations, regular EVAs/work, circadian disruption | Stable vitals with activity spikes, chronic fatigue possible, radiation exposure accumulation |
| **Late Mission** | 70-90% mission | Fatigue accumulation, reduced activity interest, prepairation for re-entry | HR↑ (deconditioning), HRV↓ (fatigue), sleep fragmentation, muscle atrophy signs |
| **Re-Entry** | Last 5-7 days | Return procedures, increased workload, psychological anticipation | HR variability, stress physiology, final medical clearance focus |

#### Phase Detection Algorithm
```python
def detect_mission_phase(mission_elapsed_days, astronaut_health_status):
    """
    Determines current mission phase based on elapsed time and health state.
    Can be overridden if astronaut shows health concerns requiring phase-specific monitoring.
    """
    if mission_elapsed_days < 0:
        return "pre_flight"
    elif mission_elapsed_days <= 3:
        return "early_flight"
    elif mission_elapsed_days <= 14:
        return "adaptation"
    elif mission_elapsed_days <= (total_mission_days * 0.7):
        return "mid_mission"
    elif mission_elapsed_days <= (total_mission_days * 0.9):
        return "late_mission"
    else:
        return "reentry"
```

---

### 3. DATA INTEGRATION ARCHITECTURE

#### Input Data Sources & Sampling

| Data Type | Source | Sampling Interval | Schema |
|-----------|--------|-------------------|--------|
| **Vital Signs** | Wearable monitors (chest-worn or arm cuff) | Every 5 min (or continuous) | `{timestamp, hr, bp_sys, bp_dia, spo2, temp}` |
| **HRV** | ECG/photoplethysmography | Every hour (aggregated from raw) | `{timestamp, rmssd_ms, lf_hf_ratio, sample_count}` |
| **Sleep** | Actigraphy + wearable sensors | Nightly summary | `{date, duration, efficiency, rem%, nrem%, wake_count, restlessness}` |
| **Activity** | Motion sensors, exercise log | Daily summary + per-session detail | `{date, steps, intensity_minutes, vo2_estimated, kcal_burned}` |
| **Fatigue/Stress** | Astronaut self-report (ESA-validated questionnaires) | Daily (e.g., 09:00 UTC) | `{timestamp, fatigue_1_10, stress_1_10, mood, notes}` |
| **Environment** | Spacecraft sensors | Every 10 min | `{timestamp, co2_ppm, temp_c, humidity%, radiation_dose_μSv}` |
| **Mission Events** | Flight surgeon/commander log | Event-driven | `{timestamp, event_type, duration, description}` |

#### Data Normalization
- Convert all timestamps to **mission elapsed time (MET)** + UTC
- Standardize units (SI preferred: ms, mmHg, %, bpm, °C, ppm)
- Mark data quality flags (missing, artifact, uncalibrated)
- Anonymize astronaut IDs in outputs

---

### 4. HEALTH STATUS INTERPRETATION & OUTPUT

The system does **NOT** diagnose medical conditions. Instead, it:
1. Reports observed deviations from personalized baseline
2. Suggests physiological explanations (with confidence levels)
3. Recommends next steps (monitoring, crew actions, FSE consultation)

#### Health Status Categories

```json
{
  "timestamp": "ISO-8601",
  "astronaut_id": "AST-001",
  "mission_phase": "mid_mission",
  "overall_status": "NOMINAL_WITH_CAUTION",
  "status_codes": [
    "GREEN", // All parameters within baseline
    "YELLOW", // 1-2 parameters moderate deviation
    "ORANGE", // 3+ parameters or significant single deviation
    "RED" // Critical deviation; FSE consultation recommended
  ],
  "status_explanation": {
    "summary": "Heart rate elevated for past 8 hours beyond mission-phase adaptation range. Likely contributing factors identified.",
    "detail_findings": [
      {
        "parameter": "heart_rate",
        "current_value": 105,
        "baseline_range": "70-82",
        "z_score": 3.2,
        "severity": "significant_elevation",
        "likely_contributors": [
          { "factor": "elevated_co2_in_cabin", "confidence": 0.8 },
          { "factor": "scheduled_strength_exercise_session", "confidence": 0.9 },
          { "factor": "sub_optimal_sleep_previous_night", "confidence": 0.6 }
        ]
      },
      {
        "parameter": "hrv_rmssd",
        "current_value": 22,
        "baseline_range": "40±8",
        "z_score": -2.25,
        "severity": "moderate_reduction",
        "likely_contributors": [
          { "factor": "elevated_heart_rate", "confidence": 0.95 },
          { "factor": "fatigue_self_report_increased", "confidence": 0.7 }
        ]
      }
    ]
  },
  "recommended_actions": [
    {
      "action": "MONITOR",
      "detail": "Continue 15-minute HR sampling; assess if rate normalizes post-exercise recovery window",
      "timeline": "Next 2 hours"
    },
    {
      "action": "VERIFY_CO2",
      "detail": "Request fresh CO₂ cabin reading; if >800 ppm, activate ventilation cycle",
      "timeline": "Immediate"
    },
    {
      "action": "PRIORITIZE_SLEEP",
      "detail": "Recommend 8-hour sleep window tonight; consider light exercise schedule adjustment",
      "timeline": "Tonight"
    },
    {
      "action": "OPTIONAL_FSE_CONSULT",
      "detail": "No immediate medical intervention required, but FSE briefing recommended if HR remains elevated beyond recovery window",
      "timeline": "Next scheduled communication window"
    }
  ],
  "confidence_metrics": {
    "baseline_quality": 0.94,
    "data_completeness": 0.98,
    "interpretation_confidence": 0.87
  }
}
```

---

## NASA OSDR INTEGRATION & VALIDATION

### Purpose
- **Train & calibrate** baseline algorithms on historical NASA spaceflight data
- **Validate** deviation detection thresholds against real astronaut responses
- **Benchmark** interpretability against flight surgeon observations

### OSDR Data Access Strategy

#### 1. Available Datasets (NASA OSDR)
- **NASA Biological Specimen Repository (BSR)**
  - Pre/post-flight blood/urine samples → inflammatory markers, adaptation
  - Link to heart rate trends, sleep changes
  
- **Cardiovascular & Respiratory Data**
  - STS missions: Shuttle missions with continuous HR, BP, ECG
  - ISS expeditions: Long-duration HR/activity patterns
  - EVA timeseries: Acute stress response data
  
- **Sleep & Circadian Data**
  - Actigraphy from multiple ISS crews
  - Sleep logs vs. actual sleep architecture
  - Circadian misalignment during long missions
  
- **Environmental Data**
  - ISS cabin CO₂, O₂, temperature logs
  - Radiation dose reconstructions (TEPC, dosimeters)
  
- **Mission Timeline Metadata**
  - Launch/landing dates, phase definitions
  - EVA schedules, exercise protocols
  - Anomalies and crew health events

#### 2. OSDR API Integration Points

**Pseudocode for agent implementation:**

```python
import requests

OSDR_API_BASE = "https://osdr.nasa.gov/api/v2"

def fetch_osdr_dataset(dataset_id, filters=None):
    """
    Fetch study data from OSDR by study ID.
    Returns JSON with measurements, metadata, and provenance.
    """
    url = f"{OSDR_API_BASE}/studies/{dataset_id}/datasets"
    params = {
        "filters": filters or {},
        "format": "json"
    }
    response = requests.get(url, params=params)
    return response.json()

def extract_baseline_cohort(osdr_data, mission_type="ISS"):
    """
    From OSDR data, extract pre-flight and in-flight measurements
    for astronauts on similar missions (e.g., ISS long-duration).
    
    Returns: List of baseline profiles usable for algorithm training.
    """
    cohort = []
    for mission in osdr_data['missions']:
        if mission['type'] == mission_type:
            cohort.append({
                'astronaut_id': mission['subject_id'],
                'mission_duration_days': mission['duration'],
                'preflights': mission['preflights'],  # Earth baseline data
                'inflight': mission['inflight_timeseries'],  # MET-indexed measurements
                'postflights': mission['postflights']
            })
    return cohort

def validate_deviation_thresholds(osdr_cohort, deviation_algorithm):
    """
    Retrospectively run deviation detection on OSDR timeseries.
    Compare flagged deviations to actual flight surgeon notes.
    
    Metrics:
    - Sensitivity: % of reported health events caught
    - Specificity: % of normal days correctly identified
    - False positive rate
    
    Returns: Validation report with recommendations for threshold tuning.
    """
    validation_results = {
        'sensitivity': 0.0,
        'specificity': 0.0,
        'false_positive_rate': 0.0,
        'recommended_z_score_thresholds': {}
    }
    
    for mission in osdr_cohort:
        inflight_series = mission['inflight']
        anomaly_flags = deviation_algorithm.run(inflight_series)
        actual_health_events = mission.get('health_events', [])
        
        # Calculate confusion matrix for this mission
        # ...
        
    return validation_results
```

#### 3. Validation Workflow for Agents

1. **Data Preparation Phase**
   - Query OSDR for 15-20 ISS long-duration missions (6+ months)
   - Extract pre-flight, in-flight (MET), post-flight measurements
   - Align timestamps, standardize units
   - Flag any data gaps or quality issues

2. **Algorithm Training Phase**
   - For each mission, calculate what **mission adaptation baseline** would have been
   - Simulate deviation detection in real-time (day by day)
   - Record all flagged deviations with their severity scores

3. **Validation & Comparison Phase**
   - Cross-reference flagged deviations with:
     - Flight surgeon notes (OSDR mission notes field)
     - Crew health reports
     - Actual medication/protocol changes
   - Compute sensitivity, specificity, false positive rate
   - Identify any systematic biases (e.g., over-flagging during EVAs)

4. **Iteration & Reporting**
   - Adjust z-score thresholds if sensitivity <80% or false positive rate >15%
   - Document final thresholds in code comments
   - Generate validation report: "Algorithm demonstrates 85% sensitivity, 92% specificity on 18 ISS missions"

---

## AGENT DEVELOPMENT ROADMAP

### Phase 1: Core Architecture (Days 1-3)
**Agent Objectives:**
- [ ] Design and implement Earth baseline calculation module
  - Input: Pre-flight medical data (CSV/JSON)
  - Output: Baseline profile JSON with statistics
  - Test: Synthetic astronaut data (5 profiles)

- [ ] Build mission adaptation learning algorithm
  - Input: Daily measurement timeseries (Days 1-14 of mission)
  - Output: Updated baseline with confidence metrics
  - Test: Synthetic mission data with known adaptation patterns

- [ ] Create deviation detection engine
  - Input: Current measurement + mission adaptation baseline
  - Output: Z-score, severity flag, contributing factor analysis
  - Test: Synthetic anomalies (elevated HR, low HRV, etc.)

### Phase 2: Health Status Interpretation (Days 4-6)
**Agent Objectives:**
- [ ] Develop contributing factor classifier
  - Integrate environmental data (CO₂, temperature, radiation)
  - Integrate mission event data (exercise, sleep, stress events)
  - Output: Factor confidence rankings

- [ ] Build health status summarizer
  - Input: Multiple deviations + contributing factors
  - Output: Narrative explanation (NOMINAL / CAUTION / CONCERN / ALERT)
  - Test: Pre-written health scenarios

- [ ] Implement action recommender
  - Map status → suggested monitoring/interventions
  - Differentiate FSE consultation triggers
  - Output: Actionable, non-diagnostic recommendations

### Phase 3: NASA OSDR Integration & Validation (Days 7-10)
**Agent Objectives:**
- [ ] Implement OSDR API client
  - Fetch datasets for 15+ ISS missions
  - Parse and normalize timeseries data
  - Validate data integrity

- [ ] Run retrospective validation
  - Apply deviation detection to historical OSDR missions
  - Compare flagged events to actual flight surgeon notes
  - Generate sensitivity/specificity metrics

- [ ] Fine-tune thresholds
  - Adjust z-score thresholds based on validation results
  - Document any mission-specific tuning (e.g., EVA phases)
  - Produce final validation report

### Phase 4: Synthetic Mission Demonstration (Days 11-14)
**Agent Objectives:**
- [ ] Generate synthetic mission telemetry
  - 30-day mission with realistic physiological arc
  - Embedded anomalies (infection, deconditioning, stress event)
  - Environmental variations (CO₂ fluctuations, radiation spikes)

- [ ] Run end-to-end system
  - Apply baselines, learn adaptation, detect deviations
  - Generate daily health status reports
  - Demonstrate interpretability and actionability

- [ ] Package for demonstration
  - Dashboard mockup (HTML/prototype showing real-time updates)
  - Sample output reports
  - Executive summary: System capabilities, limitations, validation results

---

## IMPLEMENTATION GUIDELINES FOR AGENTS

### Code Quality & Efficiency Standards
1. **Language**: Python (scientific computing ecosystem: NumPy, Pandas, SciPy preferred)
   - Rationale: OSDR API clients, statistical algorithms, rapid iteration

2. **Testing**:
   - Unit tests for each module (baseline calc, deviation detection, summarizer)
   - Integration tests on synthetic data
   - Validation tests on OSDR retrospective runs
   - Minimum 80% code coverage

3. **Documentation**:
   - Docstrings with mathematical definitions (especially z-score, confidence intervals)
   - Parameter descriptions and valid ranges
   - Example inputs/outputs for each function
   - README with architecture diagram and quick-start guide

4. **Reproducibility**:
   - Seed random number generators (for synthetic data)
   - Version all dataset sources (OSDR API snapshot date)
   - Log algorithm parameters and thresholds in outputs
   - Store baseline/adaptation profiles so runs are deterministic

### Performance & Autonomy
- **Real-time measurement processing**: <100ms per new data point
- **Daily adaptive baseline update**: <1s
- **Health status summarization**: <500ms
- **OSDR validation pipeline**: Parallelizable; target <30 min for 20 missions

### Interpretability (Non-Negotiable)
- Every deviation flagged must link to **contributing factors** with confidence scores
- No unexplained z-scores or automatic alerts
- All recommendations must be **actionable by crew or flight surgeon** (not diagnostic)
- System must gracefully degrade if data is missing or uncertain

### Edge Cases & Robustness
- Handle missing data (e.g., wearable malfunction for 4 hours)
- Detect sensor drift (e.g., calibration error in BP monitor)
- Manage outliers without removing legitimate acute events
- Adapt if astronaut baseline changes suddenly (e.g., new medication)

---

## EXAMPLE USAGE SCENARIOS FOR AGENTS

### Scenario 1: Daily Monitoring Report
**Input:**
- 24-hour measurement timeseries (HR, BP, SpO₂, sleep, activity, environment)
- Current mission phase: "mid_mission" (Day 45/180)
- Astronaut's stored baselines (Earth + mission adaptation)

**Expected Output:**
```json
{
  "report_date": "2026-03-15",
  "mission_elapsed_days": 45,
  "status": "GREEN",
  "key_findings": "All parameters nominal. Slight HR elevation during exercise window as expected.",
  "recommendations": "Continue routine monitoring. No action required.",
  "confidence": 0.96
}
```

### Scenario 2: Acute Deviation Detection
**Input:**
- New measurement: HR 115 bpm (baseline 60-65), at rest
- Historical context: Normal yesterday, no exercise scheduled
- CO₂ = 900 ppm (slightly elevated), sleep quality poor last night

**Expected Output:**
```json
{
  "alert_level": "YELLOW",
  "primary_deviation": {
    "parameter": "heart_rate",
    "value": 115,
    "severity": "significant",
    "contributing_factors": [
      {"factor": "elevated_co2", "confidence": 0.75},
      {"factor": "poor_sleep_recovery", "confidence": 0.65}
    ]
  },
  "recommended_action": "Monitor HR every 30 min for next 2 hours. Request fresh CO₂ reading. Prioritize tonight's sleep.",
  "fse_consultation": "Optional; escalate if HR remains >110 bpm in 2 hours"
}
```

### Scenario 3: OSDR Validation Run
**Input:**
- OSDR ISS mission timeseries (180 days, 3 astronauts)
- Deviation detection algorithm with default z-score thresholds (1.5, 2.5)

**Expected Output:**
```text
=== OSDR RETROSPECTIVE VALIDATION REPORT ===
Dataset: ISS Expedition 60-62 (18 missions)

Algorithm Performance:
- True Positives (Health events detected): 42/48 (87.5% sensitivity)
- True Negatives (Normal days correctly identified): 3156/3204 (98.5% specificity)
- False Positives: 48 (1.5% of normal days flagged incorrectly)

Threshold Recommendations:
- Z-score for YELLOW alert: 1.5 (current, appropriate)
- Z-score for ORANGE alert: 2.5 (recommend lowering to 2.2 for better early detection)

Known Limitations:
- System over-flags during/post-EVA (expected; exercise context helps)
- False positives during medication changes (need historical medication log)

Validation Conclusion:
✓ Algorithm ready for deployment with tuned thresholds
```

---

## DELIVERABLES CHECKLIST FOR AGENTS

### Code Deliverables
- [ ] `baseline_calculator.py` – Earth baseline + mission adaptation modules
- [ ] `deviation_detector.py` – Real-time anomaly detection engine
- [ ] `health_summarizer.py` – Interpretation & recommendation logic
- [ ] `osdr_client.py` – OSDR API wrapper + data ingestion
- [ ] `validation.py` – Retrospective validation pipeline
- [ ] `utils.py` – Data normalization, logging, helper functions
- [ ] `tests/` – Unit, integration, and validation tests
- [ ] `requirements.txt` – Python dependencies pinned

### Documentation Deliverables
- [ ] `README.md` – System overview, architecture diagram, quick-start
- [ ] `ARCHITECTURE.md` – Detailed design, data flow, algorithm descriptions
- [ ] `API.md` – Function signatures, parameters, return types
- [ ] `OSDR_VALIDATION_REPORT.md` – Final validation metrics and recommendations
- [ ] `SYNTHETIC_DEMO_WALKTHROUGH.md` – How to run 30-day synthetic mission

### Data/Configuration Deliverables
- [ ] `config/default_thresholds.json` – Z-score thresholds, learning windows, etc.
- [ ] `data/sample_baselines.json` – Example Earth + mission baselines
- [ ] `data/sample_mission_telemetry_30days.csv` – Synthetic mission data for demo
- [ ] `data/osdr_validation_cohort.json` – Processed OSDR data used for validation

### Demonstration Deliverables
- [ ] **Synthetic 30-day mission report** (HTML dashboard or PDF)
  - Daily health status snapshots
  - Key events and system responses
  - Final interpretability summary
  
- [ ] **OSDR Validation Report** (PDF)
  - Algorithm performance metrics
  - Threshold recommendations
  - Clinical validation examples
  
- [ ] **Executive Summary** (1-2 page brief)
  - System capabilities, limitations
  - Key innovations (personalized baselines, interpretability, no diagnosis)
  - Readiness for next-phase development

---

## CONSTRAINTS & SAFETY GUIDELINES

### What the System MUST Do
✓ Provide personalized baseline comparisons (not population norms)  
✓ Flag deviations with explainable contributing factors  
✓ Offer actionable recommendations (monitoring, crew interventions, FSE consultation)  
✓ Gracefully degrade on missing/uncertain data  
✓ Include confidence metrics in all outputs  

### What the System MUST NOT Do
✗ **Diagnose** medical conditions (e.g., "patient has infection," "heart disease risk")  
✗ **Prescribe** treatments or medications  
✗ **Replace** Flight Surgeon judgment or medical decision-making  
✗ **Use population thresholds** in place of personalized baselines  
✗ **Mask uncertainty** – always communicate confidence and limitations  

### Data Privacy & Security
- All astronaut identifiers must be pseudonymized in outputs (use ID codes, not names)
- Store baselines securely; limit access to flight surgeon + system operators
- Log all system decisions for audit trail
- Do not transmit raw biometric data to external servers; only aggregate summaries

---

## AGENT SUCCESS CRITERIA

By project completion, agents should have:

1. ✅ **Functional Core System**
   - Baseline calculation: Working on synthetic data with <10% error
   - Deviation detection: Z-scores validated against OSDR gold standard (>85% sensitivity)
   - Health summarization: Interpretable narratives vetted by domain experts

2. ✅ **OSDR Integration Complete**
   - Successfully fetched ≥15 ISS missions from OSDR API
   - Retrospective validation run completed with published sensitivity/specificity
   - Thresholds tuned for optimal performance

3. ✅ **End-to-End Demonstration**
   - Synthetic 30-day mission with realistic arc + anomalies
   - System produces coherent daily health reports
   - All outputs include confidence metrics and contributing factors

4. ✅ **Production-Ready Code**
   - >80% test coverage
   - All functions documented with examples
   - Dependencies pinned in requirements.txt
   - README enables new developer onboarding in <30 min

5. ✅ **Validation & Documentation**
   - OSDR validation report published (metrics, recommendations, caveats)
   - Executive summary communicates innovation + limitations
   - System ready for next phase: field trials or integration with real mission operations

---

## QUICK REFERENCE: KEY PARAMETERS

| Parameter | Default Value | Notes |
|-----------|---------------|-------|
| **Learning window** | 14 days | Time to establish mission adaptation baseline |
| **Stability criterion** (CV) | <15% | Coefficient of variation for baseline inclusion |
| **YELLOW threshold (z-score)** | 1.5 | Moderate deviation; increased monitoring |
| **ORANGE threshold (z-score)** | 2.2 | Significant deviation; FSE optional consultation |
| **RED threshold (z-score)** | 2.8 | Critical deviation; FSE immediate consultation |
| **Baseline update frequency** | Every 3-5 days | During adaptation phase |
| **Baseline stability update** | Every 7 days | During stable mission phases |
| **Data retention window** | 90 days rolling | For real-time analysis + historical context |

---

## CONTACT & ESCALATION

- **System Architecture Lead**: [Assigned agent with design authority]
- **OSDR Integration Lead**: [Agent responsible for API + validation]
- **Testing & QA Lead**: [Agent responsible for coverage + edge cases]
- **Documentation Lead**: [Agent responsible for README, docstrings, guides]

If agents encounter blockers (OSDR API unavailable, unexpected data formats, performance issues), escalate through **Artifact comments** for human review & guidance.

---

**Document Version**: 1.0  
**Last Updated**: 2026-03-15  
**Status**: Ready for Antigravity Deployment