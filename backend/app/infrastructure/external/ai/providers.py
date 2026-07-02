import os
import json
import logging
import google.generativeai as genai
import urllib.request
import urllib.error
from typing import List, Dict, Any
from backend.app.domain.interfaces.ai_client import AIClient
from backend.app.domain.models.event import RiskEvent
from backend.app.domain.models.decision import MitigationOption, DoNothingImpact
from backend.app.infrastructure.external.gemini_client import GeminiExtractionSchema, GeminiClient

logger = logging.getLogger(__name__)

class GeminiProvider(AIClient):
    """
    GeminiProvider calls Google Gemini API.
    Raises exceptions on failures so that the orchestrator can trigger failover.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def extract_risk_event_from_text(self, news_text: str, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("Gemini API Key missing")

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

        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=GeminiExtractionSchema
            )
        )

        extracted_data = json.loads(response.text)
        validated = GeminiExtractionSchema.model_validate(extracted_data)
        return validated.model_dump()

    def generate_executive_recommendation(
        self,
        event: RiskEvent,
        do_nothing_impact: DoNothingImpact,
        options: List[MitigationOption]
    ) -> str:
        if not self.api_key:
            raise ValueError("Gemini API Key missing")

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


class OllamaProvider(AIClient):
    """
    OllamaProvider calls a local Ollama Mistral model.
    Implements a single-attempt JSON repair loop if validation fails.
    """
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _call_ollama(self, prompt: str, format_type: str = None, timeout: int = 15) -> str:
        url = f"{self.base_url}/api/generate"
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if format_type:
            data["format"] = format_type

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data.get("response", "")

    def extract_risk_event_from_text(self, news_text: str, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        Your output MUST be a valid JSON object matching this schema precisely:
        {{
            "title": "A short, professional title summarizing the disruption event",
            "description": "A concise summary of the event details, duration, and immediate impact",
            "location": "The geographic location where the event took place",
            "affected_node_id": "The ID of the directly affected node, matching one of the IDs listed above",
            "severity": 0.0 to 1.0 (float),
            "duration_days": integer greater than 0,
            "confidence_score": 0.0 to 1.0 (float)
        }}
        
        Return ONLY raw JSON. Do not write any markdown blocks (like ```json), explanations, or notes.
        """

        response_text = self._call_ollama(prompt, format_type="json")

        try:
            extracted_data = json.loads(response_text)
            validated = GeminiExtractionSchema.model_validate(extracted_data)
            return validated.model_dump()
        except Exception as err:
            logger.warning(f"[Ollama] Initial validation failed: {str(err)}. Attempting JSON repair prompt...")
            
            repair_prompt = f"""
            You are an advanced JSON repair assistant.
            The following JSON output failed validation with error: {str(err)}
            
            ### Original Output:
            {response_text}
            
            ### Schema Requirements:
            {{
                "title": "A short, professional title summarizing the disruption event",
                "description": "A concise summary of the event details, duration, and immediate impact",
                "location": "The geographic location where the event took place",
                "affected_node_id": "The ID of the directly affected node",
                "severity": 0.0 to 1.0 (float),
                "duration_days": integer greater than 0,
                "confidence_score": 0.0 to 1.0 (float)
            }}
            
            Fix the errors and output ONLY the valid JSON object. Do not include markdown code blocks or explanations.
            """
            try:
                repaired_text = self._call_ollama(repair_prompt, format_type="json")
                extracted_data = json.loads(repaired_text)
                validated = GeminiExtractionSchema.model_validate(extracted_data)
                return validated.model_dump()
            except Exception as repair_err:
                logger.error(f"[Ollama] JSON repair failed: {str(repair_err)}")
                raise ValueError(f"Ollama output validation failed: {str(repair_err)}")

    def generate_executive_recommendation(
        self,
        event: RiskEvent,
        do_nothing_impact: DoNothingImpact,
        options: List[MitigationOption]
    ) -> str:
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
        return self._call_ollama(prompt)


class MockProvider(AIClient):
    """
    MockProvider reuses the high-fidelity keyword matching mock logic.
    Guarantees test suite execution without real API services.
    """
    def __init__(self):
        self.client = GeminiClient()

    def extract_risk_event_from_text(self, news_text: str, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self.client._mock_extraction(news_text, nodes)

    def generate_executive_recommendation(
        self,
        event: RiskEvent,
        do_nothing_impact: DoNothingImpact,
        options: List[MitigationOption]
    ) -> str:
        return self.client._mock_recommendation(event, do_nothing_impact, options)
