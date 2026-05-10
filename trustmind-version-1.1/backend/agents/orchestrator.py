"""
Orchestrator Agent — decomposes the user query into a structured research plan.
"""

from .base_agent import BaseAgent, AgentOutput


class OrchestratorAgent(BaseAgent):
    def __init__(self, api_key: str, trust_manager=None):
        super().__init__("orchestrator", api_key, trust_manager)

    @property
    def system_prompt(self) -> str:
        return """You are a senior research orchestrator coordinating a team of AI agents.

Your job: analyse the user's research query and produce a concise research plan.

Return your plan in this exact format:
---PLAN---
CORE_QUESTION: <one-sentence distillation of what we need to answer>
KEY_ANGLES:
- <angle 1>
- <angle 2>
- <angle 3 (max 5)>
PRIORITY: <HIGH | MEDIUM | LOW>
RISK_FLAGS: <potential bias or controversy to watch for>
CONFIDENCE: <your confidence in this plan as a percentage>
---END---

Be precise and actionable. Avoid vague headings."""

    async def run(self, query: str, context: str = "") -> AgentOutput:
        msg = f"Research query: {query}"
        if context:
            msg += f"\n\nAdditional context: {context}"

        raw = self._call(msg)
        confidence = self._extract_confidence(raw)

        return AgentOutput(
            agent      = self.name,
            content    = raw,
            confidence = confidence,
            metadata   = {"role": "planning"},
        )
