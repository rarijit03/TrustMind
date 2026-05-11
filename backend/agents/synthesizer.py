"""Synthesizer Agent - creates the final trust-weighted report."""
from .base_agent import BaseAgent, AgentOutput

class SynthesizerAgent(BaseAgent):
    def __init__(self, api_key: str, trust_manager=None):
        super().__init__("synthesizer", api_key, trust_manager)

    @property
    def system_prompt(self) -> str:
        return (
            "You are an expert synthesis agent. Given outputs from multiple research agents with trust scores,\n"
            "create a coherent, balanced final report. Weight information by agent trust levels.\n"
            "High-trust agents (>=0.85): accept findings readily.\n"
            "Medium-trust agents (0.60-0.84): include with caveats.\n"
            "Low-trust agents (<0.60): flag clearly, require corroboration.\n\n"
            "Format your final report with:\n"
            "EXECUTIVE_SUMMARY: (3-4 sentences)\n"
            "MAIN_FINDINGS: (numbered list, trust-weighted)\n"
            "AREAS_OF_CONSENSUS: (what all agents agree on)\n"
            "AREAS_OF_DISAGREEMENT: (where agents conflict)\n"
            "CAVEATS_AND_LIMITATIONS: (important uncertainties)\n"
            "CONFIDENCE: (overall confidence percentage)"
        )

    async def run(self, query: str, context: str = "") -> AgentOutput:
        msg = f"Research query: {query}\n\nAll agent outputs (with trust scores):\n{context}"
        raw = self._call(msg)
        confidence = self._extract_confidence(raw)
        return AgentOutput(agent=self.name, content=raw, confidence=confidence,
                           metadata={"role": "synthesis"})
