import os, sys, json, requests
base = os.getenv("ADP_BASE_URL"); key = os.getenv("ADP_API_KEY"); model = os.getenv("ADP_MODEL","deepseek-r1")
HEAD = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

# 1) Non-streaming
r = requests.post(f"{base}/chat/completions", headers=HEAD, json={
  "model": model,
  "messages": [{"role":"user","content":"에이전틱 AI 3가지 활용사례를 알려줘."}]
})
r.raise_for_status()
print(r.json()["choices"][0]["message"]["content"])

# 2) Streaming (SSE)
with requests.post(f"{base}/chat/completions", headers=HEAD, json={
  "model": model, "stream": True,
  "messages": [{"role":"user","content":"에이전트에 관한 짧은 하이쿠를 스트리밍해줘."}]
}, stream=True) as s:
  s.raise_for_status()
  for line in s.iter_lines():
    if not line: continue
    if line.startswith(b"data:"):
      chunk = line[5:].strip()
      if chunk == b"[DONE]": break
      try:
        obj = json.loads(chunk)
        sys.stdout.write(obj.get("choices", [{}])[0].get("delta", {}).get("content", ""))
        sys.stdout.flush()
      except Exception:
        pass
print()