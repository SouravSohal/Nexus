import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.infrastructure.external.ai.orchestrator import AIOrchestrator
from backend.app.infrastructure.external.ai.providers import GeminiProvider, OllamaProvider, MockProvider
from backend.app.domain.models.event import RiskEvent
from backend.app.domain.models.decision import DoNothingImpact, MitigationOption

class TestAIFailover(unittest.TestCase):
    def setUp(self):
        # Configure test variables
        settings.PRIMARY_AI_PROVIDER = "gemini"
        settings.FALLBACK_AI_PROVIDER = "ollama"
        self.orchestrator = AIOrchestrator()
        
        # Test Nodes list
        self.sample_nodes = [
            {"id": "port-antwerp", "name": "Port of Antwerp", "type": "PORT", "location": "Antwerp, Belgium"}
        ]
        
    @patch("backend.app.infrastructure.external.ai.providers.GeminiProvider.extract_risk_event_from_text")
    def test_gemini_success(self, mock_gemini_extract):
        """Verify that a successful Gemini call completes directly without failover."""
        expected_output = {
            "title": "Port of Antwerp Strike",
            "description": "5-day dockworker walkout",
            "location": "Antwerp, Belgium",
            "affected_node_id": "port-antwerp",
            "severity": 0.85,
            "duration_days": 5,
            "confidence_score": 0.95
        }
        mock_gemini_extract.return_value = expected_output
        
        res = self.orchestrator.extract_risk_event_from_text("Antwerp strike alert", self.sample_nodes)
        
        self.assertEqual(res["affected_node_id"], "port-antwerp")
        self.assertEqual(self.orchestrator.get_provider_status(), "gemini")
        mock_gemini_extract.assert_called_once()

    @patch("backend.app.infrastructure.external.ai.providers.GeminiProvider.extract_risk_event_from_text")
    @patch("backend.app.infrastructure.external.ai.providers.OllamaProvider.extract_risk_event_from_text")
    def test_gemini_quota_exceeded_failover_to_ollama(self, mock_ollama_extract, mock_gemini_extract):
        """Verify that Gemini quota exhaustion triggers failover to Ollama."""
        # Mock Gemini raising QuotaExceeded
        mock_gemini_extract.side_effect = ValueError("429 ResourceExhausted: Quota exceeded")
        
        expected_output = {
            "title": "Port of Antwerp Strike (Local)",
            "description": "5-day dockworker walkout",
            "location": "Antwerp, Belgium",
            "affected_node_id": "port-antwerp",
            "severity": 0.85,
            "duration_days": 5,
            "confidence_score": 0.95
        }
        mock_ollama_extract.return_value = expected_output
        
        res = self.orchestrator.extract_risk_event_from_text("Antwerp strike alert", self.sample_nodes)
        
        self.assertEqual(res["title"], "Port of Antwerp Strike (Local)")
        self.assertEqual(self.orchestrator.get_provider_status(), "ollama")
        mock_gemini_extract.assert_called_once()
        mock_ollama_extract.assert_called_once()

    @patch("backend.app.infrastructure.external.ai.providers.GeminiProvider.extract_risk_event_from_text")
    @patch("backend.app.infrastructure.external.ai.providers.OllamaProvider.extract_risk_event_from_text")
    def test_gemini_timeout_failover_to_ollama(self, mock_ollama_extract, mock_gemini_extract):
        """Verify that Gemini timeout triggers failover to Ollama."""
        # Mock Gemini timeout
        mock_gemini_extract.side_effect = TimeoutError("Request timed out after 10s")
        
        expected_output = {
            "title": "Port of Antwerp Strike (Local)",
            "description": "5-day dockworker walkout",
            "location": "Antwerp, Belgium",
            "affected_node_id": "port-antwerp",
            "severity": 0.85,
            "duration_days": 5,
            "confidence_score": 0.95
        }
        mock_ollama_extract.return_value = expected_output
        
        res = self.orchestrator.extract_risk_event_from_text("Antwerp strike alert", self.sample_nodes)
        
        self.assertEqual(res["title"], "Port of Antwerp Strike (Local)")
        self.assertEqual(self.orchestrator.get_provider_status(), "ollama")
        mock_gemini_extract.assert_called_once()
        mock_ollama_extract.assert_called_once()

    @patch("backend.app.infrastructure.external.ai.providers.GeminiProvider.extract_risk_event_from_text")
    @patch("backend.app.infrastructure.external.ai.providers.OllamaProvider.extract_risk_event_from_text")
    @patch("backend.app.infrastructure.external.ai.providers.MockProvider.extract_risk_event_from_text")
    def test_all_providers_fail_triggers_mock_fallback(self, mock_safety_extract, mock_ollama_extract, mock_gemini_extract):
        """Verify that if both Gemini and Ollama fail, the MockProvider safety valve is engaged."""
        mock_gemini_extract.side_effect = ValueError("Gemini key error")
        mock_ollama_extract.side_effect = ConnectionRefusedError("Ollama port closed")
        
        mock_safety_extract.return_value = {
            "title": "Mock Resilient Event",
            "description": "Mock description",
            "location": "Antwerp, Belgium",
            "affected_node_id": "port-antwerp",
            "severity": 0.50,
            "duration_days": 4,
            "confidence_score": 0.80
        }
        
        res = self.orchestrator.extract_risk_event_from_text("General warning", self.sample_nodes)
        
        self.assertEqual(res["title"], "Mock Resilient Event")
        self.assertEqual(self.orchestrator.get_provider_status(), "offline")
        mock_gemini_extract.assert_called_once()
        mock_ollama_extract.assert_called_once()
        mock_safety_extract.assert_called_once()

    @patch("backend.app.infrastructure.external.ai.providers.OllamaProvider._call_ollama")
    def test_ollama_json_repair_loop(self, mock_call_ollama):
        """Verify that Ollama validation failures trigger the single-attempt repair prompt."""
        # 1. First call returns malformed JSON (missing closing brace)
        # 2. Second call (repair) returns valid JSON
        mock_call_ollama.side_effect = [
            '{"title": "Antwerp Strike", "severity": 0.85, "duration_days": 5', # malformed
            '{"title": "Antwerp Strike", "description": "Dock strike", "location": "Antwerp, Belgium", "affected_node_id": "port-antwerp", "severity": 0.85, "duration_days": 5, "confidence_score": 0.95}' # repaired
        ]
        
        provider = OllamaProvider("http://localhost:11434", "mistral")
        res = provider.extract_risk_event_from_text("Antwerp strike alert", self.sample_nodes)
        
        self.assertEqual(res["title"], "Antwerp Strike")
        self.assertEqual(res["affected_node_id"], "port-antwerp")
        self.assertEqual(mock_call_ollama.call_count, 2)  # Initial call + Repair call

if __name__ == "__main__":
    unittest.main()
