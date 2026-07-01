import os
import json
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv
from backend.app.domain.interfaces.ai_client import AIClient
from backend.app.domain.models.event import RiskEvent
from backend.app.domain.models.decision import MitigationOption, DoNothingImpact

logger = logging.getLogger(__name__)

# Pydantic schema for Gemini structured output extraction
class GeminiExtractionSchema(BaseModel):
    title: str = Field(
        ..., 
        description="A short, professional title summarizing the disruption event (e.g. 'Port of Antwerp worker strike')."
    )
    description: str = Field(
        ..., 
        description="A concise summary of the event details, duration, and immediate impact."
    )
    location: str = Field(
        ..., 
        description="The geographic location where the event took place (e.g. 'Antwerp, Belgium')."
    )
    affected_node_id: str = Field(
        ..., 
        description="The ID of the digital twin node directly affected. MUST match one of the node IDs provided in the prompt."
    )
    severity: float = Field(
        ..., 
        description="Disruption severity fraction: 1.0 is total shutdown, 0.0 is zero impact. Value must be between 0.0 and 1.0."
    )
    duration_days: int = Field(
        ..., 
        description="Estimated duration of the disruption in days. If not mentioned, estimate a realistic duration. Must be an integer greater than 0."
    )
    confidence_score: float = Field(
        ..., 
        description="Your confidence score in the accuracy of this extraction. Value must be between 0.0 and 1.0."
    )

class GeminiClient(AIClient):
    """
    GeminiClient interfaces with the Google Gemini API.
    If the GEMINI_API_KEY environment variable is missing, it falls back
    gracefully to a high-fidelity local mock engine.
    """

    def __init__(self):
        # Load local .env secrets securely
        load_dotenv()
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.mock_active = not bool(self.api_key)
        
        if self.mock_active:
            logger.warning("GEMINI_API_KEY not found in environment. Running GeminiClient in MOCK mode.")
        else:
            logger.info("Initializing Google Gemini SDK.")
            genai.configure(api_key=self.api_key)

    def extract_risk_event_from_text(self, news_text: str, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extracts structured risk parameters from unstructured news text.
        """
        if self.mock_active:
            return self._mock_extraction(news_text, nodes)
            
        try:
            # Format nodes list to inform the LLM of valid matches
            nodes_context = "\n".join([
                f"- ID: '{n['id']}', Name: '{n['name']}', Type: '{n['type']}', Location: '{n['location']}'"
                for n in nodes
            ])
            
            prompt = f"""
            You are an advanced risk analyzer for the NEXUS Decision Intelligence Platform.
            Analyze the following unstructured news text and extract the core risk event details.
            
            You MUST map the event to one of our existing Digital Twin nodes listed below.
            Select the ID of the node most directly impacted.
            
            ### Known Digital Twin Nodes:
            {nodes_context}
            
            ### Unstructured News Article Content:
            "{news_text}"
            
            ### Extraction Instructions:
            1. Match location and context to select the single best matching node ID.
            2. Infer a severity score between 0.0 and 1.0 (e.g., partial closure = 0.5, complete halt = 1.0).
            3. Infer duration in days.
            """
            
            # Using Gemini supporting schema enforcement
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiExtractionSchema
                )
            )
            
            extracted_data = json.loads(response.text)
            logger.info(f"Gemini Extraction successful: {extracted_data}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Gemini Extraction failed: {str(e)}. Falling back to mock engine.")
            return self._mock_extraction(news_text, nodes)

    def generate_executive_recommendation(
        self,
        event: RiskEvent,
        do_nothing_impact: DoNothingImpact,
        options: List[MitigationOption]
    ) -> str:
        """
        Generates a professional markdown briefing detailing mitigation trade-offs.
        """
        if self.mock_active:
            return self._mock_recommendation(event, do_nothing_impact, options)
            
        try:
            # Format options list for the model
            options_context = ""
            for idx, opt in enumerate(options):
                rec_flag = "[RECOMMENDED]" if opt.is_recommended else ""
                options_context += f"""
                Option {idx+1}: {opt.title} {rec_flag}
                - Description: {opt.description}
                - Implementation Surcharge Cost: ${opt.cost_impact:,.2f}
                - Lead Time Surcharge: {opt.lead_time_surcharge_days} days
                - Operational Feasibility: {opt.feasibility_score * 100:.0f}%
                - Optimization Utility Score: {opt.calculated_score}
                """

            prompt = f"""
            You are the Chief Operations Officer and Lead Decision Architect for NEXUS.
            Write an executive decision briefing for the CEO regarding an active disruption event.
            
            ### Disruption Event Details:
            - Title: {event.title}
            - Target Impact: {event.affected_node_id} (Severity: {event.severity * 100:.0f}%, Duration: {event.duration_days} days)
            - Description: {event.description}
            
            ### Do Nothing Baseline Cost:
            - Earliest Downstream Stockout: Day {do_nothing_impact.earliest_stockout_day}
            - Total Financial Risk: ${do_nothing_impact.total_financial_loss:,.2f}
            - Delayed Product Vol: {do_nothing_impact.delayed_products_count} units
            
            ### Scored Mitigation Alternatives:
            {options_context}
            
            ### Formatting Guidelines:
            - Write in a professional, authoritative, and concise tone.
            - Start with a clear header.
            - Provide a quick summary of the risk and "do-nothing" impact.
            - Compare the mitigation options, highlighting cost vs time trade-offs.
            - Conclude with a strong, actionable sign-off recommending the top option.
            - Use clean Markdown styling. Keep it under 250 words.
            """
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini Briefing generation failed: {str(e)}. Falling back to mock briefing.")
            return self._mock_recommendation(event, do_nothing_impact, options)

    def _mock_extraction(self, news_text: str, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Mock extraction engine fallback. Matches keywords to return high-fidelity data.
        """
        text_lower = news_text.lower()
        
        # 1. Check for Antwerp strike
        if "antwerp" in text_lower or "strike" in text_lower:
            return {
                "title": "Port of Antwerp Dockworker Strike",
                "description": "A 5-day walkout by container terminal operators halts shipping and trucking operations.",
                "location": "Antwerp, Belgium",
                "affected_node_id": "port-antwerp",
                "severity": 0.85,
                "duration_days": 5,
                "confidence_score": 0.95
            }
        
        # 2. Check for Kaohsiung port issues
        elif "kaohsiung" in text_lower or "typhoon" in text_lower:
            return {
                "title": "Typhoon Disruption at Kaohsiung",
                "description": "Category 3 typhoon forces closure of container berths at the Port of Kaohsiung for 3 days.",
                "location": "Kaohsiung, Taiwan",
                "affected_node_id": "port-kaohsiung",
                "severity": 0.90,
                "duration_days": 3,
                "confidence_score": 0.92
            }
            
        # 3. Default fallback
        return {
            "title": "Unscheduled Logistics Disruption",
            "description": "General transport delays affecting international container processing channels.",
            "location": "Global",
            "affected_node_id": "port-antwerp",
            "severity": 0.50,
            "duration_days": 4,
            "confidence_score": 0.80
        }

    def _mock_recommendation(
        self,
        event: RiskEvent,
        do_nothing_impact: DoNothingImpact,
        options: List[MitigationOption]
    ) -> str:
        """
        Mock recommendation summary builder. Returns a beautiful executive markdown brief.
        """
        recommended_opt = next((o for o in options if o.is_recommended), options[0])
        
        return f"""### Executive Recommendation: Operational Rerouting Required

**Disruption Summary:** The active disruption at `{event.affected_node_id}` ({event.title}) blocks vital logistics pathways. 

**Do-Nothing Risk:** If no action is taken, downstream safety stocks deplete rapidly. Munich Logistics Hub will face a complete component stockout on **Day {do_nothing_impact.earliest_stockout_day}**, resulting in manufacturing downtime at the Munich Cognitive Assembly Plant. Cumulative financial risk is estimated at **${do_nothing_impact.total_financial_loss:,.2f}** with **{do_nothing_impact.delayed_products_count} units** of Nexus Autopilot ECUs delayed.

**Mitigation Analysis:**
- **{recommended_opt.title} (RECOMMENDED):** Rerouting container arrivals offers the highest utility score ({recommended_opt.calculated_score}). It incurs a minor surcharge of **${recommended_opt.cost_impact:,.2f}** and adds **{recommended_opt.lead_time_surcharge_days} day(s)** to lead times, but keeps assembly lines operational.
- **Air Freight Acceleration:** Bypasses ports entirely, but at a prohibitive cost of $220,000.00. Air freight slot feasibility is constrained (60%).
- **Domestic Sourcing Switch:** Switching to the European backup supplier has high feasibility (80%) but increases procurement overhead by $95,000.00.

**Decision Endorsement:** We recommend immediately implementing the **{recommended_opt.title}** playbook to maintain plant operations and avoid the $1.25M production shutdown penalty.
"""
