"""
TrustMind — Production Backend
GROQ_API_KEY is read from environment variables (set on Render dashboard).
No API key is ever sent from the frontend.
"""

import asyncio
import json
import os
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

from agents import (
    OrchestratorAgent, ResearcherAgent, FactCheckerAgent,
    AnalystAgent, CriticAgent, SynthesizerAgent,
)
from trust import TrustManager

app = FastAPI(title="TrustMind", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    query: str


def sse(event_type: str, data: dict) -> str:
    return "data: " + json.dumps({"type": event_type, **data}) + "\n\n"


async def stream_research(query: str) -> AsyncGenerator[str, None]:
    if not GROQ_API_KEY:
        yield sse("error", {"message": "GROQ_API_KEY not configured on server."})
        return

    tm   = TrustManager()
    loop = asyncio.get_event_loop()

    agents = {
        "orchestrator": OrchestratorAgent(GROQ_API_KEY, tm),
        "researcher":   ResearcherAgent(GROQ_API_KEY, tm),
        "fact_checker": FactCheckerAgent(GROQ_API_KEY, tm),
        "analyst":      AnalystAgent(GROQ_API_KEY, tm),
        "critic":       CriticAgent(GROQ_API_KEY, tm),
        "synthesizer":  SynthesizerAgent(GROQ_API_KEY, tm),
    }

    yield sse("trust_snapshot", {"scores": tm.all_scores()})

    # Phase 1
    yield sse("agent_start", {"agent": "orchestrator", "phase": 1, "trust": tm.get("orchestrator")})
    plan = await loop.run_in_executor(None, lambda: agents["orchestrator"]._call(
        "Research query: " + query
    ))
    yield sse("agent_output", {
        "agent": "orchestrator", "content": plan,
        "confidence": agents["orchestrator"]._extract_confidence(plan),
        "trust": tm.get("orchestrator"),
    })

    # Phase 2 — parallel
    yield sse("phase", {"phase": 2, "label": "Gathering information and analysis in parallel..."})
    for ag in ("researcher", "analyst"):
        yield sse("agent_start", {"agent": ag, "phase": 2, "trust": tm.get(ag)})

    async def run_agent(name: str, prompt: str):
        out = await loop.run_in_executor(None, lambda: agents[name]._call(prompt))
        return name, out

    p2_tasks = [
        run_agent("researcher", f"Research thoroughly: {query}\n\nPlan:\n{plan}"),
        run_agent("analyst",    f"Analyse deeply: {query}\n\nPlan:\n{plan}"),
    ]
    p2 = {}
    for coro in asyncio.as_completed(p2_tasks):
        name, out = await coro
        p2[name] = out
        yield sse("agent_output", {
            "agent": name, "content": out,
            "confidence": agents[name]._extract_confidence(out),
            "trust": tm.get(name),
        })

    # Phase 3
    yield sse("phase", {"phase": 3, "label": "Verifying claims..."})
    yield sse("agent_start", {"agent": "fact_checker", "phase": 3, "trust": tm.get("fact_checker")})
    fc_out = await loop.run_in_executor(None, lambda: agents["fact_checker"]._call(
        f"Question: {query}\n\nResearch to verify:\n{p2.get('researcher','')}"
    ))
    yield sse("agent_output", {
        "agent": "fact_checker", "content": fc_out,
        "confidence": agents["fact_checker"]._extract_confidence(fc_out),
        "trust": tm.get("fact_checker"),
    })
    yield sse("trust_snapshot", {"scores": tm.all_scores()})

    # Phase 4
    yield sse("phase", {"phase": 4, "label": "Challenging findings..."})
    yield sse("agent_start", {"agent": "critic", "phase": 4, "trust": tm.get("critic")})
    combined = f"RESEARCH:\n{p2.get('researcher','')}\n\nANALYSIS:\n{p2.get('analyst','')}\n\nFACT CHECK:\n{fc_out}"
    critic_out = await loop.run_in_executor(None, lambda: agents["critic"]._call(
        f"Query: {query}\n\nFindings to challenge:\n{combined}"
    ))
    yield sse("agent_output", {
        "agent": "critic", "content": critic_out,
        "confidence": agents["critic"]._extract_confidence(critic_out),
        "trust": tm.get("critic"),
    })

    # Phase 5
    yield sse("phase", {"phase": 5, "label": "Synthesising final report..."})
    yield sse("agent_start", {"agent": "synthesizer", "phase": 5, "trust": tm.get("synthesizer")})
    synth_ctx = tm.weight_outputs({
        "researcher":   p2.get("researcher", ""),
        "analyst":      p2.get("analyst", ""),
        "fact_checker": fc_out,
        "critic":       critic_out,
    })
    synth_out = await loop.run_in_executor(None, lambda: agents["synthesizer"]._call(
        f"Query: {query}\n\nWeighted agent outputs:\n{synth_ctx}"
    ))
    yield sse("agent_output", {
        "agent": "synthesizer", "content": synth_out,
        "confidence": agents["synthesizer"]._extract_confidence(synth_out),
        "trust": tm.get("synthesizer"),
    })

    yield sse("trust_snapshot", {"scores": tm.all_scores()})
    yield sse("final_report",   {"content": synth_out, "trust_summary": tm.summary()})
    yield sse("done", {})


@app.get("/health")
def health():
    configured = bool(GROQ_API_KEY)
    return {"status": "ok", "model": "llama-3.3-70b-versatile", "configured": configured}


@app.post("/api/research")
async def research(req: ResearchRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY not set. Add it in your Render environment variables.")
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    return StreamingResponse(
        stream_research(req.query),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)
