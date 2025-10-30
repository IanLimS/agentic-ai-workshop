"""
KB-only JSON response (non-streaming).
Reads env: ADP_BASE_URL, ADP_API_KEY, ADP_MODEL
"""
import os, json, requests

BASE = os.getenv("ADP_BASE_URL")
KEY  = os.getenv("ADP_API_KEY")
MODEL= os.getenv("ADP_MODEL", "deepseek-r1")

HEAD = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

payload = {
  "model": MODEL,
  "messages": [
    {"role": "system", "content": "Answer ONLY using the app Knowledge Base. Respond in JSON: {\"found\":bool, \"answer\":string, \"citations\":[{\"file\":string, \"loc\":string}]}"},
    {"role": "user", "content": "SKU-1003 Headphones의 가격은 얼마야?"}
  ]
}

r = requests.post(f"{BASE}/chat/completions", headers=HEAD, json=payload, timeout=60)
r.raise_for_status()
content = r.json()["choices"][0]["message"]["content"]
print(content)  # JSON string from the model
try:
    obj = json.loads(content)
    print("\nParsed summary -> found:", obj.get("found"), "| citations:", obj.get("citations"))
except Exception:
    pass
