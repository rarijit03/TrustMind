"""
Trust Manager — tracks and updates agent trust scores dynamically.
Scores range from 0.1 (unreliable) to 1.0 (fully trusted).
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TrustEvent:
    agent: str
    delta: float
    reason: str
    timestamp: float = field(default_factory=time.time)


class TrustManager:
    INITIAL_SCORES: Dict[str, float] = {
        "orchestrator": 0.90,
        "researcher":   0.72,
        "fact_checker": 0.85,
        "analyst":      0.75,
        "critic":       0.70,
        "synthesizer":  0.80,
    }

    CLAMP_MIN = 0.10
    CLAMP_MAX = 1.00

    def __init__(self):
        self.scores: Dict[str, float] = dict(self.INITIAL_SCORES)
        self.history: List[TrustEvent] = []

    # ── Read ──────────────────────────────────────────────────────────────
    def get(self, agent: str) -> float:
        return self.scores.get(agent, 0.5)

    def all_scores(self) -> Dict[str, float]:
        return dict(self.scores)

    def tier(self, agent: str) -> str:
        s = self.get(agent)
        if s >= 0.85:
            return "high"
        if s >= 0.60:
            return "medium"
        return "low"

    # ── Write ─────────────────────────────────────────────────────────────
    def update(self, agent: str, delta: float, reason: str) -> float:
        old = self.scores.get(agent, 0.5)
        new = max(self.CLAMP_MIN, min(self.CLAMP_MAX, old + delta))
        self.scores[agent] = new
        self.history.append(TrustEvent(agent, delta, reason))
        return new

    # ── Domain events ────────────────────────────────────────────────────
    def on_fact_verified(self, agent: str = "researcher"):
        self.update(agent,        +0.05, "claim verified by fact-checker")
        self.update("fact_checker", +0.02, "successful verification")

    def on_fact_disputed(self, agent: str = "researcher"):
        self.update(agent,        -0.08, "claim disputed by fact-checker")
        self.update("fact_checker", +0.03, "dispute raised (useful signal)")

    def on_agent_agreement(self, a: str, b: str):
        self.update(a, +0.03, f"agrees with {b}")
        self.update(b, +0.03, f"agrees with {a}")

    def on_low_quality_output(self, agent: str):
        self.update(agent, -0.05, "low-quality or empty output")

    def on_critic_insight_adopted(self):
        self.update("critic",      +0.05, "critique adopted by synthesizer")
        self.update("synthesizer", +0.02, "incorporated critique")

    def on_high_confidence_match(self, agent: str):
        self.update(agent, +0.03, "high-confidence output matched consensus")

    # ── Weighted synthesis helper ─────────────────────────────────────────
    def weight_outputs(self, outputs: Dict[str, str]) -> str:
        """
        Returns a formatted string listing agent outputs weighted by trust,
        clearly flagging low-trust contributions.
        """
        lines = []
        for agent, text in outputs.items():
            score = self.get(agent)
            tier  = self.tier(agent)
            flag  = " ⚠️ [LOW TRUST — verify independently]" if tier == "low" else ""
            lines.append(
                f"[{agent.upper()} | trust={score:.2f} | {tier}{flag}]\n{text}\n"
            )
        return "\n".join(lines)

    def summary(self) -> List[Dict]:
        return [
            {"agent": a, "score": round(s, 3), "tier": self.tier(a)}
            for a, s in self.scores.items()
        ]
