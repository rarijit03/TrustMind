"""
BaseAgent — Groq-powered foundation for every specialised agent.
Free tier: Llama 3.3 70B at ~750 tokens/sec. No credit card required.
Get your key at: https://console.groq.com
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from groq import Groq

MODEL   = "llama-3.3-70b-versatile"   # Best free model on Groq
TOKENS  = 1500


class AgentOutput:
    def __init__(self, agent: str, content: str, confidence: float,
                 metadata: Optional[Dict[str, Any]] = None):
        self.agent      = agent
        self.content    = content
        self.confidence = max(0.0, min(1.0, confidence))
        self.metadata   = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent":      self.agent,
            "content":    self.content,
            "confidence": self.confidence,
            "metadata":   self.metadata,
        }


class BaseAgent(ABC):
    def __init__(self, name: str, api_key: str, trust_manager=None):
        self.name          = name
        self.trust_manager = trust_manager
        self._client       = Groq(api_key=api_key)

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    @abstractmethod
    async def run(self, query: str, context: str = "") -> AgentOutput: ...

    def _call(self, user_message: str) -> str:
        """Synchronous Groq call — runs via executor in async context."""
        response = self._client.chat.completions.create(
            model=MODEL,
            max_tokens=TOKENS,
            messages=[
                {"role": "system",  "content": self.system_prompt},
                {"role": "user",    "content": user_message},
            ],
        )
        return response.choices[0].message.content

    def _extract_confidence(self, text: str) -> float:
        for pattern in [
            r"confidence[:\s]+([\d]+(?:\.[\d]+)?)\s*%",
            r"confidence[:\s]+([\d]+(?:\.[\d]+)?)",
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                val = float(m.group(1))
                return val / 100 if val > 1 else val
        return 0.75

    def _parse_json_block(self, text: str) -> Dict:
        clean = re.sub(r"```(?:json)?|```", "", text).strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            return {}
