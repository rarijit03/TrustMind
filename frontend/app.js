/* TrustMind — Production Frontend */

const AGENTS = {
  orchestrator: { color: "#6366F1", label: "Orchestrator" },
  researcher:   { color: "#0EA5E9", label: "Researcher"   },
  fact_checker: { color: "#F59E0B", label: "Fact Checker" },
  analyst:      { color: "#10B981", label: "Analyst"      },
  critic:       { color: "#EF4444", label: "Critic"       },
  synthesizer:  { color: "#8B5CF6", label: "Synthesizer"  },
};

const PHASES = {
  2: "Gathering information and analysis in parallel...",
  3: "Verifying claims...",
  4: "Challenging findings...",
  5: "Synthesising final report...",
};

const BADGE_COLORS_LIGHT = {
  orchestrator: ["#EEF2FF","#4338CA"], researcher:   ["#E0F2FE","#0369A1"],
  fact_checker: ["#FFFBEB","#B45309"], analyst:      ["#ECFDF5","#065F46"],
  critic:       ["#FEF2F2","#B91C1C"], synthesizer:  ["#F5F3FF","#6D28D9"],
  system:       ["#F1F5F9","#475569"],
};
const BADGE_COLORS_DARK = {
  orchestrator: ["#2D2B6B","#A5B4FC"], researcher:   ["#0C2D40","#7DD3FC"],
  fact_checker: ["#3D2D00","#FCD34D"], analyst:      ["#063D28","#6EE7B7"],
  critic:       ["#3D0808","#FCA5A5"], synthesizer:  ["#2D1B6B","#C4B5FD"],
  system:       ["#1E293B","#94A3B8"],
};

const $ = id => document.getElementById(id);

/* ── Backend URL resolution ── */
function getBackendUrl() {
  const cfg = window.TRUSTMIND_CONFIG || {};
  // If config has a URL, use it. Otherwise auto-detect.
  if (cfg.BACKEND_URL && cfg.BACKEND_URL.trim() !== "") {
    return cfg.BACKEND_URL.replace(/\/$/, "");
  }
  // In production (Vercel), the backend URL must be set in config.js.
  // Locally, fall back to localhost:8000.
  return "http://localhost:8000";
}

/* ── Dark mode ── */
function isDark() { return document.documentElement.getAttribute("data-theme") === "dark"; }

function applyTheme(dark) {
  document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  $("themeIcon").textContent = dark ? "☀" : "☾";
  localStorage.setItem("tm_theme", dark ? "dark" : "light");
}

// On load: respect saved preference, then system preference
(function initTheme() {
  const saved = localStorage.getItem("tm_theme");
  if (saved) { applyTheme(saved === "dark"); return; }
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyTheme(prefersDark);
})();

$("themeToggle").onclick = () => applyTheme(!isDark());

/* ── Examples ── */
document.querySelectorAll(".example").forEach(b =>
  b.onclick = () => { $("queryInput").value = b.dataset.q; $("queryInput").focus(); }
);

/* ── Run ── */
let running = false;

$("runBtn").onclick = startResearch;
$("queryInput").addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") startResearch();
});
$("logClear").onclick  = () => { $("feed").innerHTML = ""; };
$("newResearch").onclick = reset;

$("copyReport").onclick = () => {
  navigator.clipboard.writeText($("reportBody").textContent);
  $("copyReport").textContent = "Copied!";
  setTimeout(() => $("copyReport").textContent = "Copy", 2000);
};

async function startResearch() {
  const query = $("queryInput").value.trim();
  if (!query || running) return;

  running = true;
  $("runBtn").disabled = true;
  $("runBtn").textContent = "Working…";

  $("heroSection").style.display  = "none";
  $("dashboard").style.display    = "block";
  $("reportWrap").style.display   = "none";
  $("feed").innerHTML             = "";
  $("phaseLine").textContent      = "Planning research strategy...";
  $("dashQuery").textContent      = "\u201c" + query + "\u201d";
  $("newResearch").style.display  = "none";

  buildAgentCards();

  try {
    const res = await fetch(getBackendUrl() + "/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    if (!res.ok) {
      const e = await res.json().catch(() => ({}));
      throw new Error(e.detail || "HTTP " + res.status);
    }
    await consumeSSE(res);
  } catch (err) {
    log("system", "Error: " + err.message);
    console.error(err);
  } finally {
    running = false;
    $("runBtn").disabled   = false;
    $("runBtn").textContent = "Research";
    $("newResearch").style.display = "inline-flex";
  }
}

async function consumeSSE(res) {
  const reader = res.body.getReader(), dec = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const lines = buf.split("\n"); buf = lines.pop();
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try { handleEvent(JSON.parse(line.slice(6))); } catch {}
    }
  }
}

function handleEvent(e) {
  switch (e.type) {
    case "trust_snapshot": updateTrust(e.scores); break;
    case "phase":          $("phaseLine").textContent = PHASES[e.phase] || e.label; break;
    case "agent_start":    setActive(e.agent); log(e.agent, "Running…"); break;
    case "agent_output":
      setDone(e.agent, e.confidence);
      log(e.agent, e.content.replace(/\n+/g," ").slice(0,160));
      break;
    case "error":
      log("system", e.message || "Unknown error");
      break;
    case "final_report":
      $("reportBody").textContent   = e.content;
      if (e.trust_summary) buildScorecard(e.trust_summary);
      $("reportWrap").style.display = "block";
      $("phaseLine").textContent    = "Complete.";
      $("reportWrap").scrollIntoView({ behavior: "smooth", block: "start" });
      break;
  }
}

function buildAgentCards() {
  $("agentRow").innerHTML = "";
  Object.entries(AGENTS).forEach(([id, meta]) => {
    const card = document.createElement("div");
    card.className = "agent-card"; card.id = "card-" + id;
    card.style.setProperty("--agent-color", meta.color);
    card.innerHTML = `
      <div class="agent-dot" id="dot-${id}"></div>
      <div class="agent-name">${meta.label}</div>
      <div class="agent-score-val" id="sv-${id}">—</div>
      <div class="agent-track"><div class="agent-fill" id="af-${id}" style="width:0%"></div></div>
      <div class="agent-conf" id="cf-${id}"></div>
    `;
    $("agentRow").appendChild(card);
  });
}

function updateTrust(scores) {
  let sum = 0, n = 0;
  Object.entries(scores).forEach(([id, s]) => {
    const af = $("af-" + id), sv = $("sv-" + id);
    if (af) af.style.width = Math.round(s * 100) + "%";
    if (sv) sv.textContent  = Math.round(s * 100) + "%";
    sum += s; n++;
  });
  const avg = sum / n;
  $("trustFill").style.width = (avg * 100).toFixed(1) + "%";
  $("trustPct").textContent  = (avg * 100).toFixed(1) + "%";
}

function setActive(id) {
  const c = $("card-" + id); if (!c) return;
  c.classList.add("active"); c.classList.remove("done");
}

function setDone(id, conf) {
  const c = $("card-" + id); if (!c) return;
  c.classList.remove("active"); c.classList.add("done");
  if (conf != null) {
    const cf = $("cf-" + id);
    if (cf) { cf.textContent = Math.round(conf * 100) + "% confidence"; cf.classList.add("show"); }
  }
}

function buildScorecard(summary) {
  $("scorecard").innerHTML = "";
  summary.forEach(({ agent, score, tier }) => {
    const pill = document.createElement("div");
    pill.className = "score-pill";
    pill.innerHTML = `<span class="score-dot ${tier}"></span>${AGENTS[agent]?.label || agent} — ${Math.round(score * 100)}%`;
    $("scorecard").appendChild(pill);
  });
}

function ts() {
  return new Date().toLocaleTimeString("en-US", { hour12:false, hour:"2-digit", minute:"2-digit", second:"2-digit" });
}

function log(agentId, text) {
  const entry  = document.createElement("div");
  entry.className = "feed-entry";
  const colors = isDark() ? BADGE_COLORS_DARK : BADGE_COLORS_LIGHT;
  const [bg, fg] = colors[agentId] || colors.system;
  const label  = AGENTS[agentId]?.label || agentId;
  const safe   = text.replace(/</g,"&lt;").replace(/>/g,"&gt;");
  entry.innerHTML = `
    <span class="feed-ts">${ts()}</span>
    <span class="feed-badge" style="background:${bg};color:${fg}">${label}</span>
    <span class="feed-text">${safe.slice(0,180)}${text.length > 180 ? "…" : ""}</span>
  `;
  $("feed").appendChild(entry);
  $("feed").scrollTop = $("feed").scrollHeight;
}

function reset() {
  $("heroSection").style.display = "block";
  $("dashboard").style.display   = "none";
  $("reportWrap").style.display  = "none";
  $("queryInput").value          = "";
  $("queryInput").focus();
}
