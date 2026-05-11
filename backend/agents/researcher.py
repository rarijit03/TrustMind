"""
Researcher Agent — comprehensive information gathering.
"""

from .base_agent import BaseAgent, AgentOutput


class ResearcherAgent(BaseAgent):
    def __init__(self, api_key: str, trust_manager=None):
        super().__init__("researcher", api_key, trust_manager)

    @property
    def system_prompt(self) -> str:
        return """You are an expert research agent with deep knowledge across all domains.

Your job: gather comprehensive, factual information on the given topic.

Structure your response EXACTLY as:
---RESEARCH---
SUMMARY: <2-3 sentence overview>

KEY FACTS:
• <fact 1 — be specific, include numbers/dates where relevant>
• <fact 2>
• <fact 3>
(include 5-8 bullet points)

CONTEXT: <paragraph on background, history, or relevant framing>

RECENT DEVELOPMENTS: <what has changed or emerged recently in this area>

KNOWLEDGE GAPS: <what remains uncertain or debated>

CONFIDENCE: <overall confidence as a percentage>
---END---

Prioritise accuracy over completeness. Flag uncertainty explicitly."""

    async def run(self, query: str, context: str = "") -> AgentOutput:
        plan_note = f"\nResearch plan guidance:\n{context}" if context else ""
        msg = f"Research this topic thoroughly: {query}{plan_note}"

        raw = self._call(msg)
        confidence = self._extract_confidence(raw)

        return AgentOutput(
            agent      = self.name,
            content    = raw,
            confidence = confidence,
            metadata   = {"role": "research"},
        )
