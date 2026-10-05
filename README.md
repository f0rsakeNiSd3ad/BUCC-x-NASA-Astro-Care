# BUCC x NASA: Astro Care

**Astro Care** is a prototype automated astronaut health monitoring pipeline developed for Phase 1 and Phase 2 simulations. The project focuses on robust telemetry processing, dynamic baseline adaptation in spaceflight environments, and non-diagnostic narrative health summarization for Flight Surgeons. 

## Project Overview

This system was collaboratively built to demonstrate a modular, fault-tolerant approach to astronaut health monitoring, integrating real open-source NASA data and handling edge-case scenarios gracefully.

### Key Components Built:

1. **Baseline Calculator (`baseline_calculator.py`)**
   - **Earth Baseline:** Establishes initial resting medians for vital signs (HR, BP, SpO2) using pre-flight data.
   - **Mission Adaptation Baseline:** Recognizes that human physiology shifts in microgravity. Calculates a rolling 14-day adaptation baseline to adjust expected telemetry ranges dynamically during the mission.
   - *Tested for mathematical determinism and edge-case handling.*

2. **Health Summarizer (`health_summarizer.py`)**
   - Evaluates physiological deviations (using z-scores) against the adapted baseline.
   - Maps deviations to severity levels (`NOMINAL`, `NOMINAL_WITH_CAUTION`, `RED`).
   - Strictly enforces **no-diagnostic rules**: The summarizer provides operational context and actionable recommendations (e.g., "Schedule FSE Consult", "Reduce workload") without making unapproved medical diagnoses.

3. **OSDR Integrator (`osdr_client.py`)**
   - Interfaces directly with the **NASA Open Science Data Repository (OSDR)** API.
   - Fetches real dataset metadata (Target: **OSD-379**) and dynamically maps biological sample identifiers into simulated astronaut profiles.
   - Validates incoming data pipelines strictly using `Pydantic` schemas (`VitalSigns`, `Mission`, `TimeseriesData`).
   - Includes an **Offline Fallback Protocol**: If the live OSDR API times out or is network-blocked, the client falls back to a locally generated mock cohort ensuring the dashboard remains operational.

4. **Mission Orchestrator (`mission_orchestrator.py`)**
   - The central nervous system uniting all modules.
   - Simulates a complete 30-day ISS mission.
   - **Fault-Tolerance Testing:** We injected a rigorous failure scenario to test the pipeline's resilience. The orchestrator simulates a complete 48-hour telemetry network dropout (Days 16-17) followed by corrupted/malformed data packets (Day 18). The pipeline catches `TypeErrors` and degrades gracefully, passing missing data safely to the UI and tagging data completeness at `0.0%` for those days, preventing catastrophic system crashes.

5. **Visual Dashboard (`app.py`)**
   - An interactive web application built with **Streamlit**.
   - Features real-time line charts mapping Actual Heart Rate against the dynamically shifting Expected Baseline.
   - Presents daily Flight Surgeon Health Reports in a clean, color-coded, expandable UI layout.

## Setup and Installation

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install streamlit
   ```

2. **Run the Dashboard:**
   ```bash
   python -m streamlit run app.py
   ```
   Navigate to `http://localhost:8501` to view the live simulation.

3. **Run Unit Tests:**
   ```bash
   pytest
   ```

## Design Philosophy

- **Graceful Degradation:** The pipeline must survive real-world spaceflight communication blackouts.
- **Strict Data Contracts:** Pydantic models ensure that no malformed data reaches the calculator modules.
- **Actionable, Not Diagnostic:** Information is delivered to support medical officers, not replace them.
