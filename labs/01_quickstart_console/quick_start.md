# 📘 ADP API/SDK 워크샵 (KR)

> 이 워크샵은 **콘솔 없이**도 ADP(TCADP)를 바로 호출해볼 수 있도록 **API/SDK 중심**으로 구성되어 있습니다. 
> 💡 콘솔에서 애플리케이션을 만드는 절차가 필요하다면 `labs/01_quickstart_console/quick_start_from_console.md`를 먼저 참고하세요.

## 0) 우리가 만들 것
- `.env` 기반 환경 변수 세팅 → **OpenAI 호환 API**로 **chat/embeddings** 호출
- **스트리밍(SSE)** 수신 방법 이해
- **툴콜(Function/Tools)** 왕복 패턴 익히기 (모델이 함수 호출 제안 → 실제 실행 → 결과 재전달 → 최종 답변)
- **오류 처리/백오프** 공통 패턴 적용

> 왜 OpenAI 호환?  
> ADP는 OpenAI 스타일의 엔드포인트(예: `/chat/completions`, `/embeddings`)를 제공합니다. 덕분에 익숙한 SDK(파이썬/노드)로 빠르게 연동할 수 있고, 코드 변경이 최소화됩니다.

---

## 1) 준비물
- ADP 활성화 & 모델 쿼터 (예: `deepseek-r1`)
- 로컬 도구: `curl`, **Python 3.10+** 또는 **Node 18+**
- 레포 루트에 `.env` 생성:
  ```ini
  ADP_BASE_URL=https://api.lkeap.tencentcloud.com/v1
  ADP_API_KEY=YOUR_ADP_API_KEY
  ADP_MODEL=deepseek-r1
  # (옵션) 임베딩 전용 모델을 분리하고 싶다면
  # ADP_EMBEDDINGS_MODEL=text-embedding-3-large
  ```
- 셸에 적용:
  ```bash
  # macOS/Linux
  export $(grep -v '^#' .env | xargs)
  ```
  ```powershell
  # Windows PowerShell
  Get-Content .env | ForEach-Object {
    if ($_ -and -not $_.StartsWith('#')) { $name,$value = $_.Split('='); $env:$name=$value }
  }
  ```

> **자주 하는 실수**: `Bearer` 접두사 누락, `/v1` 경로 오타, 모델명 오타.

---

## 2) 첫 호출 — cURL로 연기 풀기
가장 단순한(논‑스트리밍) 호출입니다. **요청 JSON 구조**(`model`, `messages`)에 주목하세요.
```bash
curl -s -X POST "$ADP_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $ADP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"${ADP_MODEL:-deepseek-r1}"'",
    "messages": [
      {"role":"user","content":"에이전틱 AI가 해결하는 문제를 3가지로 요약해줘."}
    ]
  }' | jq -r '.choices[0].message.content'
```
**무엇을 확인하나요?**
- 200 OK & 응답 JSON 
- `choices[0].message.content`에 자연스러운 답변

**스트리밍(SSE)**은 `"stream": true`만 추가하면 됩니다. 터미널에서는 `data: ...`가 연속 출력되고 마지막에 `data: [DONE]`가 옵니다.

---

## 3) Python — `requests`와 스트리밍
아래 파일명으로 저장해 두고 바로 실행해 보세요.
```python
# samples/python/chat_requests.py
import os, sys, json, requests
base = os.getenv("ADP_BASE_URL"); key = os.getenv("ADP_API_KEY"); model = os.getenv("ADP_MODEL","deepseek-r1")
HEAD = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

# 1) 논-스트리밍
r = requests.post(f"{base}/chat/completions", headers=HEAD, json={
  "model": model,
  "messages": [{"role":"user","content":"에이전틱 AI 3가지 활용사례를 알려줘."}]
})
r.raise_for_status()
print(r.json()["choices"][0]["message"]["content"])

# 2) 스트리밍(SSE)
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
```
> **왜 스트리밍?** 사용자 경험(UX) 측면에서 대기 시간을 체감상 줄이고, 긴 답변도 자연스럽게 보여줄 수 있습니다.

---

## 4) Python — OpenAI **공식 SDK**로 더 간결하게
`base_url`만 ADP로 바꿔주면 됩니다.
```python
# samples/python/chat_sdk.py
import os
from openai import OpenAI

client = OpenAI(base_url=os.getenv("ADP_BASE_URL"), api_key=os.getenv("ADP_API_KEY"))
model = os.getenv("ADP_MODEL","deepseek-r1")

# 1) 논-스트리밍
res = client.chat.completions.create(
  model=model,
  messages=[{"role":"user","content":"Give me 3 bullets about agentic AI."}]
)
print(res.choices[0].message.content)

# 2) 스트리밍
for event in client.chat.completions.create(
  model=model, stream=True,
  messages=[{"role":"user","content":"Stream a one-line haiku about agents."}]
):
  delta = getattr(event.choices[0], "delta", None)
  if delta and delta.content:
    print(delta.content, end="", flush=True)
print()
```
> **포인트**: SDK를 쓰면 직렬화/예외 처리/타입 힌트 지원이 편리합니다.

---

## 5) Node.js — OpenAI SDK (ESM)
```js
// samples/node/chat_sdk.mjs
import 'dotenv/config'
import OpenAI from 'openai'

const client = new OpenAI({ baseURL: process.env.ADP_BASE_URL, apiKey: process.env.ADP_API_KEY })
const model = process.env.ADP_MODEL || 'deepseek-r1'

// 1) 논-스트리밍
const res = await client.chat.completions.create({
  model, messages: [{ role:'user', content:'Give me 3 bullets on agentic AI.' }]
})
console.log(res.choices?.[0]?.message?.content)

// 2) 스트리밍
const stream = await client.chat.completions.create({
  model, stream: true,
  messages: [{ role:'user', content:'Stream a one-line haiku about agents.' }]
})
for await (const event of stream) {
  const delta = event.choices?.[0]?.delta?.content
  if (delta) process.stdout.write(delta)
}
console.log()
```

---

## 6) 임베딩(Embeddings) — KB/RAG의 친구
임베딩은 텍스트를 벡터로 바꿔 **유사도 검색**이 가능하도록 합니다. 아래는 Python/Node 예시입니다.
```python
# samples/python/embeddings_sdk.py
import os
from openai import OpenAI

client = OpenAI(base_url=os.getenv("ADP_BASE_URL"), api_key=os.getenv("ADP_API_KEY"))
model = os.getenv("ADP_EMBEDDINGS_MODEL","text-embedding-3-large")

emb = client.embeddings.create(model=model, input=["hello world", "agentic ai"])
print(len(emb.data[0].embedding), len(emb.data[1].embedding))
```
```js
// samples/node/embeddings_sdk.mjs
import 'dotenv/config'
import OpenAI from 'openai'
const client = new OpenAI({ baseURL: process.env.ADP_BASE_URL, apiKey: process.env.ADP_API_KEY })
const model = process.env.ADP_EMBEDDINGS_MODEL || 'text-embedding-3-large'

const r = await client.embeddings.create({ model, input: ['hello', 'agentic ai'] })
console.log(r.data[0].embedding.length, r.data[1].embedding.length)
```
> **실무 팁**: 벡터 차원 수는 모델에 따라 다릅니다. 인덱스(FAISS/PGVector) 생성 시 동일모델로 일관성 있게 생성/조회하세요.

---

## 7) 툴콜(Function/Tools) — “모델이 함수를 부르게 하자”
흐름은 ① 모델이 도구 호출 제안 → ② 애플리케이션이 **실행** → ③ 결과를 **tool 메시지**로 재전달 → ④ 모델이 **최종 답변** 정리 입니다.
```json
{
  "type": "function",
  "function": {
    "name": "get_order_status",
    "description": "Lookup order status by order_number",
    "parameters": {
      "type": "object",
      "properties": {
        "order_number": { "type": "string", "description": "e.g., ORD-20251025-001" }
      },
      "required": ["order_number"]
    }
  }
}
```
```python
# samples/python/tools_roundtrip.py
import os, json, requests
base, key, model = os.getenv("ADP_BASE_URL"), os.getenv("ADP_API_KEY"), os.getenv("ADP_MODEL","deepseek-r1")
HEAD = {"Authorization": f"Bearer {key}", "Content-Type":"application/json"}

tools = [{
  "type":"function",
  "function":{
    "name":"get_order_status",
    "description":"Lookup order status by order_number",
    "parameters":{
      "type":"object",
      "properties":{"order_number":{"type":"string"}},
      "required":["order_number"]
    }
  }
}]

# 1) 모델이 도구 호출 제안
resp = requests.post(f"{base}/chat/completions", headers=HEAD, json={
  "model": model,
  "messages":[{"role":"user","content":"ORD-20251025-001 주문 상태 알려줘"}],
  "tools": tools,
  "tool_choice": "auto"
}).json()

choice = resp["choices"][0]
msg = choice["message"]
calls = msg.get("tool_calls", [])

# 2) 툴 실행(여기선 가짜 응답)
tool_results = []
for call in calls:
  if call["type"] == "function" and call["function"]["name"] == "get_order_status":
    args = json.loads(call["function"]["arguments"])
    tool_results.append({
      "role":"tool",
      "tool_call_id": call["id"],
      "content": json.dumps({"order_number": args["order_number"], "status":"delivered"})
    })

# 3) 모델에 결과 전달 → 최종 답변
final = requests.post(f"{base}/chat/completions", headers=HEAD, json={
  "model": model,
  "messages":[msg] + tool_results
}).json()
print(final["choices"][0]["message"]["content"])
```
> **디자인 팁**: 실제에선 이 도구가 내부 REST/DB를 호출합니다. 실패 시 재시도/대체 경로를 설계해 두세요.

---

## 8) 오류 처리 & 백오프 — “회복 탄력성”의 핵심 패턴
- **429 (rate limit)**: 지수 백오프 + **Jitter**를 적용해 동시성 폭주를 피합니다.
- **5xx (서버 오류)**: 멱등(idempotent)한 요청만 재시도합니다.
- **네트워크/타임아웃**: 명시적 타임아웃과 로깅을 추가합니다.
```python
import random, time, requests

def backoff_retry(request_fn, max_tries=5, base=0.5, cap=8.0):
  for i in range(max_tries):
    try:
      return request_fn()
    except requests.HTTPError as e:
      code = e.response.status_code
      if code not in (429,500,502,503,504):
        raise
    sleep = min(cap, base * (2 ** i)) + random.uniform(0, 0.2)
    time.sleep(sleep)
  raise RuntimeError("max retries exceeded")
```

---

## 9) 마무리 & 다음 단계
- 이제 **chat/stream/embeddings/tools**를 모두 다뤘습니다. 
- 다음 단계로 **KB(RAG) 결합**, **워크플로우/에이전트화**, **플러그인(MCP/OpenAPI)** 연동을 진행하세요. 
- 팀 내 공유를 위해 위 샘플을 `samples/python`, `samples/node` 경로에 파일로 만들어 커밋하면 실습 준비가 더 빨라집니다.

---

# 📗 ADP API/SDK Workshop (EN)

> This workshop focuses on **API/SDK only** (no Console). The goal is to help you understand *why* each step matters while giving copy‑paste runnable samples. Korean guide appears above; this is the full English version.
> 💡 Need the console-first walkthrough? Read `labs/01_quickstart_console/quick_start_from_console.md`.

## 0) What we’ll build
- Configure env vars, call **OpenAI‑compatible** **chat/embeddings** endpoints
- Handle **SSE streaming**
- Implement a full **tool‑calling** round trip
- Apply **error handling/backoff** patterns

## 1) Prereqs
- ADP enabled & model quota (e.g., `deepseek-r1`)
- Tools: `curl`, **Python 3.10+** or **Node 18+**
- `.env` at repo root:
  ```ini
  ADP_BASE_URL=https://api.lkeap.tencentcloud.com/v1
  ADP_API_KEY=YOUR_ADP_API_KEY
  ADP_MODEL=deepseek-r1
  # ADP_EMBEDDINGS_MODEL=text-embedding-3-large
  ```
- Load into your shell (macOS/Linux or PowerShell on Windows)

> **Common pitfalls**: missing `Bearer` prefix, wrong `/v1` path, misspelled model name.

## 2) First call with cURL
Non‑streaming request:
```bash
curl -s -X POST "$ADP_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $ADP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"${ADP_MODEL:-deepseek-r1}"'",
    "messages": [{"role":"user","content":"Give me 3 bullets on agentic AI."}]
  }' | jq -r '.choices[0].message.content'
```
**Streaming**: add `"stream": true` and read `data:` chunks until `[DONE]`.

## 3) Python — `requests` (non‑stream + SSE)
See `samples/python/chat_requests.py` in the KR section; it prints the final message content and an SSE stream progressively.

## 4) Python — OpenAI **official SDK**
Specify `base_url` to point at ADP, then call `chat.completions.create(...)`. Streaming is one `stream=True` flag away.

## 5) Node.js — OpenAI SDK (ESM)
Create a client with `{ baseURL, apiKey }`, then call `chat.completions.create(...)`. Use async iteration to consume the stream.

## 6) Embeddings
Turn text into vectors for similarity search; keep the same model across index & query. See KR/EN code blocks for Python/Node samples.

## 7) Tool calling (functions/tools)
Use a JSON schema to advertise functions. The model proposes a `tool_call`; you execute it; send the result back as a `tool` message; the model synthesizes the final answer. See `tools_roundtrip.py`.

## 8) Errors & backoff
Handle 429/5xx with exponential backoff + jitter; set explicit timeouts and log failures.

## 9) Wrap‑up & next steps
You now have chat, streaming, embeddings, tools, and resiliency patterns. Next, combine with **KB (RAG)**, orchestrate **workflows/agents**, and integrate **plugins (MCP/OpenAPI)**.
