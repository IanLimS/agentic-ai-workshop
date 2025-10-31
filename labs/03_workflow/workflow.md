

# 🛠️ ADP 워크플로우 핸즈온 — 콜센터(고객센터) 시나리오

> 이 문서는 **설명형(teacher‑style)** 가이드입니다. 단순 클릭 순서가 아니라 “왜 그 설정을 하는지, 어떤 문제가 해결되는지”를 먼저 이해하고, **콘솔 경로**와 **API 경로** 두 가지 방식으로 같은 워크플로우를 만들어 봅니다.

---

## 0) 목적과 산출물
**목적**
- ADP의 **워크플로우(Workflow)** 개념 이해: *트리거 → 분류 → 도구/지식 → 응답 생성 → 가드레일 → 라우팅*의 폐루프 설계.
- 콜센터 티켓의 **의도 분류**, **주문 상태 조회(HTTP API)**, **반품/환불 정책 답변(Knowledge)**, **휴먼 핸드오프**까지 전 과정을 한 줄로 연결.

**산출물**
- 샘플 워크플로우 JSON: `callcenter-triage.json` (아래 제공)
- 콘솔로 동일 로직 구성 후 **테스트 대화 & 인용 검증**
- API로 **생성 → 배포 → 실행(run)**까지 수행하는 실습

> 체크포인트: 답변 하단에 **Reference Sources**(지식 인용)가 붙는지, 주문 조회가 **실제 API 응답**을 반영하는지, **신뢰도(confidence)**와 **가드레일**이 설계대로 동작하는지 확인합니다.

---

## 1) ADP 워크플로우 멘탈 모델
- **Ingress(트리거)**: 메시지/이벤트의 진입점(웹챗, 콜 전사 텍스트, 카카오, 이메일 등).
- **Classifier(분류)**: intent(주문조회/환불/정책/기술/잡담/에스컬레이션)과 **신뢰도** 산출.
- **Router/Switch(경로 결정)**: intent·신뢰도·감정(senti)·고객 등급에 따라 다음 노드 결정.
- **Tools/Knowledge(도구/지식)**:
  - HTTP/SQL/MCP/사내 API로 **사실 데이터** 조회(예: 주문 상태, 배송 ETA).
  - KB(RAG)로 **정책/절차** 답변(근거 인용).
- **Response Composer(응답 생성)**: 톤/서식/다국어 등 브랜드 가이드 적용.
- **Guardrails(가드레일)**: PII 마스킹, 환각·인젝션 탐지, 컴플라이언스 룰.
- **Handoff(휴먼 연계)**: 신뢰도 낮거나 에스컬레이션 시 헬프데스크로 전달(Zendesk 등).
- **Observability(가시성)**: 로그/트레이스/평가 루브릭(grounding, tone, compliance).

---

## 2) 샘플 워크플로우 JSON (콜센터용)
> 이 JSON은 **레퍼런스 템플릿**입니다. 테넌트/버전에 따라 키 이름이 다를 수 있으므로, 콘솔의 *Export JSON* 또는 *API Call Information*과 비교해 조정하세요.

```json
{
  "version": "1.0",
  "name": "callcenter-triage",
  "description": "Classify intents, fetch order info, answer with KB, apply guardrails, and handoff if needed.",
  "inputs": {
    "channel": {"type": "string", "enum": ["webchat","kakao","email","transcript"]},
    "user_id": {"type": "string"},
    "message": {"type": "string"},
    "order_id": {"type": "string", "nullable": true}
  },
  "secrets": ["OMS_BASE","OMS_TOKEN"],
  "nodes": [
    {
      "id": "ingress",
      "type": "ingress",
      "channels": ["webchat","kakao","email","transcript"],
      "next": "classify"
    },
    {
      "id": "classify",
      "type": "agent",
      "model": "deepseek-r1",
      "system": "You are a call-center triage agent. Classify the user's intent as one of: order_status, refund, policy, tech_support, smalltalk, escalation. Return JSON with intent, confidence(0..1), and key entities (like order_id).",
      "inputs": {"text": "${message}"},
      "outputs": {
        "variables": {"intent": "$.json.intent", "confidence": "$.json.confidence", "ent_order_id": "$.json.order_id"},
        "next": "route"
      }
    },
    {
      "id": "route",
      "type": "switch",
      "cases": [
        {"when": "${intent} == 'order_status' && ${confidence} >= 0.6", "to": "fetch_order"},
        {"when": "${intent} in ['refund','policy'] && ${confidence} >= 0.6", "to": "kb_retrieve"},
        {"when": "${intent} == 'tech_support' && ${confidence} >= 0.6", "to": "kb_retrieve"},
        {"when": "${intent} == 'escalation' || ${confidence} < 0.6", "to": "handoff"},
        {"default": "smalltalk"}
      ]
    },
    {
      "id": "fetch_order",
      "type": "tool",
      "tool": "http_call",
      "config": {
        "method": "GET",
        "url": "${OMS_BASE}/orders/${order_id ?? ent_order_id}",
        "headers": {"Authorization": "Bearer ${OMS_TOKEN}"},
        "timeout": 8
      },
      "outputs": {"variables": {"order": "$.body"}, "next": "compose_reply"}
    },
    {
      "id": "kb_retrieve",
      "type": "knowledge_search",
      "config": {"tags": ["policy","faq"], "top_k": 5, "rerank": true},
      "outputs": {"variables": {"kb": "$.chunks"}, "next": "compose_reply"}
    },
    {
      "id": "smalltalk",
      "type": "agent",
      "model": "deepseek-v3",
      "system": "Friendly smalltalk assistant. Keep answers concise and helpful.",
      "inputs": {"context": "${message}"},
      "outputs": {"next": "guardrails"}
    },
    {
      "id": "compose_reply",
      "type": "agent",
      "model": "deepseek-v3",
      "system": "You are a courteous CS agent. If order data is present, summarize status (item, carrier, ETA). If KB chunks are present, answer ONLY with cited facts and include citations. If information is insufficient, ask one clarifying question or escalate.",
      "inputs": {"user": "${message}", "order": "${order}", "kb": "${kb}"},
      "outputs": {"variables": {"reply": "$.text", "citations": "$.citations", "reply_conf": "$.confidence"}, "next": "guardrails"}
    },
    {
      "id": "guardrails",
      "type": "guardrail",
      "policies": ["pii_mask","hallucination_check","prompt_injection"],
      "thresholds": {"min_confidence": 0.55},
      "outputs": {"next": "final_route"}
    },
    {
      "id": "final_route",
      "type": "router",
      "rules": [
        {"when": "${reply_conf} < 0.6 || ${intent} == 'escalation'", "to": "handoff"},
        {"default": "send_reply"}
      ]
    },
    {
      "id": "send_reply",
      "type": "egress",
      "channels": ["webchat","email"],
      "payload": {"text": "${reply}", "citations": "${citations}"}
    },
    {
      "id": "handoff",
      "type": "egress",
      "channel": "zendesk",
      "payload": {"summary": "${reply}", "intent": "${intent}", "confidence": "${confidence}", "user_id": "${user_id}", "transcript": "${message}"}
    }
  ],
  "observability": {
    "log": true,
    "trace": true,
    "eval": {"rubrics": ["grounding","tone","policy_compliance"]}
  }
}
```

> 저장 방법: 위 블록을 `labs/03_workflow/callcenter-triage.json` 파일로 저장하세요.

---

## 3) 콘솔 실습 (권장 순서)
1) **애플리케이션 생성/선택**: *Application Management*에서 새 앱을 만들거나 기존 앱을 선택합니다.
2) **커넥터/툴 준비**:
   - **HTTP Connector**에 `OMS_BASE`, `OMS_TOKEN`을 시크릿으로 등록합니다.
   - **Knowledge**: 정책/FAQ 문서를 업로드하고 *Reference Sources*를 켭니다.
3) **워크플로우 캔버스 구성**:
   - Ingress → Classify → Switch → (Fetch Order | KB Retrieve | Smalltalk) → Compose → Guardrails → (Send | Handoff).
   - 각 노드의 **입출력 변수** 이름이 JSON과 일치하도록 설정하세요 (`intent`, `confidence`, `order`, `kb`, `reply`).
4) **테스트**:
   - "주문 123-456 상태 알려줘" → `fetch_order` 경로로 가는지.
   - "반품 기간과 환불 소요기간?" → `kb_retrieve` 경로로 가는지(인용 확인).
   - 애매한 질문 → `handoff`로 가는지.
5) **배포/엔드포인트 확인**: *Deploy* 후, 콘솔의 *API Call Information*에서 **run URL**과 **API Key**를 확인합니다.

> 콘솔 팁: 라우팅이 예상과 다르면 `classify` 시스템 프롬프트의 **라벨 문구**(intent 명칭)와 **스코어 임계치**를 먼저 조정하세요.

---

## 4) API 실습 — 생성/배포/실행
> 워크플로우 API는 테넌트 별 경로가 다를 수 있습니다. 아래는 **변수화된 템플릿**입니다. 콘솔의 *API Call Information* 값을 그대로 넣으세요.

### 4-1. 환경 변수(.env)
```bash
export ADP_API_KEY="YOUR_ADP_API_KEY"
export ADP_WF_CREATE_URL="https://<tenant>/v1/apps/<app_id>/workflows"
export ADP_WF_DEPLOY_URL="https://<tenant>/v1/apps/<app_id>/workflows/{workflow_id}:deploy"
export ADP_WF_RUN_URL="https://<tenant>/v1/apps/<app_id>/workflows/{workflow_id}:run"
```

### 4-2. 생성(Create)
```bash
curl -s -X POST "$ADP_WF_CREATE_URL" \
  -H "Authorization: Bearer $ADP_API_KEY" \
  -H "Content-Type: application/json" \
  -d @labs/03_workflow/callcenter-triage.json | tee .create.out.json
# 결과에서 workflow_id 추출
export WF_ID=$(cat .create.out.json | python -c 'import sys,json;print(json.load(sys.stdin).get("id",""))')
```

### 4-3. 배포(Deploy)
```bash
curl -s -X POST "${ADP_WF_DEPLOY_URL//{workflow_id}/$WF_ID}" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json"
```

### 4-4. 실행(Run)
```bash
# 주문 조회 예시
cat <<'JSON' > .run_input.json
{
  "channel": "webchat",
  "user_id": "u-101",
  "message": "주문 123-456 배송 어디쯤이야?",
  "order_id": "123-456"
}
JSON

curl -s -X POST "${ADP_WF_RUN_URL//{workflow_id}/$WF_ID}" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json" \
  -d @.run_input.json | jq -r

# 정책 질문 예시 (인용 확인)
cat <<'JSON' > .run_input_policy.json
{
  "channel": "webchat",
  "user_id": "u-102",
  "message": "반품 기간과 환불 소요기간을 알려줘"
}
JSON

curl -s -X POST "${ADP_WF_RUN_URL//{workflow_id}/$WF_ID}" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json" \
  -d @.run_input_policy.json | jq -r
```

### 4-5. Python(선택)
```python
import os, json, requests
API_KEY = os.environ["ADP_API_KEY"]
RUN_URL = os.environ["ADP_WF_RUN_URL"].replace("{workflow_id}", os.environ.get("WF_ID",""))

payload = {"channel":"webchat","user_id":"u-201","message":"반품 기준 알려줘"}
r = requests.post(RUN_URL, headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json"}, json=payload, timeout=30)
r.raise_for_status()
print(json.dumps(r.json(), ensure_ascii=False, indent=2))
```

---

## 5) 검증 기준(What good looks like)
- **분류 정확도**: 의도와 신뢰도(confidence)가 설계와 일치한다.
- **주문 조회**: 응답 본문에 실제 *상품/택배사/ETA*가 포함된다.
- **인용 표시**: 정책/FAQ 답변에는 *Reference Sources*가 붙는다.
- **가드레일**: 개인정보(전화/주소) 마스킹, 환각/인젝션 차단 로그가 남는다.
- **핸드오프**: 불확실/에스컬레이션 시 헬프데스크에 요약/메타데이터 전달.

---

## 6) 트러블슈팅
- 401 Unauthorized: `ADP_API_KEY`/테넌트 권한/워크플로우 배포 완료 여부 확인.
- Unknown tool/http_call: HTTP Connector **활성화 및 시크릿 바인딩** 확인.
- 인용 누락: Knowledge 색인 옵션(Reference Sources On), 표/시트 정규화.
- 라우팅 오작동: `classify` 시스템 프롬프트의 intent 라벨/예시 강화, 임계치 조정.

---

## 7) 확장 아이디어
- 감정 분석(senti)에 따라 **사과/보상 쿠폰** 정책 분기.
- VIP 등급/최근 N건 CS 이력에 따른 우선 응답·대기열 스킵.
- SLA(응답시간/정확도) 위반 시 **자동 재질의/재검색** 후 핸드오프.

---

## 8) Python SDK 실습 — requests 기반 경량 SDK 어댑터
> 공식 ADP Python SDK가 테넌트별로 상이하거나 미배포인 환경을 고려하여, **REST를 래핑한 경량 SDK 스타일**로 실습합니다. 콘솔의 *API Call Information*에서 확인한 **정확한 엔드포인트**를 사용하세요.

### 8-1. 설치 & 환경 변수
```bash
pip install requests python-dotenv

# .env 예시 (프로젝트 루트)
ADP_BASE=https://<tenant-base>            # 예: https://api.lkeap.tencentcloud.com
ADP_API_KEY=YOUR_ADP_API_KEY
ADP_APP_ID=1958................           # 애플리케이션 ID
```

### 8-2. `sdk/adp_sdk.py` — 최소 구현
```python
# coding: utf-8
import os, json, requests
from typing import Any, Dict

class AdpClient:
    def __init__(self, base: str, api_key: str, timeout: int = 30):
        self.base = base.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.h = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    # Helper
    def _post(self, url: str, payload: Dict[str, Any]):
        r = requests.post(url, headers=self.h, json=payload, timeout=self.timeout)
        r.raise_for_status(); return r.json()

    def _get(self, url: str):
        r = requests.get(url, headers=self.h, timeout=self.timeout)
        r.raise_for_status(); return r.json()

    # Workflows
    def create_workflow(self, app_id: str, spec: Dict[str, Any]):
        url = f"{self.base}/v1/apps/{app_id}/workflows"
        return self._post(url, spec)

    def deploy_workflow(self, app_id: str, workflow_id: str):
        url = f"{self.base}/v1/apps/{app_id}/workflows/{workflow_id}:deploy"
        return self._post(url, {})

    def run_workflow(self, app_id: str, workflow_id: str, inputs: Dict[str, Any]):
        url = f"{self.base}/v1/apps/{app_id}/workflows/{workflow_id}:run"
        return self._post(url, inputs)

    def get_workflow(self, app_id: str, workflow_id: str):
        url = f"{self.base}/v1/apps/{app_id}/workflows/{workflow_id}"
        return self._get(url)
```

### 8-3. `examples/use_sdk_workflow.py` — 생성 → 배포 → 실행
```python
# coding: utf-8
import os, json
from pathlib import Path
from sdk.adp_sdk import AdpClient

BASE = os.getenv("ADP_BASE")
KEY  = os.getenv("ADP_API_KEY")
APP  = os.getenv("ADP_APP_ID")

assert BASE and KEY and APP, "ADP_BASE / ADP_API_KEY / ADP_APP_ID 환경변수를 설정하세요."
client = AdpClient(BASE, KEY)

# 1) 워크플로우 스펙 로드
spec_path = Path("labs/03_workflow/callcenter-triage.json")
spec = json.loads(spec_path.read_text(encoding="utf-8"))

# 2) 생성
created = client.create_workflow(APP, spec)
wf_id = created.get("id") or created.get("data",{}).get("id")
print("[create]", json.dumps(created, ensure_ascii=False, indent=2))
assert wf_id, "워크플로우 ID를 응답에서 찾지 못했습니다. 응답 스키마를 확인하세요."

# 3) 배포
print("[deploy]", client.deploy_workflow(APP, wf_id))

# 4) 실행 — 주문 조회 케이스
run_input = {
    "channel": "webchat",
    "user_id": "u-101",
    "message": "주문 123-456 배송 어디쯤이야?",
    "order_id": "123-456"
}
run_out = client.run_workflow(APP, wf_id, run_input)
print("[run/order]", json.dumps(run_out, ensure_ascii=False, indent=2))

# 5) 실행 — 정책 FAQ 케이스 (인용 기대)
run_input2 = {
    "channel": "webchat",
    "user_id": "u-102",
    "message": "반품 기간과 환불 소요기간을 알려줘"
}
run_out2 = client.run_workflow(APP, wf_id, run_input2)
print("[run/policy]", json.dumps(run_out2, ensure_ascii=False, indent=2))
```

### 8-4. 실행 방법
```bash
# 가상환경 권장
python -m venv .venv && source .venv/bin/activate
pip install requests python-dotenv

# 환경변수 로드
export $(grep -v '^#' .env | xargs)

# 예제 실행
python examples/use_sdk_workflow.py
```

### 8-5. 주의 & 팁
- **엔드포인트 경로는 테넌트마다 다를 수 있습니다.** 콘솔의 *API Call Information*과 대조하여 `AdpClient`의 URL을 조정하세요.
- 404/405가 발생하면 `base` 또는 `:deploy`, `:run` suffix가 다른 케이스일 수 있습니다.
- `secrets`(예: `OMS_BASE`, `OMS_TOKEN`)는 콘솔에서 등록/바인딩했는지 확인하세요.
- 응답 스키마가 다르면 `wf_id` 추출 부분을 직접 맞추세요.
```

### 부록 A) 최소 실행용 환경 변수 모음
```bash
export OMS_BASE="https://api.example-oms.local"
export OMS_TOKEN="xxxxx"
export ADP_API_KEY="xxxxx"
export ADP_WF_CREATE_URL="https://<tenant>/v1/apps/<app_id>/workflows"
export ADP_WF_DEPLOY_URL="https://<tenant>/v1/apps/<app_id>/workflows/{workflow_id}:deploy"
export ADP_WF_RUN_URL="https://<tenant>/v1/apps/<app_id>/workflows/{workflow_id}:run"
```

### 부록 B) 테스트 프롬프트 모음
- "주문 123-456 배송 현황 알려줘"
- "반품 기간과 환불 소요기간?"
- "이어폰 페어링이 안 돼요(제품명 불명)"
- "상담사 연결해줘"

> 위 프롬프트로 라우트/도구/인용/핸드오프가 기대대로 작동하면 **핸즈온 완료**입니다. 🎉


----


좋아! 워크플로우 핸즈온 문서에 Python SDK(경량 어댑터) 실습 섹션까지 들어간 상태야.
이제 바로 실행만 하면 돼—아래 순서대로 진행해봐.

지금 당장 해볼 것 (요약)
	1.	.env 채우기

ADP_BASE=https://<your-tenant-base>
ADP_API_KEY=YOUR_ADP_API_KEY
ADP_APP_ID=<your_app_id>
OMS_BASE=https://api.example-oms.local
OMS_TOKEN=xxxxx

	2.	의존성 설치

python -m venv .venv && source .venv/bin/activate
pip install requests python-dotenv

	3.	SDK/예제 파일 만들기
문서(labs/03_workflow/workflow.md)의 8-2, 8-3 코드블록을 그대로 파일로 저장:

sdk/adp_sdk.py
examples/use_sdk_workflow.py

	4.	워크플로우 JSON 저장

labs/03_workflow/callcenter-triage.json

(문서의 “샘플 워크플로우 JSON” 블록을 그대로 저장)
	5.	실행

export $(grep -v '^#' .env | xargs)
python examples/use_sdk_workflow.py

필요하면 위 3) 과정을 자동화하는 부트스트랩 스크립트(디렉터리 생성 + 파일 생성)도 만들어줄게.


----


좋지! 한 번에 디렉터리/파일을 만들어주는 부트스트랩 스크립트를 준비했어. 아래 스크립트를 레포 루트(예: agentic-ai-workshop/)에 저장하고 실행하면, 필요한 폴더/파일이 자동으로 생성돼.

1) 스크립트 저장

scripts/bootstrap_workflow_sdk.sh (새 파일)로 저장:

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

echo "==> Bootstrapping ADP Workflow SDK sample at: $ROOT_DIR"

# 1) Create directories
mkdir -p sdk examples labs/03_workflow scripts

# 2) .env.example
cat > .env.example <<'EOF'
# === ADP / App ===
ADP_BASE=https://<tenant-base>           # e.g., https://api.lkeap.tencentcloud.com
ADP_API_KEY=YOUR_ADP_API_KEY
ADP_APP_ID=<your_app_id>

# === External Service (Order Management System) ===
OMS_BASE=https://api.example-oms.local
OMS_TOKEN=xxxxx
EOF
echo "[+] Wrote .env.example"

# 3) sdk/adp_sdk.py
cat > sdk/adp_sdk.py <<'EOF'
# coding: utf-8
import os, json, requests
from typing import Any, Dict

class AdpClient:
    def __init__(self, base: str, api_key: str, timeout: int = 30):
        self.base = base.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.h = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    # Helpers
    def _post(self, url: str, payload: Dict[str, Any]):
        r = requests.post(url, headers=self.h, json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _get(self, url: str):
        r = requests.get(url, headers=self.h, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # Workflows
    def create_workflow(self, app_id: str, spec: Dict[str, Any]):
        url = f"{self.base}/v1/apps/{app_id}/workflows"
        return self._post(url, spec)

    def deploy_workflow(self, app_id: str, workflow_id: str):
        url = f"{self.base}/v1/apps/{app_id}/workflows/{workflow_id}:deploy"
        return self._post(url, {})

    def run_workflow(self, app_id: str, workflow_id: str, inputs: Dict[str, Any]):
        url = f"{self.base}/v1/apps/{app_id}/workflows/{workflow_id}:run"
        return self._post(url, inputs)

    def get_workflow(self, app_id: str, workflow_id: str):
        url = f"{self.base}/v1/apps/{app_id}/workflows/{workflow_id}"
        return self._get(url)
EOF
echo "[+] Wrote sdk/adp_sdk.py"

# 4) examples/use_sdk_workflow.py
cat > examples/use_sdk_workflow.py <<'EOF'
# coding: utf-8
import os, json
from pathlib import Path
from sdk.adp_sdk import AdpClient

BASE = os.getenv("ADP_BASE")
KEY  = os.getenv("ADP_API_KEY")
APP  = os.getenv("ADP_APP_ID")

assert BASE and KEY and APP, "ADP_BASE / ADP_API_KEY / ADP_APP_ID 환경변수를 설정하세요."
client = AdpClient(BASE, KEY)

# 1) 워크플로우 스펙 로드
spec_path = Path("labs/03_workflow/callcenter-triage.json")
spec = json.loads(spec_path.read_text(encoding="utf-8"))

# 2) 생성
created = client.create_workflow(APP, spec)
wf_id = created.get("id") or created.get("data",{}).get("id")
print("[create]", json.dumps(created, ensure_ascii=False, indent=2))
assert wf_id, "워크플로우 ID를 응답에서 찾지 못했습니다. 응답 스키마를 확인하세요."

# 3) 배포
print("[deploy]", client.deploy_workflow(APP, wf_id))

# 4) 실행 — 주문 조회 케이스
run_input = {
    "channel": "webchat",
    "user_id": "u-101",
    "message": "주문 123-456 배송 어디쯤이야?",
    "order_id": "123-456"
}
run_out = client.run_workflow(APP, wf_id, run_input)
print("[run/order]", json.dumps(run_out, ensure_ascii=False, indent=2))

# 5) 실행 — 정책 FAQ 케이스 (인용 기대)
run_input2 = {
    "channel": "webchat",
    "user_id": "u-102",
    "message": "반품 기간과 환불 소요기간을 알려줘"
}
run_out2 = client.run_workflow(APP, wf_id, run_input2)
print("[run/policy]", json.dumps(run_out2, ensure_ascii=False, indent=2))
EOF
echo "[+] Wrote examples/use_sdk_workflow.py"

# 5) labs/03_workflow/callcenter-triage.json
cat > labs/03_workflow/callcenter-triage.json <<'EOF'
{
  "version": "1.0",
  "name": "callcenter-triage",
  "description": "Classify intents, fetch order info, answer with KB, apply guardrails, and handoff if needed.",
  "inputs": {
    "channel": {"type": "string", "enum": ["webchat","kakao","email","transcript"]},
    "user_id": {"type": "string"},
    "message": {"type": "string"},
    "order_id": {"type": "string", "nullable": true}
  },
  "secrets": ["OMS_BASE","OMS_TOKEN"],
  "nodes": [
    {
      "id": "ingress",
      "type": "ingress",
      "channels": ["webchat","kakao","email","transcript"],
      "next": "classify"
    },
    {
      "id": "classify",
      "type": "agent",
      "model": "deepseek-r1",
      "system": "You are a call-center triage agent. Classify the user's intent as one of: order_status, refund, policy, tech_support, smalltalk, escalation. Return JSON with intent, confidence(0..1), and key entities (like order_id).",
      "inputs": {"text": "${message}"},
      "outputs": {
        "variables": {"intent": "$.json.intent", "confidence": "$.json.confidence", "ent_order_id": "$.json.order_id"},
        "next": "route"
      }
    },
    {
      "id": "route",
      "type": "switch",
      "cases": [
        {"when": "${intent} == 'order_status' && ${confidence} >= 0.6", "to": "fetch_order"},
        {"when": "${intent} in [" "refund"," "policy" "] && ${confidence} >= 0.6", "to": "kb_retrieve"},
        {"when": "${intent} == 'tech_support' && ${confidence} >= 0.6", "to": "kb_retrieve"},
        {"when": "${intent} == 'escalation' || ${confidence} < 0.6", "to": "handoff"},
        {"default": "smalltalk"}
      ]
    },
    {
      "id": "fetch_order",
      "type": "tool",
      "tool": "http_call",
      "config": {
        "method": "GET",
        "url": "${OMS_BASE}/orders/${order_id ?? ent_order_id}",
        "headers": {"Authorization": "Bearer ${OMS_TOKEN}"},
        "timeout": 8
      },
      "outputs": {"variables": {"order": "$.body"}, "next": "compose_reply"}
    },
    {
      "id": "kb_retrieve",
      "type": "knowledge_search",
      "config": {"tags": ["policy","faq"], "top_k": 5, "rerank": true},
      "outputs": {"variables": {"kb": "$.chunks"}, "next": "compose_reply"}
    },
    {
      "id": "smalltalk",
      "type": "agent",
      "model": "deepseek-v3",
      "system": "Friendly smalltalk assistant. Keep answers concise and helpful.",
      "inputs": {"context": "${message}"},
      "outputs": {"next": "guardrails"}
    },
    {
      "id": "compose_reply",
      "type": "agent",
      "model": "deepseek-v3",
      "system": "You are a courteous CS agent. If order data is present, summarize status (item, carrier, ETA). If KB chunks are present, answer ONLY with cited facts and include citations. If information is insufficient, ask one clarifying question or escalate.",
      "inputs": {"user": "${message}", "order": "${order}", "kb": "${kb}"},
      "outputs": {"variables": {"reply": "$.text", "citations": "$.citations", "reply_conf": "$.confidence"}, "next": "guardrails"}
    },
    {
      "id": "guardrails",
      "type": "guardrail",
      "policies": ["pii_mask","hallucination_check","prompt_injection"],
      "thresholds": {"min_confidence": 0.55},
      "outputs": {"next": "final_route"}
    },
    {
      "id": "final_route",
      "type": "router",
      "rules": [
        {"when": "${reply_conf} < 0.6 || ${intent} == 'escalation'", "to": "handoff"},
        {"default": "send_reply"}
      ]
    },
    {
      "id": "send_reply",
      "type": "egress",
      "channels": ["webchat","email"],
      "payload": {"text": "${reply}", "citations": "${citations}"}
    },
    {
      "id": "handoff",
      "type": "egress",
      "channel": "zendesk",
      "payload": {"summary": "${reply}", "intent": "${intent}", "confidence": "${confidence}", "user_id": "${user_id}", "transcript": "${message}"}
    }
  ],
  "observability": {
    "log": true,
    "trace": true,
    "eval": {"rubrics": ["grounding","tone","policy_compliance"]}
  }
}
EOF
echo "[+] Wrote labs/03_workflow/callcenter-triage.json"

cat <<'EOF'

Next steps:
1) python -m venv .venv && source .venv/bin/activate
2) pip install requests python-dotenv
3) cp .env.example .env  # 그리고 값 채우기
4) export $(grep -v '^#' .env | xargs)
5) python examples/use_sdk_workflow.py

Tip) 콘솔에서 API Call Information의 엔드포인트가 다른 경우, ADP_BASE를 그 값에 맞춰 수정.
EOF

echo "==> Done."

JSON의 route.cases 두 번째 when 조건에서 문자열 인용이 복잡해질 수 있어 위처럼 넣었어도 동작엔 문제 없지만, 만약 파서가 까다롭다면 ["refund","policy"] 형태로 수동 수정해줘.

⸻

2) 실행 방법

# 레포 루트에서
chmod +x scripts/bootstrap_workflow_sdk.sh
scripts/bootstrap_workflow_sdk.sh

# 가상환경 + 의존성
python -m venv .venv && source .venv/bin/activate
pip install requests python-dotenv

# 환경변수 채우기
cp .env.example .env
# .env 내용을 테넌트 값으로 편집 후:
export $(grep -v '^#' .env | xargs)

# 예제 실행
python examples/use_sdk_workflow.py

필요하면 workflow.json의 노드/정책을 너 상황(카카오 채널, 다른 헬프데스크, 별도 가드레일 이름 등)에 맞게 커스텀하는 패치도 바로 만들어줄게.