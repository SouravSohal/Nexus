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

def build_ask_context(question: str, system_state: Dict[str, Any]) -> str:
    """
    Constructs a textual state summary of the Digital Twin network
    (nodes, edges, metrics, active disruptions) as context for LLM answering.
    """
    nodes_summary = []
    for n in system_state.get("nodes", []):
        nodes_summary.append(
            f"- {n.get('name')} (ID: '{n.get('id')}'): Location: {n.get('location')}, "
            f"Health: {n.get('health', 1.0) * 100:.0f}%, "
            f"Inv: {n.get('inventory', 0.0):.0f}/{n.get('capacity', 100.0):.0f}"
        )

    edges_summary = []
    for e in system_state.get("edges", []):
        edges_summary.append(
            f"- {e.get('source')} -> {e.get('target')}: Mode: {e.get('transport_mode')}, "
            f"Dependency Ratio: {e.get('dependency_ratio', 1.0):.2f}"
        )

    metrics = system_state.get("metrics", {})
    active_event = system_state.get("active_event")
    if active_event:
        affected_nodes_list = active_event.get("affected_nodes", [])
        if affected_nodes_list:
            nodes_impacted_str = ", ".join([
                f"{an.get('node_id')} (Severity: {an.get('severity', 0.0)*100:.0f}%, Disruption: {an.get('disruption_type')})"
                for an in affected_nodes_list
            ])
            event_str = (
                f"Active Disruption: {active_event.get('title')} affecting multiple assets: {nodes_impacted_str} "
                f"for a duration of {active_event.get('duration_days', 0)} days."
            )
        else:
            event_str = (
                f"Active Disruption: {active_event.get('title')} at node '{active_event.get('affected_node_id')}' "
                f"(Severity: {active_event.get('severity', 0.0) * 100:.0f}%, Duration: {active_event.get('duration_days', 0)} days)"
            )
    else:
        event_str = "No active disruptions."

    context = f"""
    NEXUS is an AI Decision Intelligence Platform for Critical Infrastructure & Community Resilience.
    Here is the current state of our infrastructure network:
    
    ### Active Disruption State:
    {event_str}
    
    ### Global Resilience KPIs:
    - Overall System Resilience Score: {metrics.get('overall_resilience', 100.0):.1f}%
    - Projected Community/Financial Impact: ${metrics.get('total_financial_loss', 0.0):,.2f}
    
    ### Active Infrastructure Nodes State:
    {"\n".join(nodes_summary)}
    
    ### Active Connectivity Channels:
    {"\n".join(edges_summary)}
    """

    prompt = f"""
    {context}
    
    User Question: "{question}"
    
    Answer the user's operational question concisely based on the system state. Highlight key risks, at-risk facilities, or optimal mitigations using professional, executive-focused language. Keep it under 150 words.
    """
    return prompt


class GeminiProvider(AIClient):
    """
    GeminiProvider calls Google Gemini API.
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

    def ask_question(self, question: str, system_state: Dict[str, Any]) -> str:
        if not self.api_key:
            raise ValueError("Gemini API Key missing")
        prompt = build_ask_context(question, system_state)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text


class OllamaProvider(AIClient):
    """
    OllamaProvider calls a local Ollama Mistral model.
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
        
        You MUST map the event to one or more of our existing Digital Twin nodes listed below.
        Select the IDs of all nodes directly impacted.
        
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
            "affected_node_id": "The primary ID of the directly affected node",
            "severity": 0.0 to 1.0 (float),
            "duration_days": integer greater than 0,
            "confidence_score": 0.0 to 1.0 (float),
            "affected_nodes": [
                {{
                    "node_id": "The ID of the affected node, matching one of the IDs listed above",
                    "severity": 0.0 to 1.0 (float),
                    "confidence": 0.0 to 1.0 (float),
                    "disruption_type": "The type of disruption, e.g. shutdown"
                }}
            ]
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
                "affected_node_id": "The primary ID of the directly affected node",
                "severity": 0.0 to 1.0 (float),
                "duration_days": integer greater than 0,
                "confidence_score": 0.0 to 1.0 (float),
                "affected_nodes": [
                    {{
                        "node_id": "The ID of the affected node",
                        "severity": 0.0 to 1.0 (float),
                        "confidence": 0.0 to 1.0 (float),
                        "disruption_type": "disruption type string"
                    }}
                ]
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

    def ask_question(self, question: str, system_state: Dict[str, Any]) -> str:
        prompt = build_ask_context(question, system_state)
        return self._call_ollama(prompt)


class MockProvider(AIClient):
    """
    MockProvider reuses the high-fidelity keyword matching mock logic.
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

    def ask_question(self, question: str, system_state: Dict[str, Any]) -> str:
        q = question.lower()
        if "risk" in q or "facility" in q or "node" in q:
            return "Based on current telemetry, the Munich Logistics Hub is at highest risk. Safety stocks are projected to deplete to 0 by Day 6 due to the active port closure."
        elif "mitigation" in q or "recommend" in q:
            return "To minimize community impact, we recommend activating the Rotterdam Rerouting path immediately. This restores material flow and avoids the plant shutdown penalty."
        elif "what happens" in q or "duration" in q or "last" in q:
            return "An extended disruption will trigger a complete stockout at the Munich assembly factory, causing essential equipment manufacturing to halt by Day 10."
        else:
            return "NEXUS currently monitors 25 critical infrastructure nodes. The overall resilience is at 100% under baseline operations, but drops when Kaohsiung or Antwerp ports are blocked."
