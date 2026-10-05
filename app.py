import streamlit as st
import pandas as pd
from mission_orchestrator import run_30_day_mission

st.set_page_config(page_title="Astronaut Health Dashboard", layout="wide")

st.title("👨‍🚀 Astronaut Health Monitoring Dashboard")
st.markdown("NASA OSDR Real Dataset Integration (OSD-379 mapped to telemetry)")

def get_data():
    return run_30_day_mission()

data = get_data()

if data is None:
    st.error("Failed to fetch or process data from OSDR API. Please check your network connection.")
else:
    st.header(f"Subject: {data['astronaut_id']}")
    st.subheader(f"Earth Baseline Resting HR: {data['earth_hr_median']:.1f} bpm")
    
    results = data['daily_results']
    df = pd.DataFrame(results)
    
    # Telemetry Chart
    st.write("### Telemetry: Heart Rate vs Expected Baseline")
    
    # Rename columns for better legend display in Streamlit
    chart_data = df[['day', 'hr_val', 'expected_hr']].rename(
        columns={'hr_val': 'Actual HR', 'expected_hr': 'Expected HR'}
    ).set_index('day')
    
    st.line_chart(chart_data)
    
    st.info("💡 **Note:** Adapted Baseline shifts after Day 14 as the system learns the mission-phase expected range.")
    
    # Health Reports
    st.write("### Flight Surgeon Health Reports")
    
    for row in results:
        status = row['status']
        if status == "NOMINAL":
            color = "green"
            icon = "✅"
        elif status == "NOMINAL_WITH_CAUTION":
            color = "orange"
            icon = "⚠️"
        else:
            color = "red"
            icon = "🚨"
            
        with st.expander(f"{icon} Day {row['day']} - Status: {status}"):
            st.markdown(f"**Heart Rate:** {row['hr_val']:.1f} bpm (Expected: {row['expected_hr']:.1f} bpm)")
            st.markdown(f"**Summary:** {row['summary']}")
            st.markdown(f"**Recommended Action:** <span style='color:{color}; font-weight:bold;'>{row['action']}</span>", unsafe_allow_html=True)
