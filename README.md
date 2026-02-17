LilSite-o

A tiny AI agent that builds static websites from prompts.

LilSite-o is a local-first, open-source project that generates small static sites using an LLM, then previews them instantly in a built-in UI.

The goal is to keep the architecture:

simple

transparent

hackable

easy to run on a single machine

Core idea
User prompt
   ↓
LLM (local server)
   ↓
Agent (FastAPI)
   ↓
Static site files
   ↓
Published preview
   ↓
Iframe in UI


No heavy frameworks, no complex orchestration.

Current status (v0 skeleton)
Implemented

Project structure

UI (chat + logs + preview iframe)

FastAPI backend skeleton

LLM client (OpenAI-compatible)

Local model server via vLLM

Basic generation flow (structure ready)

Not implemented yet

Real site generation logic

Template rendering

Validator

Persistent session storage

Multi-step agent logic

Project structure
lilsite-o/
│
├─ README.md
├─ .env.example
├─ run.sh
│
├─ services/
│  ├─ agent/
│  │  ├─ app/
│  │  │  ├─ main.py              # FastAPI entrypoint
│  │  │  │
│  │  │  ├─ api/
│  │  │  │   ├─ sessions.py
│  │  │  │   ├─ generate.py
│  │  │  │   └─ health.py
│  │  │  │
│  │  │  ├─ ws/
│  │  │  │   └─ stream.py
│  │  │  │
│  │  │  ├─ core/
│  │  │  │   ├─ config.py
│  │  │  │   ├─ models.py
│  │  │  │   ├─ events.py
│  │  │  │   ├─ storage.py
│  │  │  │   └─ publish.py
│  │  │  │
│  │  │  ├─ llm/
│  │  │  │   ├─ client.py        # LLM client (OpenAI-compatible)
│  │  │  │   └─ prompts.py
│  │  │  │
│  │  │  ├─ tools/
│  │  │  │   ├─ site_writer.py
│  │  │  │   ├─ assets.py
│  │  │  │   └─ validator.py
│  │  │  │
│  │  │  └─ runners/
│  │  │      ├─ host_runner.py
│  │  │      └─ sandbox.py
│  │  │
│  │  ├─ requirements.txt
│  │  └─ run_llm.sh              # starts vLLM server
│  │
│  └─ llm/
│     └─ vllm/
│
├─ ui/
│  ├─ index.html
│  ├─ app.js
│  ├─ styles.css
│  └─ components/
│     ├─ layout.css
│     └─ chat.css
│
├─ templates/
│  ├─ sites/
│  │  └─ landing/
│  │     ├─ index.html
│  │     ├─ styles.css
│  │     └─ pages/
│  │        ├─ privacy.html
│  │        ├─ terms.html
│  │        └─ contact.html
│  │
│  └─ icons/
│     ├─ globe.svg
│     ├─ coffee.svg
│     ├─ briefcase.svg
│     ├─ heart.svg
│     └─ lightning.svg
│
└─ runtime/
   ├─ runs/        # temporary session workspaces
   ├─ published/   # static preview output
   └─ logs/

Requirements

Python 3.10+

16–32GB RAM recommended

GPU recommended for local LLM (optional but ideal)

Setup
1. Create virtual environment
python -m venv .venv
source .venv/bin/activate

2. Install agent dependencies
cd services/agent
pip install -r requirements.txt

3. Install vLLM
pip install vllm

Run the local LLM server

From project root:

LLM_MODEL="Qwen/Qwen2.5-Coder-7B-Instruct" \
services/agent/run_llm.sh


Test it:

curl http://localhost:8000/v1/models

Configure environment

Create .env in repo root:

LLM_BASE_URL=http://localhost:8000
LLM_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
LLM_API_KEY=EMPTY

Run the agent backend

From:

services/agent/app


Run:

uvicorn main:app --reload --port 9000

Run the UI

From repo root:

cd ui
python -m http.server 3000


Open:

http://localhost:3000

Runtime folders

These are created automatically:

runtime/
  runs/         # per-session working directories
  published/    # preview-ready static sites
  logs/


Example:

runtime/published/abc123/index.html


Preview URL:

http://localhost:9000/preview/abc123/index.html

How generation will work (planned flow)

UI sends prompt

Agent calls LLM

LLM returns site plan or files

Agent:

writes files

validates them

publishes to runtime/published/{session}

UI loads preview in iframe

Design principles

Local-first

Minimal dependencies

No heavy agent frameworks

Simple static output

Fully inspectable runs

Roadmap
v0.1

Deterministic site generation (no LLM)

Static templates

Publish + preview

v0.2

LLM-generated content

Theme + page structure

Validation

v0.3

Edit existing site

Multi-page reasoning

Asset generation

v0.4

Docker support

Remote deployment

User/session storage

License

MIT (recommended for open-source dev tools)
