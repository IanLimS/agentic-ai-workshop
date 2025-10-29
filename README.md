
## 워크샵 개요
이 레포는 **ADP(TCADP)**를 이용해 **Agentic AI** 애플리케이션을 처음부터 출시/운영까지 만들어 보는 실습형 워크샵입니다. 콘솔에서 앱 생성 → 지식베이스 연결 → 워크플로(동기/비동기) 설계 → 외부 플러그인 연동 → OpenAI 호환 API 호출 → 릴리스 및 관측(토큰/지연/오류)까지 한 번에 다룹니다.

## 학습 목표
- ADP 애플리케이션 생성/설정 및 **Publish** 흐름 이해
- **지식베이스(File + Q&A)** 구성과 **출처(Reference Source)** 검증
- **싱글 워크플로**(LLM/툴/지식/조건/루프/비동기) 설계
- **플러그인(MCP/OpenAPI)** 등록 및 워크플로에서 호출
- **OpenAI 호환 API**(Python/Node)로 호출 및 스트리밍 처리
- 릴리스/버전/사용량/지연/오류 등 **운영 지표** 확인

## 일정(1일, 약 7.5시간)
1) 킥오프 & 환경 점검(15m)  
2) ADP 개요 & 아키텍처(45m)  
3) 콘솔 Quick Start(60m) – 생성→설정→디버그→**Publish**  
4) 지식베이스 딥다이브(75m) – 파일/Q&A, 하이브리드 검색, 레퍼런스  
5) 워크플로(동기/비동기)(70m) – 캔버스 노드/분기/백그라운드 잡  
6) 플러그인(MCP/OpenAPI)(45m) – 등록/권한/워크플로 호출  
7) 권한 & 레퍼런스(35m) – RBAC, 외부 레퍼런스 링크  
8) API(60m) – OpenAI 호환 호출/스트리밍/WS 다이얼로그  
9) 릴리스 & 관측(30m) – 버전/메트릭/트러블슈팅

> 2일형 옵션: 1–4 (Day1), 5–9 (Day2)

## 준비사항
- Tencent Cloud 계정 + **ADP 활성화** + 모델 쿼터(예: DeepSeek R1/V3 등)
- 로컬: Python 3.10+ 또는 Node 18+, `curl`, (옵션) Postman
- **API Key**는 `.env`에 보관(직접 하드코딩 금지)

`.env` 템플릿 생성:
```bash
cp setup/.env.example .env
# 키/엔드포인트 등 환경변수 입력
```

## 빠른 시작(콘솔)
1) **Create Application** → 2) 모델/출력 설정 → 3) **Debug** 테스트 → 4) **Publish** 후 공유 링크 확보(키 비노출 주의)

## 지식베이스
- PDF/Doc/CSV 업로드 또는 **Q&A** 추가 → 하이브리드/시맨틱 검색, 매칭 임계치/청킹 조정 → Debug에서 **Reference Source** 확인

## 워크플로(싱글 워크플로: 동기/비동기)
- LLM/Tool/Knowledge/Condition/Loop 노드 구성 → 동기 경로로 기본 챗 UX → **비동기** 분기를 추가해 장기 작업 처리(상태 폴링)

## 플러그인(MCP/OpenAPI)
- Postman/Swagger 스펙(`setup/postman_collection.json`) 등록 → 최소권한 키 설정 → 워크플로 Tool 노드에서 호출 후 Debug로 응답 확인

## 권한 & 외부 레퍼런스
- 역할 기반 접근제어(RBAC) 구성 → 필요 시 **External Reference Links** 활성화

## API – OpenAI 호환 호출
`.env` 예시:
```ini
ADP_BASE_URL=https://api.lkeap.tencentcloud.com/v1
ADP_API_KEY=YOUR_ADP_API_KEY
ADP_MODEL=deepseek-r1
```
Python/Node 샘플은 본문 예제를 그대로 사용하세요.

## 릴리스 & 관측
- Release 생성 → 요청/토큰/지연/에러 메트릭 확인 → Preview/Retry로 안전한 롤아웃

## 트러블슈팅
- 인용/레퍼런스 미출력: 매칭 임계치 하향/청킹 조정/재색인  
- 비동기 지연: 노드 타임아웃/백그라운드 한도 점검  
- 플러그인 실패: 인증/네트워크 이그레스/원본 오류 확인  
- 429/쿼터: 동시성 축소, 스트리밍 활용, 대용량 문서는 사전 배치 처리

## 스크린샷 캡처(요약)
- **1280×720**, OS 100% 스케일, 좌측 내비 + 페이지 타이틀 포함, 비밀정보는 반드시 마스킹  
- 파일명은 `assets/screenshots/01_...png` 형식으로 README와 동일하게 저장  
- (옵션) Playwright 스크립트로 반자동 캡처 가능 – README 하단 예제 참고

---

# 🧠 고급 실습 (Advanced Labs)

### 1) 데이터베이스를 임베딩해 지식베이스로 활용
두 가지 경로가 있습니다.
- **A. ADP가 내부 색인**: DB를 **CSV/Markdown**으로 덤프 → 콘솔 지식베이스에 업로드 → ADP가 인덱싱
- **B. 사전 임베딩(이식성)**: 외부 임베딩 모델로 청킹→벡터화→FAISS/PGVector 저장 + 텍스트 스냅샷을 ADP KB에 업로드해 **출처 근거** 제공

> ADP 테넌트에 `/embeddings` 엔드포인트가 없다면, **OpenAI 임베딩**을 사용하고, 대화/워크플로는 ADP를 그대로 사용해도 됩니다.

- 샘플: `samples/python/db_to_embeddings.py`  
  실행 전 환경변수 예시:
  ```bash
  # OpenAI 임베딩 예시
  export OPENAI_API_KEY=sk-...
  export OPENAI_EMBEDDINGS_MODEL=text-embedding-3-large
  # 또는 ADP OpenAI 호환 임베딩
  export ADP_BASE_URL=https://api.lkeap.tencentcloud.com/v1
  export ADP_API_KEY=xxx
  export ADP_EMBEDDINGS_MODEL=<tenant-embedding-model>
  python3 samples/python/db_to_embeddings.py
  ```
  완료 후 `artifacts/embeddings/products_snapshot.md`를 ADP KB에 업로드하고, **Reference Source**가 표시되는지 확인하세요.

### 2) 멀티‑에이전트(OpenAI + Claude) + 심판(Arbiter)
- OpenAI와 Claude가 각각 답변 → 심판(예: ADP의 DeepSeek R1)이 비교/통합한 **최종 응답** 생성  
- ADP 워크플로 캔버스에서는 **두 LLM 노드 → Judge 노드 → Answer 노드**로 구성

- 샘플: `samples/python/multi_agent_panel.py`  
  환경변수 예시:
  ```bash
  export OPENAI_API_KEY=sk-...
  export OPENAI_MODEL=gpt-4.1-mini
  export ANTHROPIC_API_KEY=sk-ant-...
  export ANTHROPIC_MODEL=claude-3.7-sonnet
  export ADP_BASE_URL=https://api.lkeap.tencentcloud.com/v1
  export ADP_API_KEY=xxx
  export ADP_MODEL=deepseek-r1
  python3 samples/python/multi_agent_panel.py
  ```

### 3) 가드레일(Guardrails) 구성
- **입력 가드**: PII/부적절 콘텐츠 필터(모더레이션 API + 정규식)  
- **툴 호출 가드**: 목적지 호스트 **허용목록(allowlist)** 기반 이그레스 제어  
- **출력 가드**: 정책 위반 키워드/패턴 최소 차단 + 경고 메시지 대체  
- ADP 워크플로 팁: **Pre‑processor**(입력 검사)와 **Post‑processor**(출력 필터)를 추가하고, 위반 시 *Reject→Answer*로 분기

- 샘플 파일:  
  `samples/python/guardrails.py` (가드 함수),  
  `samples/python/guardrails_demo.py` (데모 실행)

```bash
python3 samples/python/guardrails_demo.py
```

## 추가 아젠다(부록)
- **DB 임베딩** – 45분: export → chunk → embed → KB 업로드
- **멀티‑에이전트** – 60분: 패널 디베이트 → Judge 통합
- **가드레일** – 45분: 입력/툴/출력 레이어 및 워크플로 배선

**권장 실습 디렉터리 매핑**
```
08_db_embeddings/          # db_to_embeddings.py 실행 & KB 업로드
09_multi_agent_panel/      # multi_agent_panel.py 실행 & 워크플로 반영
10_guardrails/             # pre/post 프로세서 연결 & 차단/허용 시나리오 검증
```
---

# Agentic AI Workshop with ADP (Tencent Cloud Agent Development Platform)

Build an end‑to‑end **Agentic AI** application using **ADP (a.k.a. TCADP)**: create an application, add a knowledge base, design a workflow (sync/async), plug in external tools (MCP/OpenAPI), call it via an OpenAI‑compatible API, then release and observe usage.

> **Who is this for?** Cloud/AI architects and developers who want a practical, step‑by‑step path from *hello world* to a production‑ready agent.

---

## 📌 Learning Outcomes
By the end, you will be able to:
- Create and configure an ADP application (model, output, safety) and **publish** it.
- Attach a **Knowledge Base** (files + Q&A) and validate **source‑grounded** responses.
- Design a **single‑workflow** with LLM, tools, conditions, loops, and async tasks.
- Register a **plugin** (OpenAPI/MCP) and call external APIs from the workflow.
- Call ADP via **OpenAI‑compatible API** (Python/Node), including streaming.
- Release versions and read **usage/latency/token** analytics for operations.

---

## 🗺️ Agenda (1‑Day, ~7.5 hours)
1. **Kickoff & Environment Check (15m)**
2. **ADP Overview & Architecture (45m)**
3. **Console Quick Start (60m)** – create → configure → debug → **publish**
4. **Knowledge Base Deep Dive (75m)** – files/Q&A, hybrid retrieval, references
5. **Workflow (Sync & Async) (70m)** – canvas nodes, branching, background jobs
6. **Plugins (MCP/OpenAPI) (45m)** – register, secure, call in workflow
7. **Permissions & References (35m)** – RBAC, external reference links
8. **APIs (60m)** – OpenAI‑compatible calls, streaming, WS dialog
9. **Release & Observability (30m)** – versions, metrics, troubleshooting

> Two‑day option: run 1–4 on Day 1 and 5–9 on Day 2.

---

## 📂 Repository Layout
```
agentic-ai-workshop/
├─ README.md
├─ setup/
│  ├─ .env.example
│  └─ postman_collection.json
├─ labs/
│  ├─ 01_quickstart_console/
│  ├─ 02_knowledge_base/
│  ├─ 03_workflow_single_async/
│  ├─ 04_plugin_mcp/
│  ├─ 05_api_openai_python/
│  ├─ 06_permissions_rbac/
│  └─ 07_release_analytics/
├─ samples/
│  ├─ python/
│  │  ├─ openai_client_example.py
│  │  ├─ websocket_dialog_example.py
│  │  ├─ file_upload_qna_example.py
│  │  └─ tc3_signature_demo.py
│  └─ node/
│     └─ openai_client_example.mjs
└─ assets/
   └─ screenshots/  # place PNGs used in this README here
```

---

## ✅ Prerequisites
- Tencent Cloud account with **ADP** enabled and a model quota (e.g., DeepSeek R1/V3 or other supported models)
- Local: Python 3.10+ (or Node 18+), `curl`, Postman (optional)
- **API Key** for ADP (store in `.env`, never hard‑code)
- (Optional) Keys for any external plugins/APIs you plan to call

Create `.env` from the template:
```bash
cp setup/.env.example .env
# then edit .env and add your keys
```

---

## 🚀 Quick Start (Console)
1. **Create Application** in ADP Console.
2. **Configure** model, output formatting, and safety.
3. Open **Debug** and run a few prompts.
4. Click **Publish** → obtain the share URL (keep keys secret).

**Screenshots:**
- ![Create Application](assets/screenshots/01_create_app.png)
- ![Configure Model & Output](assets/screenshots/02_configure_model_output.png)
- ![Debug Panel](assets/screenshots/03_debug_panel.png)
- ![Publish & Share](assets/screenshots/04_publish_share.png)

---

## 📚 Knowledge Base (Files + Q&A)
1. Upload PDFs/Docs/CSVs or add **Q&A** pairs for precise answers.
2. Choose retrieval (semantic/hybrid), set matching thresholds, and chunking.
3. Test again in Debug; verify **Reference Sources** are attached to answers.

**Screenshots:**
- ![Upload Files](assets/screenshots/05_kb_upload.png)
- ![Q&A Builder](assets/screenshots/06_kb_qna.png)
- ![Reference Sources](assets/screenshots/07_kb_reference.png)

---

## 🔀 Workflow (Single Workflow: Sync & Async)
1. Open **Workflow Canvas** and add nodes: LLM, Tool, Knowledge, Condition, Loop.
2. Demonstrate **sync** path for chat UX.
3. Add an **async** branch for long‑running tasks; poll job status in UI.

**Screenshots:**
- ![Workflow Canvas](assets/screenshots/08_workflow_canvas.png)
- ![Nodes & Edges](assets/screenshots/09_workflow_nodes.png)
- ![Async Execution Trace](assets/screenshots/10_workflow_async_trace.png)

---

## 🔌 Plugins (MCP/OpenAPI)
1. Import a Postman/Swagger spec (see `setup/postman_collection.json`).
2. Register as **Plugin** in ADP; scope keys to least‑privilege.
3. Invoke from the workflow (Tool node) and inspect outputs in Debug.

**Screenshots:**
- ![Register Plugin](assets/screenshots/11_plugin_register.png)
- ![Call Plugin in Workflow](assets/screenshots/12_plugin_call.png)

---

## 👥 Permissions & External References
- Create roles and assign application access (RBAC).
- (Optional) Enable **External Reference Links** in answers when appropriate.

**Screenshots:**
- ![RBAC Settings](assets/screenshots/13_rbac.png)
- ![External References](assets/screenshots/14_external_refs.png)

---

## 🧪 APIs – OpenAI‑Compatible (Python & Node)
Set these in `.env` (example):
```ini
ADP_BASE_URL=https://api.lkeap.tencentcloud.com/v1
ADP_API_KEY=YOUR_ADP_API_KEY
ADP_MODEL=deepseek-r1
```

**Python (chat, streaming optional):**
```python
import os, sys, json
import requests

base_url = os.getenv("ADP_BASE_URL")
api_key  = os.getenv("ADP_API_KEY")
model    = os.getenv("ADP_MODEL", "deepseek-r1")

headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

def chat(messages, stream=False):
    url = f"{base_url}/chat/completions"
    payload = {"model": model, "messages": messages, "stream": stream}
    with requests.post(url, headers=headers, json=payload, stream=stream) as r:
        r.raise_for_status()
        if stream:
            for line in r.iter_lines():
                if not line: continue
                if line.startswith(b"data:"):
                    data = line[5:].strip()
                    if data == b"[DONE]": break
                    chunk = json.loads(data)
                    sys.stdout.write(chunk.get("choices", [{}])[0].get("delta", {}).get("content", ""))
                    sys.stdout.flush()
        else:
            print(r.json()["choices"][0]["message"]["content"]) 

if __name__ == "__main__":
    chat([{ "role":"user", "content":"Give me 3 bullets on agentic AI." }], stream=False)
```

**Node (ESM):**
```js
import 'dotenv/config'

const baseUrl = process.env.ADP_BASE_URL
const apiKey  = process.env.ADP_API_KEY
const model   = process.env.ADP_MODEL || 'deepseek-r1'

const res = await fetch(`${baseUrl}/chat/completions`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ model, messages: [{ role: 'user', content: 'List 3 agentic AI use cases.' }] })
})
const json = await res.json()
console.log(json.choices[0].message.content)
```

**WebSocket Dialog (outline):** see `samples/python/websocket_dialog_example.py` for session token → send/receive messages with incremental deltas.

---

## 📦 Release & Observability
- Create a **Release**, then view usage metrics: requests, tokens, latency, errors.
- Use **Preview/Retry** for safe rollout and quick fixes.

**Screenshots:**
- ![Create Release](assets/screenshots/15_release.png)
- ![Usage & Tokens](assets/screenshots/16_analytics_usage.png)

---

## 🧰 Troubleshooting
- **No citations/refs?** Lower match threshold or improve chunking; re‑index.
- **Async jobs stuck?** Check node timeouts and background execution limits.
- **Plugin fails?** Verify auth scope and network egress; inspect raw error in Debug.
- **429/Quota?** Reduce parallelism; enable streaming; batch long documents offline.

---

## 📝 License
MIT (or your organization’s license). See `LICENSE`.

---

## 🙌 Contributing
PRs and issues are welcome. Please redact keys/logs in screenshots.

---

# 🧠 Advanced Labs

This section extends the workshop with **database embeddings**, **multi‑agent orchestration** (OpenAI + Claude), and **guardrails**. Copy the code into `samples/python/` (or run directly) and adjust env vars.

## 1) Knowledge Embedding from a Database → Knowledge Base
There are two practical paths:

**A. Let ADP index it for you (simplest):**
1. Export DB rows to **CSV/Markdown**.
2. Upload the file(s) to the **Knowledge Base** (Console) → ADP performs internal indexing.

**B. Pre‑embed yourself (portable pipeline):**
Use an embedding model to vectorize chunks, store vectors (FAISS/PGVector), and optionally upload a text snapshot to ADP KB for source‑grounding.

> ⚠️ If your ADP tenant does not expose an `/embeddings` endpoint, use OpenAI (or your provider) for embeddings, while still using ADP for chat/workflows.

**Sample (Python): export rows → chunk → embed (ADP/OpenAI) → save vectors**
```python
# samples/python/db_to_embeddings.py
import os, csv, json, math, sqlite3, requests, hashlib
from pathlib import Path

# --- Config (env) ---
DB_URL = os.getenv('DB_URL', 'sqlite:///sample.db')  # e.g., postgresql://user:pw@host:5432/db
TABLE  = os.getenv('DB_TABLE', 'products')
OUTDIR = Path(os.getenv('OUTDIR', 'artifacts/embeddings'))
OUTDIR.mkdir(parents=True, exist_ok=True)

# Embeddings provider: ADP OpenAI‑compatible or OpenAI
BASE_URL = os.getenv('ADP_BASE_URL') or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
API_KEY  = os.getenv('ADP_API_KEY')  or os.getenv('OPENAI_API_KEY')
EMBED_MODEL = os.getenv('ADP_EMBEDDINGS_MODEL') or os.getenv('OPENAI_EMBEDDINGS_MODEL', 'text-embedding-3-large')

headers = { 'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json' }

def to_chunks(text, max_tokens=700):
    # naive splitter by length; swap with tiktoken for production
    CH = 3000
    return [text[i:i+CH] for i in range(0, len(text), CH)]

# --- Load rows from SQLite (for demo); adapt to Postgres/MySQL in your project ---
conn = sqlite3.connect('sample.db')
c = conn.cursor()
# demo schema if absent
c.execute(f"CREATE TABLE IF NOT EXISTS {TABLE} (id INTEGER PRIMARY KEY, name TEXT, description TEXT)")
conn.commit()

rows = list(c.execute(f"SELECT id, name, description FROM {TABLE}"))
if not rows:
    # seed demo data
    demo = [
        (1, 'Hydro Flask 21oz', 'Insulated stainless bottle; keeps cold 24h; BPA‑free.'),
        (2, 'Trail Running Shoes', 'Lightweight cushion; rock plate; suitable for 10‑30km.'),
        (3, 'Noise‑Canceling Headphones', 'ANC, transparency, 30h battery; BT 5.3; AAC/LDAC.'),
    ]
    c.executemany(f"INSERT INTO {TABLE} (id,name,description) VALUES (?,?,?)", demo)
    conn.commit()
    rows = demo

# --- Convert to Markdown & chunk ---
records = []
for rid, name, desc in rows:
    md = f"""## {name} (#{rid})\n\n{desc}\n\n"""
    for i, ch in enumerate(to_chunks(md)):
        rec_id = f"{rid}-{i}"
        records.append({"id":rec_id, "rid":rid, "name":name, "text":ch})

# --- Embed via OpenAI‑compatible endpoint ---
texts = [r['text'] for r in records]
payload = {"model": EMBED_MODEL, "input": texts}
resp = requests.post(f"{BASE_URL}/embeddings", headers=headers, json=payload)
resp.raise_for_status()
data = resp.json()['data']

vectors = []
for r, d in zip(records, data):
    vectors.append({
        'id': r['id'],
        'name': r['name'],
        'vector': d['embedding'],
        'text': r['text'],
    })

# Save portable JSONL for FAISS/PGVector import
OUT = OUTDIR / 'products_embeddings.jsonl'
with OUT.open('w', encoding='utf-8') as f:
    for v in vectors:
        f.write(json.dumps(v) + "\n")
print(f"Wrote {OUT}")

# Optional: also dump Markdown snapshot so you can upload to ADP KB for references
MD = OUTDIR / 'products_snapshot.md'
with MD.open('w', encoding='utf-8') as f:
    for r in records:
        f.write(r['text'] + "\n\n")
print(f"Wrote {MD} (upload this to ADP KB for source‑grounding)")
```

**Run:**
```bash
# .env additions (example)
export OPENAI_API_KEY=sk-...
export OPENAI_EMBEDDINGS_MODEL=text-embedding-3-large
# OR use ADP OpenAI‑compatible
export ADP_BASE_URL=https://api.lkeap.tencentcloud.com/v1
export ADP_API_KEY=xxx
export ADP_EMBEDDINGS_MODEL=<your-tenant-embedding-model>

python3 samples/python/db_to_embeddings.py
```

Then upload `artifacts/embeddings/products_snapshot.md` into the ADP Knowledge Base to test **Reference Sources**.

---

## 2) Multi‑Agent (OpenAI + Claude) with an Arbiter
We’ll collect answers from **OpenAI** and **Claude**, then ask an **arbiter** model (e.g., DeepSeek R1 on ADP) to reconcile into one response. You can mirror the same design on the ADP Workflow Canvas (two LLM nodes → judge node).

**Sample (Python): two models + judge**
```python
# samples/python/multi_agent_panel.py
import os, requests, json

# Providers
OPENAI_BASE = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
OPENAI_KEY  = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL= os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')

ANTH_BASE   = os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com/v1')
ANTH_KEY    = os.getenv('ANTHROPIC_API_KEY')
ANTH_MODEL  = os.getenv('ANTHROPIC_MODEL', 'claude-3.7-sonnet')

ADP_BASE    = os.getenv('ADP_BASE_URL')  # arbiter (OpenAI‑compatible)
ADP_KEY     = os.getenv('ADP_API_KEY')
ADP_MODEL   = os.getenv('ADP_MODEL', 'deepseek-r1')

q = os.getenv('QUESTION', 'Give me a 5‑step plan to add guardrails to a RAG agent.')

# OpenAI answer
r1 = requests.post(f"{OPENAI_BASE}/chat/completions",
    headers={'Authorization': f'Bearer {OPENAI_KEY}', 'Content-Type': 'application/json'},
    json={'model': OPENAI_MODEL, 'messages':[{'role':'user','content':q}]})
r1.raise_for_status(); a1 = r1.json()['choices'][0]['message']['content']

# Claude answer
r2 = requests.post(f"{ANTH_BASE}/messages",
    headers={'x-api-key': ANTH_KEY, 'anthropic-version':'2023-06-01', 'content-type':'application/json'},
    json={'model': ANTH_MODEL, 'max_tokens': 800, 'messages':[{'role':'user','content':q}]})
r2.raise_for_status(); a2 = ''.join([b.get('text','') for b in r2.json()['content']])

# Arbiter (ADP/OpenAI‑compatible): compare & synthesize
prompt = f"""
You are an impartial judge. Compare Answer A and Answer B to the same question.
- Identify points of agreement and conflict.
- Produce a single, concise, actionable final answer.

Question:\n{q}\n\nAnswer A (OpenAI):\n{a1}\n\nAnswer B (Claude):\n{a2}
"""
r3 = requests.post(f"{ADP_BASE}/chat/completions",
    headers={'Authorization': f'Bearer {ADP_KEY}', 'Content-Type': 'application/json'},
    json={'model': ADP_MODEL, 'messages':[{'role':'system','content':'You are a careful, concise arbiter.'},{'role':'user','content':prompt}]})
r3.raise_for_status(); final = r3.json()['choices'][0]['message']['content']

print("=== OpenAI ===\n", a1)
print("\n=== Claude ===\n", a2)
print("\n=== Final (Arbiter) ===\n", final)
```

**Env:**
```bash
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4.1-mini
export ANTHROPIC_API_KEY=sk-ant-...
export ANTHROPIC_MODEL=claude-3.7-sonnet
export ADP_BASE_URL=https://api.lkeap.tencentcloud.com/v1
export ADP_API_KEY=xxx
export ADP_MODEL=deepseek-r1
python3 samples/python/multi_agent_panel.py
```

> **ADP Workflow tip:** Create two LLM nodes (OpenAI & Claude plugin/tools) feeding a **Judge** node. Judge emits the final response to the **Answer** node. For traceability, attach intermediate outputs as references.

---

## 3) Guardrails (Input/Tool/Output)
Layered safety that works across providers.

**3.1 Input guard (PII + unsafe content)**
```python
# samples/python/guardrails.py (excerpt)
import os, re, requests

OPENAI_BASE = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
OPENAI_KEY  = os.getenv('OPENAI_API_KEY')

PII_RE = re.compile(r"(\b\d{3}-\d{2}-\d{4}\b|\b\d{6}-\d{7}\b|\b\d{16}\b)")  # SSN/KR‑RRN/CC very naive

class Block(Exception): pass

def guard_input(text: str):
    if PII_RE.search(text):
        raise Block('PII detected. Please redact sensitive numbers before proceeding.')
    # OpenAI moderation (swap with your provider)
    r = requests.post(f"{OPENAI_BASE}/moderations",
        headers={'Authorization': f'Bearer {OPENAI_KEY}', 'Content-Type':'application/json'},
        json={'model':'omni-moderation-latest','input': text})
    r.raise_for_status(); out = r.json()
    if out.get('results',[{}])[0].get('flagged'):
        raise Block('Content flagged by moderation policy.')
    return True
```

**3.2 Tool‑call allowlist (egress control)**
```python
ALLOWED_HOSTS = { 'api.example.com', 'api.github.com' }

def guard_tool(url: str):
    from urllib.parse import urlparse
    host = urlparse(url).hostname or ''
    if host not in ALLOWED_HOSTS:
        raise Block(f'Tool call blocked: host {host} not in allowlist')
    return True
```

**3.3 Output self‑check (policy conformance)**
```python
def guard_output(text: str):
    # lightweight checks; add regex/keywords as needed
    banned = ['how to build a bomb', 'bypass copyright']
    if any(b in text.lower() for b in banned):
        return 'Response redacted due to policy. Please rephrase your request.'
    return text
```

**3.4 Putting it together**
```python
# samples/python/guardrails_demo.py
from guardrails import guard_input, guard_tool, guard_output, Block

def run(query: str):
    try:
        guard_input(query)
        # before calling external tool
        guard_tool('https://api.github.com/search/repositories?q=agent')
        # ... call LLM & tools ... (omitted)
        raw = "Here is your safe answer."
        final = guard_output(raw)
        return final
    except Block as e:
        return f"Blocked: {e}"

if __name__ == '__main__':
    print(run('Find OSS repos about agentic ai. My SSN is 123-45-6789'))
```

> **ADP Workflow tip:** Put a **Pre‑processor** node that runs moderation/regex, then route to either *Reject* → Answer or to the main flow. Add a **Post‑processor** node that filters outputs and attaches policy notes.

---

## Agenda Add‑On
- **(New)** *Knowledge Embedding from DB* – 45m (export → chunk → embed → KB upload)
- **(New)** *Multi‑Agent (OpenAI + Claude + Arbiter)* – 60m (panel debate → judge)
- **(New)** *Guardrails* – 45m (input/tool/output layers; workflow wiring)

``` 
**Suggested labs mapping**
08_db_embeddings/          # run db_to_embeddings.py, upload snapshot to KB
09_multi_agent_panel/      # run multi_agent_panel.py and mirror in workflow
10_guardrails/             # wire pre/post processors; test blocked vs allowed
```

---
