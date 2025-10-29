

# ADP 퀵스타트 — 콘솔 & API (KR → EN 하단)

> 이 문서는 **ADP(Tencent Cloud Agent Development Platform)**에서 애플리케이션을 생성/설정/게시한 다음, **OpenAI 호환 API**로 호출해 보는 빠른 실습 가이드입니다. 먼저 **한글 가이드 전체**가 나오고, 문서 하단에 **영문 가이드 전체**가 이어집니다.

---

## 0) 목표 (Goals)
- ADP 애플리케이션 생성 후 **Publish**까지 완료
- (선택) 지식베이스를 연결하고 **출처(Reference Sources)**를 검증
- **OpenAI 호환 API**로 ADP를 호출 (curl, Python, Node)

---

## 1) 준비사항 (Prereqs)
- **ADP 활성화** 및 모델 쿼터가 있는 텐센트 클라우드 계정
- 로컬 도구: `curl`, **Python 3.10+** 또는 **Node 18+** (둘 중 하나만 있어도 됨)
- (옵션) Postman

> ⚠️ API Key는 저장소에 커밋하지 마세요. `.env` 파일과 비밀 관리자(Secrets Manager)를 사용하세요.

---

## 2) 환경 설정 (Environment Setup)
레포 루트에서 `.env` 템플릿을 복사하고 값을 채워 넣습니다.
```bash
# repo root에서
cp setup/.env.example .env
```
`.env` 편집 (예시):
```ini
ADP_BASE_URL=https://api.lkeap.tencentcloud.com/v1
ADP_API_KEY=YOUR_ADP_API_KEY
ADP_MODEL=deepseek-r1
```
셸에 환경변수 로드:
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

---

## 3) 콘솔 빠른 시작 (Console Quick Start)
1. ADP 콘솔에서 **Create Application**
2. **모델/출력 설정(Configure)** → **Debug**에서 프롬프트 테스트
3. **Publish** 클릭 → 공유 URL 보관

**참고 스크린샷**: `assets/screenshots/01_create_app.png`, `02_configure_model_output.png`, `03_debug_panel.png`, `04_publish_share.png`

---

## 4) (선택) 지식베이스 연결 (Knowledge Base)
- PDF/CSV/XLSX 또는 **Q&A** 업로드
- 검색 모드: **Hybrid** 권장(또는 Semantic)
- Debug에서 답변에 **Reference Sources**(출처 링크)가 포함되는지 확인

**참고 스크린샷**: `05_kb_upload.png`, `06_kb_qna.png`, `07_kb_reference.png`

---

## 5) API 호출 — curl
기본(논‑스트리밍) 예시:
```bash
curl -s -X POST "$ADP_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $ADP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"${ADP_MODEL:-deepseek-r1}"'",
    "messages": [
      {"role":"user","content":"에이전틱 AI에 대해 3가지 포인트를 알려줘."}
    ]
  }' | jq -r '.choices[0].message.content'
```

---

## 6) API 호출 — Python
`samples/python/quick_chat.py`로 저장:
```python
import os, sys, json, requests
base = os.getenv("ADP_BASE_URL"); key = os.getenv("ADP_API_KEY"); model = os.getenv("ADP_MODEL","deepseek-r1")
HEAD = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

# 1) 일반 호출
r = requests.post(f"{base}/chat/completions", headers=HEAD, json={
    "model": model,
    "messages": [{"role":"user","content":"에이전틱 AI의 3가지 활용사례를 알려줘."}]
})
r.raise_for_status(); print(r.json()["choices"][0]["message"]["content"]) 

# 2) 스트리밍(SSE)
with requests.post(f"{base}/chat/completions", headers=HEAD, json={
    "model": model,
    "stream": True,
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
실행:
```bash
python3 samples/python/quick_chat.py
```

---

## 7) API 호출 — Node (ESM)
`samples/node/quick_chat.mjs`로 저장:
```js
import 'dotenv/config'
const base = process.env.ADP_BASE_URL
const key  = process.env.ADP_API_KEY
const model= process.env.ADP_MODEL || 'deepseek-r1'

const res = await fetch(`${base}/chat/completions`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model,
    messages: [{ role: 'user', content: '에이전틱 AI의 대표 유스케이스 3가지를 말해줘.' }]
  })
})
const j = await res.json()
console.log(j.choices?.[0]?.message?.content)
```
실행:
```bash
node samples/node/quick_chat.mjs
```

---

## 8) (선택) WebSocket 대화
테넌트에서 대화용 WebSocket을 제공하는 경우, 세션 토큰 발급 후 **증분(delta)**를 수신할 수 있습니다. 레포의 `samples/python/websocket_dialog_example.py`를 참고하세요.

---

## 9) 문제 해결 (Troubleshooting)
- **401/403**: API Key 불일치 또는 `Bearer` 접두사 누락
- **404**: Base URL 경로(`/v1`) 불일치, 엔드포인트 미활성화
- **429**: 레이트 리밋 → 동시성 축소, 스트리밍 사용
- **인용 없음**: 매칭 임계치를 낮추거나 KB 재색인
- 네트워크 정책(프록시/VPC), 모델명/엔드포인트를 `.env`로 재확인

---

## 10) 다음 실습 (Next Labs)
- **02_knowledge_base**: 파일/Q&A 업로드와 인용 검증
- **03_workflow_single_async**: 동기 vs 비동기 분기 설계
- **04_plugin_mcp**: OpenAPI/MCP 플러그인 등록 후 Tool 노드 호출


---

# ADP Quick Start — Console & API (EN)

> Build and test a working **Agentic AI** app on **ADP** (Tencent Cloud Agent Development Platform), then call it via an **OpenAI‑compatible API**. This is the English version (the Korean version is above).

---

## 0) Goals
- Create and **Publish** an ADP application
- (Optional) Attach a Knowledge Base and validate **Reference Sources**
- Call ADP via **OpenAI‑compatible** APIs (curl, Python, Node)

---

## 1) Prereqs
- Tencent Cloud account with **ADP** enabled and model quota
- Local tools: `curl`, **Python 3.10+** or **Node 18+**
- (Optional) Postman

> ⚠️ Never commit API keys. Use `.env` and a secrets manager.

---

## 2) Environment Setup
From repo root:
```bash
cp setup/.env.example .env
```
Edit `.env`:
```ini
ADP_BASE_URL=https://api.lkeap.tencentcloud.com/v1
ADP_API_KEY=YOUR_ADP_API_KEY
ADP_MODEL=deepseek-r1
```
Export envs:
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

---

## 3) Console Quick Start
1. **Create Application** in ADP Console
2. **Configure** model & output; test prompts in **Debug**
3. Click **Publish** and keep the share URL

**Screenshots**: `assets/screenshots/01_create_app.png`, `02_configure_model_output.png`, `03_debug_panel.png`, `04_publish_share.png`

---

## 4) (Optional) Knowledge Base
- Upload PDFs/CSVs/XLSX or **Q&A**
- Retrieval: **Hybrid** recommended (or Semantic)
- In Debug, verify answers include **Reference Sources**

**Screenshots**: `05_kb_upload.png`, `06_kb_qna.png`, `07_kb_reference.png`

---

## 5) API — curl
Minimal, non‑streaming:
```bash
curl -s -X POST "$ADP_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $ADP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"${ADP_MODEL:-deepseek-r1}"'",
    "messages": [
      {"role":"user","content":"Give me 3 bullets on agentic AI."}
    ]
  }' | jq -r '.choices[0].message.content'
```

---

## 6) API — Python
Save as `samples/python/quick_chat.py`:
```python
import os, sys, json, requests
base = os.getenv("ADP_BASE_URL"); key = os.getenv("ADP_API_KEY"); model = os.getenv("ADP_MODEL","deepseek-r1")
HEAD = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

# Non‑streaming
r = requests.post(f"{base}/chat/completions", headers=HEAD, json={
    "model": model,
    "messages": [{"role":"user","content":"List 3 agentic AI use cases."}]
})
r.raise_for_status(); print(r.json()["choices"][0]["message"]["content"]) 

# Streaming (SSE)
with requests.post(f"{base}/chat/completions", headers=HEAD, json={
    "model": model,
    "stream": True,
    "messages": [{"role":"user","content":"Stream a short haiku about agents."}]
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
Run:
```bash
python3 samples/python/quick_chat.py
```

---

## 7) API — Node (ESM)
Save as `samples/node/quick_chat.mjs`:
```js
import 'dotenv/config'
const base = process.env.ADP_BASE_URL
const key  = process.env.ADP_API_KEY
const model= process.env.ADP_MODEL || 'deepseek-r1'

const res = await fetch(`${base}/chat/completions`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model,
    messages: [{ role: 'user', content: 'Give me 3 bullets on agentic AI.' }]
  })
})
const j = await res.json()
console.log(j.choices?.[0]?.message?.content)
```
Run:
```bash
node samples/node/quick_chat.mjs
```

---

## 8) (Optional) WebSocket Dialog
If your tenant exposes a dialog WS, use a session token and stream deltas. See `samples/python/websocket_dialog_example.py` in the repo.

---

## 9) Troubleshooting
- **401/403**: wrong API key or missing `Bearer` prefix
- **404**: base URL path mismatch (`/v1`), or endpoint disabled
- **429**: rate‑limited → reduce concurrency, enable streaming
- **No citations**: lower match threshold or re‑index KB

---

## 10) Next labs
- **02_knowledge_base**: file/Q&A upload and citations
- **03_workflow_single_async**: sync vs async branches
- **04_plugin_mcp**: register OpenAPI/MCP plugin and call from Tool node
