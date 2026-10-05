"""
health_summarizer.py

Implements Health Status Interpretation & Output module for astronaut health monitoring.
This system does NOT diagnose medical conditions. It flags deviations, provides
non-diagnostic narrative explanations, and recommends actionable interventions.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any

class HealthSummarizer:
    def __init__(self):
        # Thresholds derived from the system prompt guidelines
        self.thresholds = {
            "YELLOW": 1.5,
            "ORANGE": 2.2,
            "RED": 2.8
        }
        
    def determine_status_code(self, deviations: List[Dict[str, Any]]) -> str:
        """
        Calculates the appropriate status code (GREEN, YELLOW, ORANGE, RED)
        based on the maximum z-score and the number of deviations.
        """
        if not deviations:
            return "GREEN"
            
        max_abs_z = max([abs(d.get("z_score", 0.0)) for d in deviations])
        yellow_count = sum(1 for d in deviations if abs(d.get("z_score", 0.0)) >= self.thresholds["YELLOW"])
        
        if max_abs_z >= self.thresholds["RED"]:
            return "RED"
        elif max_abs_z >= self.thresholds["ORANGE"] or yellow_count >= 3:
            return "ORANGE"
        elif max_abs_z >= self.thresholds["YELLOW"]:
            return "YELLOW"
            
        return "GREEN"
        
    def generate_narrative_summary(self, status_code: str, deviations: List[Dict[str, Any]]) -> str:
        """
        Provides human-readable narrative explanations without diagnosing conditions.
        """
        if status_code == "GREEN":
            return "All parameters are nominal and within the mission-phase adaptation baseline."
            
        params = [d.get("parameter", "unknown_parameter").replace("_", " ") for d in deviations]
        params_str = ", ".join(params)
        
        if status_code == "YELLOW":
            return f"Moderate deviation detected in {params_str}. Likely environmental or behavioral contributing factors identified."
        elif status_code == "ORANGE":
            return f"Significant deviation detected in {params_str} beyond mission-phase adaptation range. Closer monitoring warranted."
        elif status_code == "RED":
            return f"Critical deviation detected in {params_str}. Immediate intervention and consultation recommended."
            
        return "Status undefined."

    def recommend_actions(self, status_code: str, deviations: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Generates actionable, non-diagnostic next steps.
        """
        actions = []
        if status_code == "GREEN":
            actions.append({
                "action": "MONITOR",
                "detail": "Continue routine 15-minute telemetry sampling.",
                "timeline": "Ongoing"
            })
            
        elif status_code == "YELLOW":
            actions.append({
                "action": "MONITOR",
                "detail": "Increase monitoring frequency. Assess if parameter normalizes within next 2 hours.",
                "timeline": "Next 2 hours"
            })
            actions.append({
                "action": "OPTIONAL_FSE_CONSULT",
                "detail": "No immediate medical intervention required, but mention in next FSE briefing.",
                "timeline": "Next scheduled communication window"
            })
            
        elif status_code == "ORANGE":
            actions.append({
                "action": "VERIFY_ENVIRONMENT",
                "detail": "Request fresh cabin environmental readings (CO2, temp) to rule out external factors.",
                "timeline": "Immediate"
            })
            actions.append({
                "action": "FSE_CONSULT",
                "detail": "FSE briefing recommended to review adaptation baseline.",
                "timeline": "Next available communication window"
            })
            
        elif status_code == "RED":
            actions.append({
                "action": "IMMEDIATE_FSE_CONSULT",
                "detail": "Immediate Flight Surgeon consultation required.",
                "timeline": "Immediate"
            })
            
        return actions

    def summarize(self, astronaut_id: str, mission_phase: str, deviations: List[Dict[str, Any]],
                  baseline_quality: float = 0.94, data_completeness: float = 0.98) -> Dict[str, Any]:
        """
        Constructs the final health status output matching the architecture payload specifications.
        """
        status_code = self.determine_status_code(deviations)
        
        overall_status_map = {
            "GREEN": "NOMINAL",
            "YELLOW": "NOMINAL_WITH_CAUTION",
            "ORANGE": "CONCERN",
            "RED": "ALERT"
        }
        
        summary_text = self.generate_narrative_summary(status_code, deviations)
        recommended_actions = self.recommend_actions(status_code, deviations)
        
        # Detail findings exactly pass through
        detail_findings = deviations 
        
        # Interpretation confidence modeled generically
        interpretation_confidence = 0.96 if not deviations else 0.87
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "astronaut_id": astronaut_id,
            "mission_phase": mission_phase,
            "overall_status": overall_status_map.get(status_code, "UNKNOWN"),
            "status_codes": [status_code],
            "status_explanation": {
                "summary": summary_text,
                "detail_findings": detail_findings
            },
            "recommended_actions": recommended_actions,
            "confidence_metrics": {
                "baseline_quality": baseline_quality,
                "data_completeness": data_completeness,
                "interpretation_confidence": interpretation_confidence
            }
        }
