# 🤝 ADP Multi‑Agent 핸즈온 — DeepSeek + Claude + OpenAI로 한 문제를 푸는 방법

> 이 문서는 **설명형(teacher‑style)** 가이드입니다. 동일한 사용자 질문을 **세 개의 에이전트(DeepSeek, Claude, OpenAI)** 가 각자 답하고, **종합 에이전트**가 이를 비교·융합해 최종 답을 내는 멀티‑에이전트 패턴을 콘솔·API·Python SDK로 차례대로 실습합니다.

---

## 0) 목표와 산출물
**목표**
- ADP의 **Multi‑Agent 오케스트레이션** 개념 이해: *Fan‑out(병렬/순차) → Gather → Synthesize → Guardrail → Egress*.
- **최저가 모델 조합**(권장):
  - DeepSeek: `deepseek-r1` (reasoning)
  - Claude: `claude-3-haiku` (저가/속도용)
  - OpenAI: `gpt-4o-mini` (저가/범용)
- 동일 질문에 대해 세 모델의 관점을 취합하고 **일관성/근거**를 점검하는 방식 학습.

**산출물**
- 샘플 워크플로우 JSON: `multi-agent-roundtable.json`
- 콘솔로 구성/테스트, API로 **생성→배포→실행**, Python SDK(경량 어댑터)로 **end‑to‑end 실행** 스크립트

> 체크포인트: 각 에이전트의 **중간 답변**이 로깅·수집되고, 최종 답변에 **근거(인용)** 와 **불일치 해소 전략**이 반영되는지 확인합니다.

---

## 1) 멀티‑에이전트 멘탈 모델
- **Round‑table(라운드테이블)**: 여러 전문가가 같은 질문에 답 → **조정자(synthesizer)** 가 합의·타협.
- **Router**: 질문 유형/제약(속도/비용/정확성)에 따라 특정 모델만 선택.
- **Self‑consistency**: 서로 다른 경로의 답을 비교해 공통 핵심을 채택.
- **Guardrails**: 금칙어/PII/환각 탐지 후 재시도 또는 휴먼 핸드오프.

본 실습은 가장 이해가 쉬운 **Round‑table + Synthesizer** 패턴을 사용합니다.

---

## 2) 샘플 워크플로우 JSON — `multi-agent-roundtable.json`
> 테넌트/버전에 따라 스키마가 다를 수 있습니다. **콘솔의 Export JSON** 또는 **API Call Information**과 대조해 키 이름을 조정하세요.

```json
{
  "version": "1.0",
  "name": "multi-agent-roundtable",
  "description": "Ask DeepSeek, Claude, OpenAI in sequence; then synthesize with guardrails and respond.",
  "inputs": {
    "channel": {"type": "string", "enum": ["webchat","kakao","email","api"]},
    "user_id": {"type": "string"},
    "message": {"type": "string"}
  },
  "secrets": ["OPENAI_API_KEY","ANTHROPIC_API_KEY"],
  "nodes": [
    {"id": "ingress", "type": "ingress", "channels": ["webchat","kakao","email","api"], "next": "ask_deepseek"},

    {"id": "ask_deepseek", "type": "agent", "provider": "adp", "model": "deepseek-r1",
     "system": "You are a reasoning specialist. Provide a concise, step-by-step answer. State assumptions and uncertainties.",
     "inputs": {"question": "${message}"},
     "outputs": {"variables": {"ans_ds": "$.text", "trace_ds": "$.reasoning"}, "next": "ask_claude"}
    },

    {"id": "ask_claude", "type": "agent", "provider": "anthropic", "model": "claude-3-haiku",
     "system": "You are a fast, safety-conscious assistant. Provide a short, precise answer with bullet points if helpful.",
     "inputs": {"question": "${message}"},
     "auth": {"api_key_secret": "ANTHROPIC_API_KEY"},
     "outputs": {"variables": {"ans_claude": "$.text"}, "next": "ask_openai"}
    },

    {"id": "ask_openai", "type": "agent", "provider": "openai", "model": "gpt-4o-mini",
     "system": "You are a generalist who balances brevity and clarity. Include one-sentence rationale if non-trivial.",
     "inputs": {"question": "${message}"},
     "auth": {"api_key_secret": "OPENAI_API_KEY"},
     "outputs": {"variables": {"ans_oai": "$.text"}, "next": "synthesize"}
    },

    {"id": "synthesize", "type": "agent", "provider": "adp", "model": "deepseek-v3",
     "system": "You are a synthesizer. Read three candidates (DeepSeek, Claude, OpenAI). Produce a single, correct, citation-friendly answer.\nRules:\n1) If two or more agree, adopt consensus; else explain trade-offs.\n2) Prefer verifiable statements; if unsure, ask one clarifying question.\n3) Return JSON: {answer:string, picked:string, conflicts:[string]}",
     "inputs": {"ds": "${ans_ds}", "cl": "${ans_claude}", "oai": "${ans_oai}", "user": "${message}"},
     "outputs": {"variables": {"merged": "$.json.answer", "picked": "$.json.picked", "conflicts": "$.json.conflicts"}, "next": "guardrails"}
    },

    {"id": "guardrails", "type": "guardrail", "policies": ["pii_mask","hallucination_check"],
     "outputs": {"next": "egress"}
    },

    {"id": "egress", "type": "egress", "channels": ["webchat","email"],
     "payload": {"text": "${merged}", "meta": {"picked": "${picked}", "conflicts": "${conflicts}"}}
    }
  ],
  "observability": {"log": true, "trace": true}
}
```

> 병렬 실행이 가능한 테넌트는 `ask_deepseek/ask_claude/ask_openai`를 `type: "parallel"` 노드로 묶어 **동시에** 실행하고, `join` 노드에서 합쳐도 됩니다. 본 예시는 **호환성**을 위해 순차로 작성했습니다.

---

## 3) 콘솔 실습 (권장 순서)
1) **모델/프로바이더 시크릿 등록**
   - Settings → *Secrets*: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
   - 필요 시 Provider Connector에서 OpenAI/Anthropic를 활성화합니다.
2) **지식(선택)**: 정책/FAQ가 있다면 업로드하고 *Reference Sources*를 켭니다.
3) **워크플로우 캔버스 구성**
   - Ingress → DeepSeek → Claude → OpenAI → Synthesize → Guardrails → Egress
   - 각 에이전트 노드의 **provider/model**와 **auth(시크릿 바인딩)** 를 설정합니다.
4) **테스트**
   - "반품 기간과 환불 소요기간 알려줘" / "주문 123-456 배송 어디쯤?" / "USB‑C 모니터 듀얼 연결 방법?" 등으로 비교.
   - Observability에서 **ans_ds / ans_claude / ans_oai** 변수와 합성 결과를 확인하세요.
5) **배포 & 엔드포인트 확인**: *Deploy* 후 API 호출 정보를 기록합니다.

> 팁: 비용 민감 시 **OpenAI/Claude는 미니 모델**, DeepSeek는 `-r1` 등 저가 라인으로. 토큰 상한/온도도 낮춰서 설정하세요.

---

## 4) API 실습 — 생성/배포/실행
> 경로는 테넌트마다 다릅니다. **콘솔의 API Call Information**을 기준으로 입력하세요.

### 4‑1. 환경 변수(.env)
```bash
export ADP_API_KEY="YOUR_ADP_API_KEY"
export ADP_BASE="https://<tenant-base>"
export ADP_APP_ID="<your_app_id>"
export ADP_WF_CREATE_URL="$ADP_BASE/v1/apps/$ADP_APP_ID/workflows"
export ADP_WF_DEPLOY_URL="$ADP_BASE/v1/apps/$ADP_APP_ID/workflows/{workflow_id}:deploy"
export ADP_WF_RUN_URL="$ADP_BASE/v1/apps/$ADP_APP_ID/workflows/{workflow_id}:run"
```

### 4‑2. 생성(Create)
```bash
# 파일 저장: labs/09_multi_agents/multi-agent-roundtable.json
curl -s -X POST "$ADP_WF_CREATE_URL" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json" \
  -d @labs/09_multi_agents/multi-agent-roundtable.json | tee .ma.create.out.json
export MA_WF_ID=$(cat .ma.create.out.json | python -c 'import sys,json;print(json.load(sys.stdin).get("id",""))')
```

### 4‑3. 배포(Deploy)
```bash
curl -s -X POST "${ADP_WF_DEPLOY_URL//{workflow_id}/$MA_WF_ID}" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type": "application/json" -d '{}'
```

### 4‑4. 실행(Run)
```bash
cat <<'JSON' > .ma.run.json
{
  "channel": "webchat",
  "user_id": "u-999",
  "message": "반품 기간과 환불 소요기간 알려줘"
}
JSON

curl -s -X POST "${ADP_WF_RUN_URL//{workflow_id}/$MA_WF_ID}" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json" \
  -d @.ma.run.json | jq -r
```

---

## 5) Python SDK 실습 — 경량 AdpClient 재사용
> 이전 랩에서 만든 `AdpClient`(create/deploy/run)를 그대로 사용합니다.

### 5‑1. 예제 스크립트 `examples/use_sdk_multiagent.py`
```python
# coding: utf-8
import os, json
from pathlib import Path
from sdk.adp_sdk import AdpClient

BASE = os.getenv("ADP_BASE"); KEY = os.getenv("ADP_API_KEY"); APP = os.getenv("ADP_APP_ID")
assert BASE and KEY and APP, "ADP_BASE / ADP_API_KEY / ADP_APP_ID 환경변수를 설정하세요."
client = AdpClient(BASE, KEY)

spec_path = Path("labs/09_multi_agents/multi-agent-roundtable.json")
spec = json.loads(spec_path.read_text(encoding="utf-8"))

# 1) 생성
created = client.create_workflow(APP, spec)
wf_id = created.get("id") or created.get("data",{}).get("id")
print("[create]", json.dumps(created, ensure_ascii=False, indent=2))
assert wf_id

# 2) 배포
print("[deploy]", client.deploy_workflow(APP, wf_id))

# 3) 실행
run_input = {"channel":"webchat","user_id":"u-999","message":"USB-C 모니터 듀얼 연결 방법?"}
out = client.run_workflow(APP, wf_id, run_input)
print("[run]", json.dumps(out, ensure_ascii=False, indent=2))
```

### 5‑2. 실행
```bash
python -m venv .venv && source .venv/bin/activate
pip install requests python-dotenv
export $(grep -v '^#' .env | xargs)
python examples/use_sdk_multiagent.py
```

---

## 6) 품질/비용 최적화 팁
- **라벨/프롬프트 표준화**: 세 에이전트의 지시문을 간결·동일하게 유지 → 합성 난이도↓.
- **토큰 상한**: 미니 모델에선 `max_tokens`를 낮추고, 합성 단계에만 충분한 토큰 허용.
- **Fail‑open vs Fail‑closed**: 한 에이전트 실패 시 합성에서 제외하거나 재시도 1회.
- **지식 인용**: 필요 시 `knowledge_search` 노드를 **각 에이전트 앞**에 추가해 동일 근거를 제공.

---

## 7) 트러블슈팅
- 401/403: OpenAI/Anthropic 시크릿 바인딩 확인, 테넌트 권한.
- 404/스키마 오류: 워크플로우 키 이름(`provider`,`auth`)이 테넌트 스펙과 다른 경우.
- 응답 누락: 중간 변수(`ans_ds`,`ans_claude`,`ans_oai`)가 캡처되는지 Observability에서 확인.
- 비용 폭주: 순차 대신 **Router**로 특정 질문만 다중 에이전트로 보내는 하이브리드 구성 권장.

---

### 부록 A) 환경 변수 예시
```bash
# ADP
export ADP_BASE="https://<tenant-base>"
export ADP_API_KEY="YOUR_ADP_API_KEY"
export ADP_APP_ID="<your_app_id>"

# Providers
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 부록 B) 테스트 프롬프트
- "반품 기간과 환불 소요기간 알려줘" (정책/FAQ)
- "주문 123-456 배송 어디쯤이야?" (사실 조회)
- "USB‑C 모니터로 노트북 듀얼 연결하려면?" (절차/트러블슈팅)

> 위 프롬프트로 세 에이전트의 관점이 수집되고, Synthesizer가 일관된 답을 만들면 **핸즈온 완료**입니다. 🎉
