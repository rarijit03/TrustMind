"""Critic Agent - devil's advocate, challenges findings."""
from .base_agent import BaseAgent, AgentOutput

class CriticAgent(BaseAgent):
    def __init__(self, api_key: str, trust_manager=None):
        super().__init__("critic", api_key, trust_manager)

    @property
    def system_prompt(self) -> str:
        return (
            "You are a critical thinking agent (devil's advocate). Your job is to challenge research findings.\n"
            "Identify: weaknesses in arguments, alternative explanations, missing perspectives,\n"
            "counterevidence, logical fallacies, oversimplifications, and what the research ignores.\n\n"
            "Be constructively critical, not dismissive. Format your output with sections:\n"
            "WEAKNESSES, COUNTERARGUMENTS, MISSING_PERSPECTIVES, ALTERNATIVE_EXPLANATIONS, VERDICT, CONFIDENCE."
        )

    async def run(self, query: str, context: str = "") -> AgentOutput:
        msg = f"Research query: {query}\n\nFindings to challenge:\n{context}"
        raw = self._call(msg)
        confidence = self._extract_confidence(raw)
        return AgentOutput(agent=self.name, content=raw, confidence=confidence,
                           metadata={"role": "critique"})
