// LilSite-o UI (vanilla JS)
// Assumes FastAPI agent at http://localhost:9000 by default.
// Change API_BASE if your backend runs elsewhere.

const API_BASE = localStorage.getItem("lilsite_api_base") || "http://localhost:9000";
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
  // Support markdown-like formatting (simple)
  body.innerHTML = content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');

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

function setGenerating(isGenerating) {
  generateBtn.disabled = isGenerating;
  if (isGenerating) {
    generateBtn.innerHTML = '<span class="spinner"></span> Generating...';
    generateBtn.classList.add("generating");
  } else {
    generateBtn.textContent = "Generate";
    generateBtn.classList.remove("generating");
  }
}

function previewUrlFor(sessionId) {
  return `${API_BASE}/preview/${encodeURIComponent(sessionId)}/index.html`;
}

function setPreview(sessionId) {
  const url = previewUrlFor(sessionId);
  previewUrlInput.value = url;
  previewFrame.src = url;
  // Show frame and hide empty state
  const previewEmpty = el("previewEmpty");
  if (previewEmpty) {
    previewEmpty.style.display = "none";
    previewFrame.style.display = "block";
  }
}

// ---------- API calls ----------
async function createSession() {
  const res = await fetch(`${API_BASE}/sessions`, { method: "POST" });
  if (!res.ok) throw new Error(`Create session failed: ${res.status}`);
  const data = await res.json();
  return data.session_id;
}

async function postMessage(sessionId, role, content) {
  const res = await fetch(`${API_BASE}/sessions/${encodeURIComponent(sessionId)}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role, content })
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`POST /messages returned ${res.status}: ${errorText}`);
  }
  return await res.json();
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
    // Welcome message will come from server
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
        // Show visual feedback in UI
        if (ev.message) {
          const msgLower = ev.message.toLowerCase();
          if (msgLower.includes("generation") || msgLower.includes("generating") || msgLower.includes("starting")) {
            setGenerating(true);
          }
        }
        break;

      case "assistant_message":
        appendMessage("assistant", ev.content ?? "");
        // Also log important assistant messages
        if (ev.content) {
          const content = ev.content;
          // Log all assistant messages to logs tab
          appendLog(`[assistant] ${content.replace(/[🚀✅🎉❌⚠️📡🤖📝🔍📦💬👋]/g, "").trim()}`);
        }
        break;

      case "assistant_token":
        // Stream tokens into the last assistant bubble
        streamToken(ev.delta ?? "");
        break;

      case "artifact_published":
        appendLog(`[artifact] published`);
        setGenerating(false);
        if (ev.preview_url) {
          previewUrlInput.value = ev.preview_url;
          previewFrame.src = ev.preview_url;
          // Hide empty state
          const previewEmpty = el("previewEmpty");
          if (previewEmpty) {
            previewEmpty.style.display = "none";
            previewFrame.style.display = "block";
          }
        } else {
          setPreview(currentSessionId);
          const previewEmpty = el("previewEmpty");
          if (previewEmpty) {
            previewEmpty.style.display = "none";
            previewFrame.style.display = "block";
          }
        }
        break;

      case "error":
        appendLog(`[error] ${ev.message ?? "unknown error"}`);
        appendMessage("assistant", `❌ Error: ${ev.message ?? "unknown error"}`);
        setGenerating(false);
        break;

      case "status":
        appendLog(`[status] ${ev.status ?? ""}`);
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
  
  // Append text, preserving any existing HTML
  const currentText = target.textContent || target.innerText || "";
  const newText = currentText + delta;
  // Simple formatting: convert markdown-style to HTML
  target.textContent = newText;
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
  // Initially hide preview frame and show empty state
  previewFrame.style.display = "none";
  const previewEmpty = el("previewEmpty");
  if (previewEmpty) {
    previewEmpty.style.display = "block";
  }
  
  if (currentSessionId) {
    sessionIdInput.value = currentSessionId;
    // Don't auto-load preview on init
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
    // Wait for WebSocket to connect
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  appendMessage("user", text);
  promptInput.value = "";

  // Store message and get agent response
  try {
    const response = await postMessage(currentSessionId, "user", text);
    if (response && response.assistant_response) {
      appendMessage("assistant", response.assistant_response);
      appendLog(`[assistant] ${response.assistant_response}`);
    }
  } catch (e) {
    appendLog(`[error] Failed to get agent response: ${e.message}`);
  }
});

generateBtn.addEventListener("click", async () => {
  try {
    if (!currentSessionId) {
      const id = await createSession();
      setSessionId(id);
      connectWs(id);
      // Wait a bit for WebSocket to connect
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    // Ensure WebSocket is connected
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      appendLog("[ui] Connecting WebSocket...");
      appendMessage("assistant", "🔌 Connecting to server...");
      connectWs(currentSessionId);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    appendLog("[ui] Starting generation...");
    appendMessage("assistant", "🚀 Initiating website generation...");
    setGenerating(true);
    
    await startGeneration(currentSessionId);
    
    // If WebSocket is connected, send generate command
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: "generate" }));
    } else {
      appendLog("[ui] WebSocket not ready, waiting...");
      // Wait a bit more and try again
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: "generate" }));
      } else {
        appendMessage("assistant", "⚠️ WebSocket connection issue. Please try again.");
        setGenerating(false);
      }
    }
  } catch (e) {
    appendLog(`[error] ${e.message}`);
    appendMessage("assistant", `❌ Error: ${e.message}`);
    setGenerating(false);
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
