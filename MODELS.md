# Recommended LLM Models for LilSite-o

## Current Model
- **Qwen/Qwen2.5-Coder-7B-Instruct** - Good baseline, but can be improved

## Better Alternatives (Ranked by Quality)

### 1. **DeepSeek Coder** ⚠️ (May have compatibility issues)
- **Model ID**: `deepseek-ai/DeepSeek-Coder-6.7B-Instruct` or `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct`
- **Why**: Excellent code generation, better instruction following than Qwen
- **Size**: 6.7B or 7B (Lite)
- **VRAM**: ~14GB
- **Note**: ⚠️ **May fail with "Engine core initialization failed" error on some vLLM versions**
- **Requires**: `--trust-remote-code` flag with vLLM
- **Status**: Not recommended until vLLM compatibility is confirmed
- **Best for**: High-quality HTML/CSS generation (if it works with your vLLM version)

### 2. **Qwen2.5-Coder-32B-Instruct**
- **Model ID**: `Qwen/Qwen2.5-Coder-32B-Instruct`
- **Why**: Same architecture as current, but much larger = better quality
- **Size**: 32B
- **VRAM**: ~64GB
- **Best for**: If you like Qwen but want better output

### 3. **CodeLlama 34B**
- **Model ID**: `codellama/CodeLlama-34b-Instruct-hf`
- **Why**: Meta's specialized coding model, very strong
- **Size**: 34B
- **VRAM**: ~68GB
- **Best for**: Complex multi-page site generation

### 4. **Mistral 7B/8x7B**
- **Model ID**: `mistralai/Mistral-7B-Instruct-v0.3` or `mistralai/Mixtral-8x7B-Instruct-v0.1`
- **Why**: Great general models, good at following instructions
- **Size**: 7B or 8x7B (MoE)
- **VRAM**: ~14GB (7B) or ~48GB (8x7B)
- **Best for**: Balanced quality and speed

### 5. **Llama 3.1 70B** (If you have resources)
- **Model ID**: `meta-llama/Meta-Llama-3.1-70B-Instruct`
- **Why**: Top-tier open model, excellent quality
- **Size**: 70B
- **VRAM**: ~140GB
- **Best for**: Best possible quality if you have the hardware

## Quick Comparison

| Model | Quality | Speed | VRAM | Compatibility | Best For |
|-------|---------|-------|------|---------------|----------|
| Qwen2.5-Coder-7B | ⭐⭐⭐ | ⚡⚡⚡ | 14GB | ✅ Stable | **Current default (recommended)** |
| DeepSeek Coder | ⭐⭐⭐⭐ | ⚡⚡⚡ | 14GB | ⚠️ May fail | Try if Qwen works |
| Qwen2.5-Coder-32B | ⭐⭐⭐⭐ | ⚡⚡ | 64GB | ✅ Stable | Better Qwen |
| CodeLlama 34B | ⭐⭐⭐⭐ | ⚡⚡ | 68GB | ✅ Stable | Complex sites |
| Mistral 7B | ⭐⭐⭐ | ⚡⚡⚡ | 14GB | ✅ Stable | Balanced |
| Llama 3.1 70B | ⭐⭐⭐⭐⭐ | ⚡ | 140GB | ✅ Stable | Best quality |

## How to Switch Models

1. **Update `.env` file:**
```bash
LLM_MODEL=deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct
```

2. **Or set when starting vLLM:**
```bash
LLM_MODEL="deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct" services/agent/run_llm.sh
```

3. **Restart vLLM server** - the new model will be downloaded automatically

## Recommendations by Use Case

- **Most reliable (default)**: Qwen2.5-Coder-7B ✅
- **Best quality/speed balance**: Qwen2.5-Coder-7B (proven stable) or try DeepSeek if it works
- **Maximum quality (if you have VRAM)**: Llama 3.1 70B or CodeLlama 34B
- **Staying with Qwen family**: Upgrade to Qwen2.5-Coder-32B
- **Fastest with good quality**: Mistral 7B

## Notes

- All models listed are compatible with vLLM
- Models will auto-download from HuggingFace on first use
- Larger models = better quality but slower generation
- VRAM requirements are approximate (actual may vary)
