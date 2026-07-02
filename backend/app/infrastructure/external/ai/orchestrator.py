import time
import logging
from typing import List, Dict, Any
from backend.app.core.config import settings
from backend.app.domain.interfaces.ai_client import AIClient
from backend.app.domain.models.event import RiskEvent
from backend.app.domain.models.decision import MitigationOption, DoNothingImpact
from backend.app.infrastructure.external.ai.providers import GeminiProvider, OllamaProvider, MockProvider

logger = logging.getLogger(__name__)

class AIOrchestrator(AIClient):
    """
    AIOrchestrator serves as the primary router implementing the AIClient port.
    It encapsulates Gemini and Ollama providers, managing dynamic provider status,
    measuring performance durations, and triggering automatic failovers.
    """
    def __init__(self):
        self.primary_name = settings.PRIMARY_AI_PROVIDER
        self.fallback_name = settings.FALLBACK_AI_PROVIDER

        self.gemini = GeminiProvider(settings.GEMINI_API_KEY)
        self.ollama = OllamaProvider(settings.OLLAMA_BASE_URL, settings.OLLAMA_MODEL)
        self.mock = MockProvider()

        # Track active provider status state dynamically
        self.active_status = "gemini"
        self._check_initial_status()

    def _check_initial_status(self):
        """
        Determines initial status by verifying API keys and checking if local Ollama REST port is open.
        """
        if not settings.GEMINI_API_KEY:
            try:
                import urllib.request
                req = urllib.request.Request(settings.OLLAMA_BASE_URL, method="GET")
                with urllib.request.urlopen(req, timeout=1.0):
                    self.active_status = "ollama"
            except Exception:
                self.active_status = "offline"
        else:
            self.active_status = "gemini"

    def get_provider_status(self) -> str:
        """Returns active AI engine provider state for UI status rendering."""
        return self.active_status

    def _get_provider(self, name: str) -> AIClient:
        if name == "gemini":
            return self.gemini
        elif name == "ollama":
            return self.ollama
        else:
            return self.mock

    def extract_risk_event_from_text(self, news_text: str, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        provider = self._get_provider(self.primary_name)
        start_time = time.perf_counter()

        try:
            res = provider.extract_risk_event_from_text(news_text, nodes)
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._log_and_print(self.primary_name, "Success", duration_ms)
            self.active_status = self.primary_name
            return res
        except Exception as e:
            err_type = self._classify_error(e)
            self._log_and_print(self.primary_name, err_type)

            # Fallback trigger
            self._log_switching(self.fallback_name)
            fallback_provider = self._get_provider(self.fallback_name)
            fallback_start = time.perf_counter()
            try:
                res = fallback_provider.extract_risk_event_from_text(news_text, nodes)
                duration_ms = (time.perf_counter() - fallback_start) * 1000
                self._log_and_print(self.fallback_name, "Success", duration_ms)
                self.active_status = self.fallback_name
                return res
            except Exception as fe:
                self._log_and_print(self.fallback_name, "Error")

                # Engages mock safety valve
                self.active_status = "offline"
                logger.warning("[AI] Fallback failed. Engaging Mock Provider safety valve...")
                return self.mock.extract_risk_event_from_text(news_text, nodes)

    def generate_executive_recommendation(
        self,
        event: RiskEvent,
        do_nothing_impact: DoNothingImpact,
        options: List[MitigationOption]
    ) -> str:
        provider = self._get_provider(self.primary_name)
        start_time = time.perf_counter()

        try:
            res = provider.generate_executive_recommendation(event, do_nothing_impact, options)
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._log_and_print(self.primary_name, "Success", duration_ms)
            self.active_status = self.primary_name
            return res
        except Exception as e:
            err_type = self._classify_error(e)
            self._log_and_print(self.primary_name, err_type)

            # Fallback trigger
            self._log_switching(self.fallback_name)
            fallback_provider = self._get_provider(self.fallback_name)
            fallback_start = time.perf_counter()
            try:
                res = fallback_provider.generate_executive_recommendation(event, do_nothing_impact, options)
                duration_ms = (time.perf_counter() - fallback_start) * 1000
                self._log_and_print(self.fallback_name, "Success", duration_ms)
                self.active_status = self.fallback_name
                return res
            except Exception as fe:
                self._log_and_print(self.fallback_name, "Error")

                # Engages mock safety valve
                self.active_status = "offline"
                logger.warning("[AI] Fallback failed. Engaging Mock Provider safety valve...")
                return self.mock.generate_executive_recommendation(event, do_nothing_impact, options)

    def ask_question(self, question: str, system_state: Dict[str, Any]) -> str:
        provider = self._get_provider(self.active_status)
        start_time = time.perf_counter()
        try:
            res = provider.ask_question(question, system_state)
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._log_and_print(self.active_status, "Success", duration_ms)
            return res
        except Exception as e:
            logger.warning(f"[AI] ask_question failed on active provider {self.active_status}: {str(e)}. Falling back to mock.")
            return self.mock.ask_question(question, system_state)

    def _classify_error(self, err: Exception) -> str:
        err_msg = str(err).lower()
        if "quota" in err_msg or "429" in err_msg or "rate limit" in err_msg:
            return "QuotaExceeded"
        elif "timeout" in err_msg or "timed out" in err_msg:
            return "Timeout"
        elif "auth" in err_msg or "key" in err_msg or "api key" in err_msg or "unauthorized" in err_msg:
            return "AuthError"
        elif "connection" in err_msg or "connect" in err_msg or "offline" in err_msg or "refused" in err_msg:
            return "NetworkFailure"
        return "Error"

    def _log_and_print(self, provider: str, status: str, duration_ms: float = None):
        prov_lbl = "Gemini" if provider == "gemini" else ("Ollama" if provider == "ollama" else "Mock")
        if duration_ms is not None:
            msg = f"[AI]\nProvider={prov_lbl}\nStatus={status}\nDuration={duration_ms:.0f}ms\n"
        else:
            msg = f"[AI]\nProvider={prov_lbl}\nStatus={status}\n"
        print(msg, flush=True)
        logger.info(msg.replace("\n", " "))

    def _log_switching(self, target: str):
        target_lbl = "Gemini" if target == "gemini" else ("Ollama" if target == "ollama" else "Mock")
        msg = f"[AI]\nSwitching to {target_lbl}...\n"
        print(msg, flush=True)
        logger.info(msg.replace("\n", " "))
