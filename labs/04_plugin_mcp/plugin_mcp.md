

# 🔌 ADP Plugin & MCP Hands‑on — 콜센터(고객센터) 시나리오 확장

> 이 문서는 **설명형(teacher‑style)** 가이드입니다. 콘솔과 API, 그리고 Python SDK(경량 어댑터)를 이용해 **ADP Plugin**을 사용하는 법과, **MCP(Model Context Protocol) 플러그인**을 직접 만들어 연결하는 과정을 단계별로 실습합니다.

---

## 0) 목표와 산출물
**목표**
- ADP Plugin의 개념(툴 정의, 시크릿, 입력/출력 스키마, 배포)과 사용 방법 이해.
- 콜센터 워크플로우에 **OMS(주문관리) 플러그인**을 연결해 실무형 도구 호출 구성.
- MCP 플러그인을 Python으로 직접 만들어 로컬/개발 환경에서 호출.

**산출물**
- `labs/04_plugin_mcp/oms-plugin.json` — ADP Plugin 템플릿(HTTP 기반 도구 2종).
- 콘솔 실습: 플러그인 생성/시크릿 연결/테스트/워크플로우 사용.
- API 실습: 플러그인 등록 → 앱에 연결 → 도구 호출(run)까지.
- Python SDK 실습: `AdpClient`에 plugin API 래퍼 추가, end‑to‑end 스크립트.
- `labs/04_plugin_mcp/mcp_oms.py` + `labs/04_plugin_mcp/mcp.json` — **MCP 플러그인** 최소 구현.

> 전제: 이전 랩의 콜센터 워크플로우(`labs/03_workflow/callcenter-triage.json`)가 배포되어 있다고 가정합니다.

---

## 1) ADP Plugin 멘탈 모델
ADP Plugin은 워크플로우/에이전트가 호출할 **도구(tool)** 집합입니다. 핵심 구성은 다음과 같습니다.

- **Manifest(스펙)**: 이름/버전/설명, 툴 목록, 입력/출력 스키마(JSON Schema), 인증/시크릿 참조.
- **Tool Types**: `http`, `sql`, `mcp`, `custom` 등(테넌트 별 제공 유형이 다를 수 있음).
- **Secrets**: 외부 시스템의 BASE URL, 토큰 등을 안전하게 주입.
- **Lifecycle**: 등록(Create) → 검증(Test) → 배포(Deploy) → 앱 연결(Attach) → 워크플로우에서 사용.

---

## 2) 샘플 ADP Plugin — OMS(주문관리) 도구
고객이 “주문 상태 알려줘”, “환불 신청해줘”라고 묻는 상황을 가정합니다. 두 가지 툴을 포함합니다.

- `get_order` — 주문 상세 조회(HTTP GET)
- `create_refund` — 환불 요청 생성(HTTP POST)

### 2‑1. 플러그인 스펙(JSON)
> 파일: `labs/04_plugin_mcp/oms-plugin.json`
```json
{
  "version": "1.0",
  "name": "oms-plugin",
  "description": "Order Management Plugin: fetch order and create refund",
  "secrets": ["OMS_BASE", "OMS_TOKEN"],
  "tools": [
    {
      "name": "get_order",
      "type": "http",
      "config": {
        "method": "GET",
        "url": "${OMS_BASE}/orders/${order_id}",
        "headers": {"Authorization": "Bearer ${OMS_TOKEN}"},
        "timeout": 8
      },
      "input_schema": {
        "type": "object",
        "required": ["order_id"],
        "properties": {"order_id": {"type": "string"}}
      },
      "output_schema": {"type": "object"}
    },
    {
      "name": "create_refund",
      "type": "http",
      "config": {
        "method": "POST",
        "url": "${OMS_BASE}/refunds",
        "headers": {"Authorization": "Bearer ${OMS_TOKEN}", "Content-Type": "application/json"},
        "timeout": 10,
        "body": "${json}"
      },
      "input_schema": {
        "type": "object",
        "required": ["order_id", "reason"],
        "properties": {
          "order_id": {"type": "string"},
          "reason": {"type": "string"}
        }
      },
      "output_schema": {"type": "object"}
    }
  ]
}
```

> 팁: 실제 OMS 스키마에 맞춰 `properties`를 확장하세요(예: 금액, 아이템, 고객 메모 등).

---

## 3) 콘솔 실습 — 플러그인 생성부터 워크플로우 연결까지
1) **Plugin 관리**로 이동 → *Create Plugin* → 위 스펙(JSON)을 업로드하거나 폼에 입력.
2) **Secrets 등록**: `OMS_BASE`, `OMS_TOKEN` 값 저장.
3) **테스트**: get_order에 `{"order_id":"123-456"}`로 **Test Invoke** → 200 응답/본문 확인.
4) **앱에 연결(Attach)**: 대상 앱을 선택하고 플러그인을 연결.
5) **워크플로우 노드 추가**: `fetch_order`(HTTP) 자리에 **plugin.get_order** 호출 노드를 배치하거나, 기존 http_call 노드를 플러그인 도구로 교체.
6) **배포 & 테스트 대화**: “주문 123‑456 배송 어디쯤?” → plugin 경로로 호출되는지 확인.

> 문제 해결: 401이면 토큰/권한 확인, 404는 BASE/경로 점검, 415/422는 JSON 스키마/컨텐츠 타입 확인.

---

## 4) API 실습 — 플러그인 등록/연결/호출(run)
> 테넌트에 따라 경로가 다릅니다. **콘솔의 _API Call Information_** 값을 그대로 사용하세요.

### 4‑1. 환경 변수(.env)
```bash
export ADP_API_KEY="YOUR_ADP_API_KEY"
export ADP_BASE="https://<tenant-base>"                 # 예: https://api.lkeap.tencentcloud.com
export ADP_APP_ID="<your_app_id>"
export ADP_PLUGIN_CREATE_URL="$ADP_BASE/v1/apps/$ADP_APP_ID/plugins"
export ADP_PLUGIN_ATTACH_URL="$ADP_BASE/v1/apps/$ADP_APP_ID/plugins/{plugin_id}:attach"
export ADP_PLUGIN_INVOKE_URL="$ADP_BASE/v1/apps/$ADP_APP_ID/plugins/{plugin_id}/tools/{tool_name}:run"
```

### 4‑2. 플러그인 등록(Create)
```bash
curl -s -X POST "$ADP_PLUGIN_CREATE_URL" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json" \
  -d @labs/04_plugin_mcp/oms-plugin.json | tee .plugin.create.out.json
export PLUGIN_ID=$(cat .plugin.create.out.json | python -c 'import sys,json;print(json.load(sys.stdin).get("id",""))')
```

### 4‑3. 앱에 연결(Attach)
```bash
curl -s -X POST "${ADP_PLUGIN_ATTACH_URL//{plugin_id}/$PLUGIN_ID}" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json" -d '{}'
```

### 4‑4. 도구 호출(Invoke)
```bash
# get_order
curl -s -X POST "${ADP_PLUGIN_INVOKE_URL//{plugin_id}/$PLUGIN_ID}" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json" \
  -d '{"tool":"get_order","input":{"order_id":"123-456"}}' | jq -r

# create_refund
curl -s -X POST "${ADP_PLUGIN_INVOKE_URL//{plugin_id}/$PLUGIN_ID}" \
  -H "Authorization: Bearer $ADP_API_KEY" -H "Content-Type: application/json" \
  -d '{"tool":"create_refund","input":{"order_id":"123-456","reason":"customer_request"}}' | jq -r
```

---

## 5) Python SDK 실습 — plugin API 래퍼 추가
> 이전 랩의 `AdpClient`에 **plugin** 메서드를 확장합니다.

### 5‑1. `sdk/adp_sdk.py` (추가)
```python
class AdpClient:
    # ... (기존 코드 생략)

    # Plugins
    def create_plugin(self, app_id: str, spec: dict):
        url = f"{self.base}/v1/apps/{app_id}/plugins"
        return self._post(url, spec)

    def attach_plugin(self, app_id: str, plugin_id: str):
        url = f"{self.base}/v1/apps/{app_id}/plugins/{plugin_id}:attach"
        return self._post(url, {})

    def invoke_tool(self, app_id: str, plugin_id: str, tool_name: str, tool_input: dict):
        url = f"{self.base}/v1/apps/{app_id}/plugins/{plugin_id}/tools/{tool_name}:run"
        payload = {"tool": tool_name, "input": tool_input}
        return self._post(url, payload)
```

### 5‑2. `examples/use_sdk_plugin.py`
```python
# coding: utf-8
import os, json
from pathlib import Path
from sdk.adp_sdk import AdpClient

BASE = os.getenv("ADP_BASE"); KEY = os.getenv("ADP_API_KEY"); APP = os.getenv("ADP_APP_ID")
assert BASE and KEY and APP, "ADP_BASE / ADP_API_KEY / ADP_APP_ID 환경변수를 설정하세요."
client = AdpClient(BASE, KEY)

# 1) 플러그인 스펙 로드
spec = json.loads(Path("labs/04_plugin_mcp/oms-plugin.json").read_text(encoding="utf-8"))

# 2) 생성 → attach
created = client.create_plugin(APP, spec)
plugin_id = created.get("id") or created.get("data",{}).get("id")
print("[create]", json.dumps(created, ensure_ascii=False, indent=2))
assert plugin_id
print("[attach]", client.attach_plugin(APP, plugin_id))

# 3) 도구 호출 테스트
print("[invoke:get_order]", json.dumps(
    client.invoke_tool(APP, plugin_id, "get_order", {"order_id":"123-456"}), ensure_ascii=False, indent=2))
print("[invoke:create_refund]", json.dumps(
    client.invoke_tool(APP, plugin_id, "create_refund", {"order_id":"123-456","reason":"customer_request"}), ensure_ascii=False, indent=2))
```

### 5‑3. 실행
```bash
python -m venv .venv && source .venv/bin/activate
pip install requests python-dotenv
export $(grep -v '^#' .env | xargs)
python examples/use_sdk_plugin.py
```

---

## 6) MCP 플러그인 만들기 — Python 최소 구현
MCP는 모델이 표준화된 방식으로 외부 도구를 호출할 수 있게 하는 **도구 서버 프로토콜**입니다(표준 입출력/웹소켓 기반 JSON‑RPC). 여기서는 Python으로 **최소 기능** 도구 서버를 만들어, 로컬/개발 환경에서 테스트합니다.

### 6‑1. 파일 구조
```
labs/04_plugin_mcp/
  mcp_oms.py       # MCP 서버 (파이썬)
  mcp.json         # MCP 매니페스트 (로컬 실행용)
```

### 6‑2. `mcp_oms.py`
> 실제 OMS API로 연결하거나, 샘플 데이터를 반환하도록 두 가지 모드를 제공합니다.
```python
# coding: utf-8
import os, json, sys
from typing import Dict

# 간단한 JSON-RPC over stdin/stdout (의존성 없는 미니 서버)
# 실제 프로젝트에서는 정식 MCP 프레임워크를 사용하는 것을 권장.

def rpc_reply(id, result=None, error=None):
    msg = {"jsonrpc":"2.0","id":id}
    if error is not None: msg["error"] = error
    else: msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n"); sys.stdout.flush()

def handle(method: str, params: Dict):
    if method == "tools/list":
        return {"tools":[
            {"name":"get_order","input_schema":{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string"}}}},
            {"name":"create_refund","input_schema":{"type":"object","required":["order_id","reason"],"properties":{"order_id":{"type":"string"},"reason":{"type":"string"}}}}
        ]}
    if method == "tools/call":
        tool = params.get("name"); data = params.get("arguments",{})
        if tool == "get_order":
            order_id = data.get("order_id")
            if os.getenv("OMS_BASE"):
                import requests
                r = requests.get(f"{os.environ['OMS_BASE'].rstrip('/')}/orders/{order_id}", headers={"Authorization":f"Bearer {os.getenv('OMS_TOKEN','')}"}, timeout=8)
                r.raise_for_status(); return r.json()
            # 샘플 응답(로컬)
            return {"order_id":order_id,"status":"in_transit","carrier":"CJ","eta":"2025-11-03"}
        if tool == "create_refund":
            order_id = data.get("order_id"); reason = data.get("reason")
            if os.getenv("OMS_BASE"):
                import requests
                r = requests.post(f"{os.environ['OMS_BASE'].rstrip('/')}/refunds", json={"order_id":order_id,"reason":reason}, headers={"Authorization":f"Bearer {os.getenv('OMS_TOKEN','')}"}, timeout=10)
                r.raise_for_status(); return r.json()
            return {"refund_id":"rf_001","order_id":order_id,"status":"submitted","reason":reason}
        return {"error":"unknown_tool"}
    return {"error":"unknown_method"}

if __name__ == "__main__":
    for line in sys.stdin:
        try:
            req = json.loads(line)
            result = handle(req.get("method"), req.get("params",{}))
            rpc_reply(req.get("id"), result=result)
        except Exception as e:
            rpc_reply(None, error={"code":-32000,"message":str(e)})
```

### 6‑3. `mcp.json` (로컬 클라이언트 연결용 매니페스트 예시)
```json
{
  "name": "mcp-oms",
  "version": "0.1.0",
  "command": "python",
  "args": ["labs/04_plugin_mcp/mcp_oms.py"],
  "env": ["OMS_BASE","OMS_TOKEN"],
  "tools": ["get_order","create_refund"]
}
```

### 6‑4. 실행
```bash
python labs/04_plugin_mcp/mcp_oms.py <<'JSON'
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_order","arguments":{"order_id":"123-456"}}}
JSON
```

> 출력에 도구 목록과 샘플 주문 응답이 보이면 MCP 서버가 정상 동작입니다. 정식 에이전트/클라이언트(MCP 호환)에서 `mcp.json`을 읽어 연결하면 동일 도구를 사용할 수 있습니다.

---

## 7) ADP와 MCP를 함께 쓰는 방법(옵션)
- 테넌트에 **MCP 커넥터/브리지**가 있을 경우, 위 `mcp.json` 또는 등가 메타를 등록해 **ADP Plugin(type:mcp)**으로 연결할 수 있습니다.
- 없다면, MCP 서버를 내부 서비스로 띄우고 ADP Plugin을 **HTTP 프록시**로 만들어 MCP 호출을 중계하는 방식도 가능합니다(도구 공개 범위/보안 고려).

---

## 8) 트러블슈팅
- 401/403: ADP API 키 권한, 시크릿 바인딩 확인.
- 404/405: 테넌트 엔드포인트/서픽스(`:attach`, `:run`) 차이.
- 415/422: `Content-Type`/입력 스키마 불일치. JSON 키 이름 점검.
- MCP 연결 실패: 표준 입출력 파이프/권한, 경로(`mcp_oms.py`) 확인.

---

## 9) 다음 단계(확장)
- `get_order` 출력 스키마를 상세화하고 **응답 합성 에이전트**의 tone/포맷(예: 한국어 존댓말, 표형식 요약) 강화.
- `create_refund` 전 가드레일로 **본인 인증** 절차(마스킹된 전화번호/주문자명 확인) 삽입.
- MCP 쪽에 `list_orders`, `cancel_order` 등 추가 도구 확장.

---

### 부록 A) 환경 변수 예시
```bash
# 공통
export ADP_BASE="https://<tenant-base>"
export ADP_API_KEY="YOUR_ADP_API_KEY"
export ADP_APP_ID="<your_app_id>"

# 외부 OMS
export OMS_BASE="https://api.example-oms.local"
export OMS_TOKEN="xxxxx"
```

### 부록 B) 테스트 프롬프트
- "주문 123-456 상태 알려줘"
- "환불 신청해줘. 사유는 단순변심"
- "반품 기간과 환불 소요기간?" (지식 인용 포함 응답 확인)