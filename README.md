# BUCC x NASA: Astro Care

Astro Care is a Phase 1 and Phase 2 prototype for automated astronaut health monitoring, integrating telemetry with the NASA OSDR dataset (OSD-379). It includes a robust data processing pipeline designed to handle extreme spaceflight environments, such as 48-hour data dropouts and corrupted telemetry points, without crashing.

## Features

- **Baseline Calculator**: Dynamically calculates Earth baselines and inflight mission adaptation baselines using a 14-day rolling window.
- **Health Summarizer**: Analyzes deviations to produce nominal, nominal-with-caution, and off-nominal mission statuses and actionable recommendations for flight surgeons, carefully avoiding unapproved medical diagnoses.
- **OSDR Integrator**: Seamlessly pulls real biological dataset metadata from NASA's Open Science Data Repository (OSD-379) and dynamically maps it to Pydantic-validated telemetry structures for simulated testing.
- **Mission Orchestrator**: The central nervous system uniting all modules, generating the telemetry loop, simulating drop-out scenarios (Days 16-17) and corrupted data (Day 18) gracefully.
- **Streamlit Dashboard**: A visual interface built with Streamlit providing real-time line charts of Heart Rate telemetry against Expected Baselines, accompanied by expandable Flight Surgeon summary reports.

## Installation & Setup

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   pip install streamlit
   ```

2. Run the interactive Streamlit dashboard:
   ```bash
   python -m streamlit run app.py
   ```
   Or run the headless pipeline:
   ```bash
   python mission_orchestrator.py
   ```
