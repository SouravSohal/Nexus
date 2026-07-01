from abc import ABC, abstractmethod
from typing import List, Dict, Any
from backend.app.domain.models.event import RiskEvent
from backend.app.domain.models.decision import MitigationOption, DoNothingImpact

class AIClient(ABC):
    """
    AIClient is the port defining natural language processing capabilities.
    It isolates the core application from specific LLM models or API clients (Gemini, Vertex AI).
    """

    @abstractmethod
    def extract_risk_event_from_text(self, news_text: str, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Uses an LLM to parse unstructured text, returning a structured dictionary
        matching the RiskEvent schema, matching locations to the list of known nodes.
        """
        pass

    @abstractmethod
    def generate_executive_recommendation(
        self,
        event: RiskEvent,
        do_nothing_impact: DoNothingImpact,
        options: List[MitigationOption]
    ) -> str:
        """
        Synthesizes the mathematical ranking of mitigation options and generates
        a clear, executive narrative explaining the trade-offs.
        """
        pass
