# LilSite-o

A tiny AI agent that builds static websites from prompts. Local-first, simple, and hackable.

## Quick Start

```bash
./run.sh
```

This script will:
- Check/start vLLM server (if needed)
- Start FastAPI backend (port 9000)
- Start UI server (port 3000)
- Open browser automatically

## Manual Setup

1. **Create `.env` file:**
```bash
LLM_BASE_URL=http://localhost:8000
LLM_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
LLM_API_KEY=EMPTY
```

2. **Start vLLM server:**
```bash
LLM_MODEL="Qwen/Qwen2.5-Coder-7B-Instruct" services/agent/run_llm.sh
```

3. **Start backend:**
```bash
cd services/agent/app
uvicorn main:app --reload --port 9000
```

4. **Start UI:**
```bash
cd ui
python -m http.server 3000
```

5. **Open:** http://localhost:3000

## How It Works

1. **Chat** with the agent about your website idea
2. **Generate** when ready - the agent creates HTML/CSS files
3. **Preview** appears instantly in the UI

The agent generates:
- Complete HTML pages with embedded CSS
- Multi-page sites (if navigation links are created)
- Minimalistic color blocks instead of images
- Inline SVG icons
- Responsive, modern designs

## Requirements

- Python 3.10+
- 16-32GB RAM (for local LLM)
- GPU recommended (optional but ideal)

## Project Structure

```
lilsite-o/
├── services/agent/app/    # FastAPI backend
├── ui/                    # Web UI
├── runtime/               # Generated sites (auto-created)
│   ├── runs/             # Session workspaces
│   └── published/        # Preview-ready sites
└── run.sh                # Startup script
```

## License

MIT
