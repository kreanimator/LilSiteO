#!/usr/bin/env bash
set -euo pipefail

# Pick a model you actually have access to (HF download will happen automatically if logged in)
MODEL="${LLM_MODEL:-Qwen/Qwen2.5-Coder-7B-Instruct}"
HOST="${LLM_HOST:-0.0.0.0}"
PORT="${LLM_PORT:-8000}"

# Try DeepSeek Coder V2 Lite, fallback to original DeepSeek-Coder if it fails
# If model name contains "deepseek", add trust-remote-code flag
EXTRA_FLAGS=""
if [[ "$MODEL" == *"deepseek"* ]]; then
    EXTRA_FLAGS="--trust-remote-code"
fi

python -m vllm.entrypoints.openai.api_server \
  --host "$HOST" \
  --port "$PORT" \
  --model "$MODEL" \
  $EXTRA_FLAGS
