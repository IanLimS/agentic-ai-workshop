import os
from openai import OpenAI

client = OpenAI(base_url=os.getenv("ADP_BASE_URL"), api_key=os.getenv("ADP_API_KEY"))
model = os.getenv("ADP_MODEL","deepseek-r1")

# 1) Non-streaming
res = client.chat.completions.create(
  model=model,
  messages=[{"role":"user","content":"Give me 3 bullets about agentic AI."}]
)
print(res.choices[0].message.content)

# 2) Streaming
for event in client.chat.completions.create(
  model=model, stream=True,
  messages=[{"role":"user","content":"Stream a one-line haiku about agents."}]
):
  delta = getattr(event.choices[0], "delta", None)
  if delta and delta.content:
    print(delta.content, end="", flush=True)
print()