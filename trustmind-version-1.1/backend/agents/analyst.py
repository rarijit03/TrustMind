"""Analyst Agent - deep analysis and pattern recognition."""
from .base_agent import BaseAgent, AgentOutput

class AnalystAgent(BaseAgent):
    def __init__(self, api_key: str, trust_manager=None):
        super().__init__("analyst", api_key, trust_manager)

    @property
    def system_prompt(self) -> str:
        return (
            "You are a deep analytical agent. Given research findings, identify:\n"
            "1. Non-obvious patterns and trends\n"
            "2. Implications and second-order effects\n"
            "3. Knowledge gaps and what questions remain unanswered\n"
            "4. Potential biases in the research\n"
            "5. Connections to broader contexts\n\n"
            "Format your output with sections: PATTERNS, IMPLICATIONS, GAPS, BIASES, CONNECTIONS, CONFIDENCE."
        )

    async def run(self, query: str, context: str = "") -> AgentOutput:
        msg = f"Research query: {query}\n\nResearch findings to analyse:\n{context}"
        raw = self._call(msg)
        confidence = self._extract_confidence(raw)
        return AgentOutput(agent=self.name, content=raw, confidence=confidence,
                           metadata={"role": "analysis"})
