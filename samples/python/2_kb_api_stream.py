"""
KB-only JSON response (SSE streaming).
Reads env: ADP_BASE_URL, ADP_API_KEY, ADP_MODEL
"""
import os, sys, json, requests

BASE = os.getenv("ADP_BASE_URL")
KEY  = os.getenv("ADP_API_KEY")
MODEL= os.getenv("ADP_MODEL", "deepseek-r1")

HEAD = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

payload = {
  "model": MODEL,
  "stream": True,
  "messages": [
    {"role": "system", "content": "Return JSON with citations ONLY from KB."},
    {"role": "user",  "content": "서울점 영업시간과 전화번호 알려줘"}
  ]
}

with requests.post(f"{BASE}/chat/completions", headers=HEAD, json=payload, stream=True, timeout=60) as s:
    s.raise_for_status()
    for line in s.iter_lines():
        if not line:
            continue
        if line.startswith(b"data:"):
            chunk = line[5:].strip()
            if chunk == b"[DONE]":
                break
            try:
                obj = json.loads(chunk)
                delta = obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                sys.stdout.write(delta)
                sys.stdout.flush()
            except Exception:
                pass
print()  # newline
