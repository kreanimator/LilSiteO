// LilSite-o UI (vanilla JS)
// Assumes FastAPI agent at http://localhost:8080 by default.
// Change API_BASE if your backend runs elsewhere.

const API_BASE = localStorage.getItem("lilsite_api_base") || "http://localhost:8080";
const WS_BASE = API_BASE.replace(/^http/, "ws");

const el = (id) => document.getElementById(id);

const sessionIdInput = el("sessionId");
const newSessionBtn = el("newSessionBtn");
const connectBtn = el("connectBtn");
const promptForm = el("promptForm");
const promptInput = el("promptInput");
const generateBtn = el("generateBtn");
const openPreviewBtn = el("openPreviewBtn");

const messagesEl = el("messages");
const logsEl = el("logs");
const clearLogsBtn = el("clearLogsBtn");

const previewFrame = el("previewFrame");
const previewUrlInput = el("previewUrl");
const reloadPreviewBtn = el("reloadPreviewBtn");

const apiBaseLabel = el("apiBaseLabel");
const wsStatus = el("wsStatus");

// Tabs
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tabbody").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    const key = btn.dataset.tab;
    el(`tab-${key}`).classList.add("active");
  });
});

apiBaseLabel.textContent = API_BASE;

let ws = null;
let currentSessionId = localStorage.getItem("lilsite_session_id") || "";

// ---------- UI helpers ----------
function nowTime() {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function appendLog(line) {
  logsEl.textContent += line + "\n";
  logsEl.scrollTop = logsEl.scrollHeight;
}

function appendMessage(role, content) {
  const wrap = document.createElement("div");
  wrap.className = "msg " + (role === "user" ? "user" : "assistant");

  const meta = document.createElement("div");
  meta.className = "meta";
  meta.innerHTML = `<span>${role}</span><span>${nowTime()}</span>`;

  const body = document.createElement("div");
  body.className = "content";
  body.textContent = content;

  wrap.appendChild(meta);
  wrap.appendChild(body);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setWsStatus(s) {
  wsStatus.textContent = s;
  wsStatus.style.color = (s === "connected") ? "var(--accent)" :
                         (s === "connecting") ? "var(--accent2)" :
                         "rgba(255,255,255,.65)";
}

function previewUrlFor(sessionId) {
  return `${API_BASE}/preview/${encodeURIComponent(sessionId)}/index.html`;
}

function setPreview(sessionId) {
  const url = previewUrlFor(sessionId);
  previewUrlInput.value = url;
  previewFrame.src = url;
}

// ---------- API calls ----------
async function createSession() {
  const res = await fetch(`${API_BASE}/sessions`, { method: "POST" });
  if (!res.ok) throw new Error(`Create session failed: ${res.status}`);
  const data = await res.json();
  return data.session_id;
}

async function postMessage(sessionId, role, content) {
  // Optional endpoint. If you don’t have it, you can remove this call.
  const res = await fetch(`${API_BASE}/sessions/${encodeURIComponent(sessionId)}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role, content })
  });
  // Don't hard-fail UI if endpoint isn't implemented yet.
  if (!res.ok) appendLog(`[warn] POST /messages returned ${res.status} (you can ignore if not implemented)`);
}

async function startGeneration(sessionId) {
  const res = await fetch(`${API_BASE}/sessions/${encodeURIComponent(sessionId)}/generate`, {
    method: "POST"
  });
  if (!res.ok) throw new Error(`Generate failed: ${res.status}`);
  return await res.json().catch(() => ({}));
}

// ---------- WebSocket ----------
function connectWs(sessionId) {
  if (ws) {
    ws.close();
    ws = null;
  }

  const wsUrl = `${WS_BASE}/sessions/${encodeURIComponent(sessionId)}/stream`;
  appendLog(`[ws] connecting ${wsUrl}`);
  setWsStatus("connecting");

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    appendLog("[ws] connected");
    setWsStatus("connected");
  };

  ws.onclose = () => {
    appendLog("[ws] disconnected");
    setWsStatus("disconnected");
  };

  ws.onerror = (e) => {
    appendLog("[ws] error");
    setWsStatus("disconnected");
  };

  ws.onmessage = (msg) => {
    // Expect JSON events from backend
    // Example event shapes:
    // { "type": "assistant_message", "content": "..." }
    // { "type": "assistant_token", "delta": "..." }
    // { "type": "log", "message": "..." }
    // { "type": "artifact_published", "preview_url": "..." }
    let ev = null;
    try { ev = JSON.parse(msg.data); } catch {
      appendLog(`[ws] ${msg.data}`);
      return;
    }

    if (!ev || !ev.type) {
      appendLog(`[ws] ${msg.data}`);
      return;
    }

    switch (ev.type) {
      case "log":
        appendLog(`[log] ${ev.message ?? ""}`);
        break;

      case "assistant_message":
        appendMessage("assistant", ev.content ?? "");
        break;

      case "assistant_token":
        // Optional: stream tokens into the last assistant bubble
        streamToken(ev.delta ?? "");
        break;

      case "artifact_published":
        appendLog(`[artifact] published`);
        if (ev.preview_url) {
          previewUrlInput.value = ev.preview_url;
          previewFrame.src = ev.preview_url;
        } else {
          setPreview(sessionId);
        }
        break;

      case "error":
        appendLog(`[error] ${ev.message ?? "unknown error"}`);
        break;

      default:
        appendLog(`[${ev.type}] ${JSON.stringify(ev)}`);
        break;
    }
  };
}

function streamToken(delta) {
  // Add tokens into the last assistant message bubble, or create one.
  const items = messagesEl.querySelectorAll(".msg.assistant .content");
  let target = items.length ? items[items.length - 1] : null;

  if (!target) {
    appendMessage("assistant", "");
    const items2 = messagesEl.querySelectorAll(".msg.assistant .content");
    target = items2[items2.length - 1];
  }
  target.textContent += delta;
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ---------- Wire up ----------
function setSessionId(id) {
  currentSessionId = id;
  sessionIdInput.value = id;
  localStorage.setItem("lilsite_session_id", id);
  setPreview(id);
}

(async function init() {
  if (currentSessionId) {
    sessionIdInput.value = currentSessionId;
    setPreview(currentSessionId);
  }
})();

newSessionBtn.addEventListener("click", async () => {
  try {
    const id = await createSession();
    messagesEl.innerHTML = "";
    logsEl.textContent = "";
    setSessionId(id);
    connectWs(id);
  } catch (e) {
    appendLog(`[error] ${e.message}`);
  }
});

connectBtn.addEventListener("click", () => {
  const id = sessionIdInput.value.trim();
  if (!id) return;
  setSessionId(id);
  connectWs(id);
});

promptForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = promptInput.value.trim();
  if (!text) return;

  if (!currentSessionId) {
    const id = await createSession();
    setSessionId(id);
    connectWs(id);
  }

  appendMessage("user", text);
  promptInput.value = "";

  // Optional: store message server-side
  await postMessage(currentSessionId, "user", text);
});

generateBtn.addEventListener("click", async () => {
  try {
    if (!currentSessionId) {
      const id = await createSession();
      setSessionId(id);
      connectWs(id);
    }
    appendLog("[ui] start generation");
    await startGeneration(currentSessionId);
  } catch (e) {
    appendLog(`[error] ${e.message}`);
  }
});

openPreviewBtn.addEventListener("click", () => {
  if (!currentSessionId) return;
  window.open(previewUrlFor(currentSessionId), "_blank");
});

reloadPreviewBtn.addEventListener("click", () => {
  if (!currentSessionId) return;
  // force reload
  const url = previewUrlFor(currentSessionId) + `?t=${Date.now()}`;
  previewUrlInput.value = url;
  previewFrame.src = url;
});

clearLogsBtn.addEventListener("click", () => {
  logsEl.textContent = "";
});

// Convenience: Ctrl+Enter to send prompt
promptInput.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    promptForm.requestSubmit();
  }
});
