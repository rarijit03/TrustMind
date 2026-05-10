"""Fact Checker Agent - verifies claims from the Researcher."""
import re
from .base_agent import BaseAgent, AgentOutput


SYSTEM = (
    "You are a rigorous fact-checking agent. Evaluate each claim in the research output.\n"
    "For each claim output:\n"
    "  CLAIM: <claim>\n"
    "  STATUS: VERIFIED | UNVERIFIED | DISPUTED\n"
    "  REASONING: <why>\n"
    "  ---\n"
    "Then provide: OVERALL_VERDICT, VERIFIED_COUNT, DISPUTED_COUNT, KEY_CORRECTIONS, CONFIDENCE (percent)."
)


class FactCheckerAgent(BaseAgent):
    def __init__(self, api_key: str, trust_manager=None):
        super().__init__("fact_checker", api_key, trust_manager)

    @property
    def system_prompt(self) -> str:
        return SYSTEM

    async def run(self, query: str, context: str = "") -> AgentOutput:
        msg = f"Original question: {query}\n\nResearch to fact-check:\n{context}"
        raw = self._call(msg)
        confidence = self._extract_confidence(raw)
        verified = len(re.findall(r"STATUS:\s*VERIFIED", raw, re.IGNORECASE))
        disputed = len(re.findall(r"STATUS:\s*DISPUTED", raw, re.IGNORECASE))
        if self.trust_manager:
            for _ in range(verified):
                self.trust_manager.on_fact_verified("researcher")
            for _ in range(disputed):
                self.trust_manager.on_fact_disputed("researcher")
        return AgentOutput(
            agent=self.name, content=raw, confidence=confidence,
            metadata={"verified": verified, "disputed": disputed, "role": "fact_check"},
        )
