

# 🛡️ ADP Guardrails & Human‑in‑the‑Loop(HITL) 핸즈온 — 멀티에이전트(DeepSeek + Claude + OpenAI)

> 이 문서는 **설명형(teacher‑style)** 가이드입니다. 동일한 질문에 대해 **DeepSeek, Claude, OpenAI**가 각각 답하고, **합성 에이전트**가 취합한 뒤 **가드레일**을 통과시키고, 필요 시 **휴먼인더루프(HITL)**로 결재/수정/거부를 거쳐 최종 응답을 내보내는 **엔드‑투‑엔드 워크플로우**를 콘솔 · API · Python SDK로 실습합니다.

---

## 0) 목표와 산출물
**목표**
- ADP에서 **Guardrails**를 설계/적용하는 방법(정책, 임계치, 액션)을 이해합니다.
- **Human‑in‑the‑Loop(HITL)**로 사람이 중간에 개입해 승인/수정/거부할 수 있는 체계를 만듭니다.
- **멀티에이전트**(DeepSeek + Claude + OpenAI)로 각각의 관점을 모은 뒤, 합성→가드레일→HITL→출력을 잇는 폐루프를 구성합니다.

**산출물**
- 샘플 워크플로우 JSON: `multi-agent-guardrails-hitl.json`
- 콘솔 핸즈온: 정책 구성, HITL 큐/채널 연결, 라우팅 점검
- API 핸즈온: 생성→배포→실행(run) 및 **HITL 승인/거부 API** 호출
- Python SDK(경량 어댑터) 핸즈온: create/deploy/run + **human_decide()** 예제

> 체크포인트: (1) 가드레일이 실제로 **차단/마스킹/재질의**를 수행하는지, (2) 위험/신뢰도 조건에서 **HITL로 전환**되는지, (3) 사람이 승인/수정하면 그 결과가 **최종 응답**으로 반영되는지.

---

## 1) 가드레일 & HITL 멘탈 모델
### 1‑1. Guardrails가 막는 것
- **PII/민감정보** 유출: 전화/주소/주민번호/카드 등 → **마스킹** 또는 **승인 필요**로 전환
- **프롬프트 인젝션/탈옥**: 모델 권한 밖의 작업 유도 → **차단** 또는 **재질의**
- **유해/독성/차별 표현**: 정책에 따라 **거부** 또는 **완화된 톤 재생성**
- **환각/비근거 주장**: **근거 필요/인용 강제**, 불확실하면 **질의 보강**

### 1‑2. Guardrails 구성 요소
- **정책(Policies)**: 예) `pii_mask`, `toxicity`, `prompt_injection`, `hallucination_check`
- **임계치(Thresholds)**: 위험 점수/신뢰도 기준(예: `min_confidence: 0.6`)
- **액션(Actions)**: `allow` / `sanitize(mask)` / `requery` / `block` / `route_to_human`
- **로깅 & 증적**: 차단 사유, 탐지 결과, 원본/정제본 쌍 저장

### 1‑3. Human‑in‑the‑Loop(HITL)
- **트리거**: (a) 위험도↑, (b) 신뢰도↓, (c) 특정 의도(법률/의학/금융), (d) 고객 등급/클레임 유형
- **작업(Tasks)**: 승인/거절, 텍스트 수정, 라벨링(위험카테고리/정확성), 코멘트
- **채널**: 콘솔 대기열, **Zendesk/Jira/Slack** 같은 외부 툴 연계
- **동기/비동기**: 응답을 **대기(wait)** 하거나, 임시 응답 후 **사후 업데이트**

---

## 2) 샘플 워크플로우 JSON — `multi-agent-guardrails-hitl.json`
> 테넌트에 따라 스키마가 다를 수 있습니다. **콘솔의 Export JSON** 또는 **API Call Information**과 대조해 키 이름을 조정하세요.

```json
{
  "version": "1.0",
  "name": "multi-agent-guardrails-hitl",
  "description": "Ask DeepSeek, Claude, OpenAI → Synthesize → Guardrails → Human review if risky → Final output.",
  "inputs": {
    "channel": {"type": "string", "enum": ["webchat","kakao","email","api"]},
    "user_id": {"type": "string"},
    "message": {"type": "string"}
  },
  "secrets": ["OPENAI_API_KEY","ANTHROPIC_API_KEY"],
  "nodes": [
    {"id": "ingress", "type": "ingress", "channels": ["webchat","kakao","email","api"], "next": "ask_deepseek"},

    {"id": "ask_deepseek", "type": "agent", "provider": "adp", "model": "deepseek-r1",
     "system": "Reasoning specialist. Provide concise, step-by-step with assumptions.",
     "inputs": {"question": "${message}"},
     "outputs": {"variables": {"ans_ds": "$.text", "trace_ds": "$.reasoning"}, "next": "ask_claude"}
    },

    {"id": "ask_claude", "type": "agent", "provider": "anthropic", "model": "claude-3-haiku",
     "system": "Fast and safe. Short, precise, bullet points if helpful.",
     "inputs": {"question": "${message}"},
     "auth": {"api_key_secret": "ANTHROPIC_API_KEY"},
     "outputs": {"variables": {"ans_claude": "$.text"}, "next": "ask_openai"}
    },

    {"id": "ask_openai", "type": "agent", "provider": "openai", "model": "gpt-4o-mini",
     "system": "Generalist. One-sentence rationale if non-trivial.",
     "inputs": {"question": "${message}"},
     "auth": {"api_key_secret": "OPENAI_API_KEY"},
     "outputs": {"variables": {"ans_oai": "$.text"}, "next": "synthesize"}
    },

    {"id": "synthesize", "type": "agent", "provider": "adp", "model": "deepseek-v3",
     "system": "Synthesizer: read DS/Claude/OAI answers. Rules: 1) adopt consensus; 2) prefer verifiable statements; 3) if unsure, ask one clarifying question; 4) Return JSON {answer, picked, conflicts}",
     "inputs": {"ds": "${ans_ds}", "cl": "${ans_claude}", "oai": "${ans_oai}", "user": "${message}"},
     "outputs": {"variables": {"merged": "$.json.answer", "picked": "$.json.picked", "conflicts": "$.json.conflicts", "reply_conf": "$.confidence"}, "next": "guardrails"}
    },

    {"id": "guardrails", "type": "guardrail",
     "policies": ["pii_mask","toxicity","prompt_injection","hallucination_check"],
     "thresholds": {"min_confidence": 0.6, "max_toxicity": 0.2},
     "outputs": {"variables": {"risk": "$.risk", "violations": "$.violations", "sanitized": "$.sanitized_text"}, "next": "hitl_router"}
    },

    {"id": "hitl_router", "type": "router",
     "rules": [
       {"when": "${risk} == 'high' || len(${violations}) > 0 || ${reply_conf} < 0.6", "to": "human_review"},
       {"default": "egress"}
     ]
    },

    {"id": "human_review", "type": "human_review",
     "queue": "cs_review",
     "channels": ["console","slack","zendesk"],
     "wait": true,
     "timeout_sec": 900,
     "payload": {"proposed": "${sanitized ?? merged}", "reason": "${violations}", "picked": "${picked}", "conflicts": "${conflicts}"},
     "outputs": {"variables": {"approved": "$.approved", "edited_text": "$.edited", "reviewer": "$.actor"}, "next": "finalize"}
    },

    {"id": "finalize", "type": "switch",
     "cases": [
       {"when": "${approved} == true", "to": "egress_approved"},
       {"when": "${approved} == false && ${edited_text}", "to": "egress_edited"},
       {"default": "egress_reject"}
     ]
    },

    {"id": "egress_approved", "type": "egress", "channels": ["webchat","email"],
     "payload": {"text": "${sanitized ?? merged}", "meta": {"picked": "${picked}", "reviewer": "${reviewer}"}}
    },

    {"id": "egress_edited", "type": "egress", "channels": ["webchat","email"],
     "payload": {"text": "${edited_text}", "meta": {"picked": "${picked}", "reviewer": "${reviewer}"}}
    },

    {"id": "egress_reject", "type": "egress", "channels": ["webchat"],
     "payload": {"text": "요청하신 내용은 검토 결과 제공이 어렵습니다. 상담원에게 연결해 드릴게요."}
    }
  ],
  "observability": {"log": true, "trace": true, "eval": {"rubrics": ["grounding","tone","policy_compliance"]}}
}
```

> 병렬 지원 시 `ask_*` 노드를 병렬 실행 후 **join** → `synthesize`로 이어도 됩니다. 여기선 호환성을 위해 순차 구성.

---

## 3) 콘솔 핸즈온 (권장 순서)
1) **시크릿/프로바이더 준비**
   - Secrets: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` 등록
   - Provider Connector에서 OpenAI/Anthropic 활성화
2) **Guardrails 정책 설정**
   - *Guardrails* 메뉴에서 `pii_mask`, `toxicity`, `prompt_injection`, `hallucination_check` 추가
   - 임계치: `min_confidence=0.6`, `max_toxicity=0.2` (예시)
   - 액션: PII→`mask`, toxic/prompt‑inj.→`route_to_human`, hallucination→`requery` 또는 `route_to_human`
3) **HITL 큐/채널 구성**
   - Human Review Queue 생성: `cs_review`
   - 연결 채널 선택: 콘솔 인박스, Slack, Zendesk 중 택1 이상
4) **캔버스 구성**
   - Ingress → DeepSeek → Claude → OpenAI → Synthesize → Guardrails → Router → (Human Review ↔ Finalize) → Egress
   - 변수 연결이 JSON과 일치하도록 `reply_conf / risk / violations / sanitized` 바인딩
5) **배포 및 테스트**
   - “주문 123‑456 배송 어디쯤?” / “환불 기간과 조건?” / “민감정보 포함 요청(전화번호 노출)” 등 시나리오 실행
   - Guardrails 로그/증적, Human Review 대기열 생성 여부 확인

---

## 4) API 핸즈온 — 생성/배포/실행 + HITL 승인
> 엔드포인트는 테넌트마다 다를 수 있습니다. **콘솔의 API Call Information** 값을 그대로 사용하세요.

### 4‑1. 환경 변수(.env)
```bash
export ADP_BASE="https://<tenant-base>"
export ADP_API_KEY="YOUR_ADP_API_KEY"
export ADP_APP_ID="<your_app_id>"
export ADP_WF_CREATE_URL="$ADP_BASE/v1/apps/$ADP_APP_ID/workflows"
export ADP_WF_DEPLOY_URL="$ADP_BASE/v1/apps/$ADP_APP_ID/workflows/{workflow_id}:deploy"
export ADP_WF_RUN_URL="$ADP_BASE/v1/apps/$ADP_APP_ID/workflows/{workflow_id}:run"
# (예시) 사람 승인/거부 엔드포인트 — 실제 경로는 테넌트 별도
export ADP_HITL_DECIDE_URL="$ADP_BASE/v1/apps/$ADP_APP_ID/humanTasks/{task_id}:decide"
```

### 4‑2. 생성
```bash
# 파일 저장: labs/10_guardrails/multi-agent-guardrails-hitl.json
curl -s -X POST "$ADP_WF_CREATE_URL" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json" \
  -d @labs/10_guardrails/multi-agent-guardrails-hitl.json | tee .hitl.create.out.json
export HITL_WF_ID=$(cat .hitl.create.out.json | python -c 'import sys,json;print(json.load(sys.stdin).get("id",""))')
```

### 4‑3. 배포
```bash
curl -s -X POST "${ADP_WF_DEPLOY_URL//{workflow_id}/$HITL_WF_ID}" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json" -d '{}'
```

### 4‑4. 실행
```bash
cat <<'JSON' > .hitl.run.json
{"channel":"webchat","user_id":"u-777","message":"환불 기간과 개인정보 처리는? 제 전화번호 010-1234-5678"}
JSON
curl -s -X POST "${ADP_WF_RUN_URL//{workflow_id}/$HITL_WF_ID}" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json" \
  -d @.hitl.run.json | tee .hitl.run.out.json | jq -r

# 응답에 human_review 대기 상태가 포함되면 task_id를 추출 (스키마는 테넌트마다 다를 수 있음)
export TASK_ID=$(cat .hitl.run.out.json | python - <<'PY'
import sys,json
j=json.load(sys.stdin)
print(j.get('human_task_id') or j.get('task',{}).get('id') or '')
PY
)
```

### 4‑5. HITL 승인/거부 (예시)
```bash
# 승인 (approve=true), 사람이 수정한 텍스트를 적용하려면 edited_text 포함
curl -s -X POST "${ADP_HITL_DECIDE_URL//{task_id}/$TASK_ID}" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json" \
  -d '{"approved":true, "edited_text":"(검토됨) 개인정보는 마스킹되어 제공됩니다. 반품 기간은 14일이며..."}' | jq -r

# 거부
# curl -s -X POST "${ADP_HITL_DECIDE_URL//{task_id}/$TASK_ID}" -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json" -d '{"approved":false,"reason":"policy_violation"}'
```

---

## 5) Python SDK 핸즈온 — human_decide() 추가
> 이전 랩의 `AdpClient`에 **Human Task** 메서드를 확장합니다. 엔드포인트는 콘솔 기준으로 조정하세요.

### 5‑1. `sdk/adp_sdk.py` (추가)
```python
class AdpClient:
    # ... 기존 create_workflow / deploy_workflow / run_workflow 등

    def human_decide(self, app_id: str, task_id: str, approved: bool, edited_text: str = None, reason: str = None):
        url = f"{self.base}/v1/apps/{app_id}/humanTasks/{task_id}:decide"
        payload = {"approved": approved}
        if edited_text: payload["edited_text"] = edited_text
        if reason: payload["reason"] = reason
        return self._post(url, payload)
```

### 5‑2. `examples/use_sdk_guardrails_hitl.py`
```python
# coding: utf-8
import os, json
from pathlib import Path
from sdk.adp_sdk import AdpClient

BASE=os.getenv("ADP_BASE"); KEY=os.getenv("ADP_API_KEY"); APP=os.getenv("ADP_APP_ID")
assert BASE and KEY and APP, "환경변수 ADP_BASE/ADP_API_KEY/ADP_APP_ID 필요"
client=AdpClient(BASE, KEY)

spec=json.loads(Path("labs/10_guardrails/multi-agent-guardrails-hitl.json").read_text(encoding="utf-8"))
created=client.create_workflow(APP, spec)
wf_id=created.get("id") or created.get("data",{}).get("id")
print("[create]", json.dumps(created, ensure_ascii=False, indent=2)); assert wf_id
print("[deploy]", client.deploy_workflow(APP, wf_id))

run_in={"channel":"webchat","user_id":"u-777","message":"환불 기간과 개인정보 처리는? 제 번호 010-1234-5678"}
run_out=client.run_workflow(APP, wf_id, run_in)
print("[run]", json.dumps(run_out, ensure_ascii=False, indent=2))

# (예시) 응답에서 task_id를 추출해 승인 수행
task_id = run_out.get("human_task_id") or run_out.get("task",{}).get("id")
if task_id:
    print("[human_decide]", json.dumps(
        client.human_decide(APP, task_id, approved=True, edited_text="(검토됨) 개인정보는 마스킹됩니다. 반품 기간은 14일입니다."),
        ensure_ascii=False, indent=2))
```

### 5‑3. 실행
```bash
python -m venv .venv && source .venv/bin/activate
pip install requests python-dotenv
export $(grep -v '^#' .env | xargs)
python examples/use_sdk_guardrails_hitl.py
```

---

## 6) 품질/컴플라이언스 점검 루틴(What good looks like)
- **민감정보**가 자동 마스킹되며 로그에 탐지 근거가 저장된다.
- **불확실/위험** 상황에서 자동으로 **HITL 대기열**이 생성된다.
- 사람이 **수정/승인/거부**하면 그 결과가 최종 응답에 반영된다.
- **관찰성**(log/trace/eval)에서 근거/가드레일/의사결정 경로가 재현 가능하다.

---

## 7) 트러블슈팅
- 401/403: API Key/권한, Provider 시크릿 바인딩(OPENAI/ANTHROPIC) 확인
- 404/스키마 오류: `human_review`/`guardrail` 노드 타입 이름이 테넌트 스펙과 다를 수 있음 → 콘솔 Export JSON 참조
- 응답 지연: `wait=true`인 HITL은 SLA에 영향 → `timeout_sec`/비동기 플로우 고려
- 과도 차단: 정책 임계치 완화, 합성 단계 프롬프트 개선(팩트 중심/인용 강제)

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
- "환불 기간과 개인정보 처리 방침 알려줘 (전화번호 포함)"
- "주문 123-456 배송 어디쯤이야?"
- "의료 조언이 필요한데…" (민감 의도 → HITL 전환 확인)

> 위 프롬프트로 **가드레일→HITL→최종응답** 흐름이 정상 동작하고, 로그/평가에서 근거가 재현되면 핸즈온 완료입니다. 🎉