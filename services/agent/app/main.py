from llm.client import LLMClient

llm = LLMClient()
text = llm.chat([
  {"role": "system", "content": "You are a helpful site generator."},
  {"role": "user", "content": "Generate a landing page plan for a coffee shop."},
])

for delta in llm.stream_chat([...]):
    print(delta, end="", flush=True)
