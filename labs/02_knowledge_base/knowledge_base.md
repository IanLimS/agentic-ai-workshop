# 🧠 Knowledge Base Workshop — 지식을 ‘이해하고’ 추가·검증하는 두 가지 길 (KR → EN below)

> 이 랩은 **지식(파일/표/DB/Q&A)**을 ADP(TCADP)에 연결하고, **콘솔**과 **API** 두 방식으로 **왜 그렇게 하는지까지** 이해하도록 돕는 “설명형(teacher-style)” 워크샵입니다. 스텝 바이 스텝의 나열이 아니라, 각각의 단계가 **무엇을**, **왜**, **어떻게** 바꾸는지 맥락을 먼저 잡아드립니다.

- 예제 자료 위치(레포): `samples/materials/`
  - `Ecommerce_Returns_Policy_and_FAQ.pdf` — 반품/환불 정책 + 표/삽화
  - `Product_Catalog_Snippet.csv` — 제품/가격/카테고리
  - `Store_Locations.xlsx` — 매장/영업시간/연락처
  - `sample_ecommerce.db` — SQLite 예제(제품·고객·주문·티켓)
  - `Knowledge_QnA.csv` — 규정/FAQ를 **짧고 일관되게** 묶은 Q&A

---

## 0) 왜 이 랩을 하나요? (문제의식 → 해결)
실무에서 모델이 “그럴듯하지만 근거 없는” 답을 내놓는 이유는 간단합니다. **모델이 알아야 할 문서들과 연결이 느슨**하기 때문이죠. 
이 랩은 두 가지 길로 이 문제를 해결합니다:

1) **콘솔 경로(손으로 익히기)**: 파일을 올리고 색인 옵션을 만지며, **출처(Reference Sources)**가 어떻게 달라지는지 감각을 잡습니다.
2) **API 경로(자동화로 굳히기)**: 같은 앱을 OpenAI 호환 API로 호출해, **JSON 응답과 인용**을 강제함으로써 파이프라인에서 **검증 가능한 흐름**을 만듭니다.

> 목표 요약: *“지식을 연결하면 답변은 어떻게 달라지는가?”*를 **체감**하고, 그 과정을 **코드로 재현**합니다.

---

## 1) 멘탈 모델: ADP의 지식 흐름을 머릿속에 그려보기
- **업로드(문서/표/스냅샷/Q&A)** → **파싱/청킹/색인** → (질문 시) **검색/Rerank** → **생성(답변+인용)**
- **Hybrid 검색**은 키워드·벡터를 함께 써서, 숫자/코드/SKU 같은 “정확 단어”와 “의미 유사성”을 동시에 잡습니다.
- **청크 크기(예: 800–1200)**와 **오버랩(예: 100–200)**은 *“한 번에 가져올 맥락의 폭”*을 조절합니다. 너무 작으면 문맥이 끊기고, 너무 크면 잡음이 늘어납니다.
- **Reference Sources**는 말 그대로 “답의 근거 문서/위치”를 보여줍니다. 운영자 관점의 **디버깅 현미경**입니다.

> 기억법: *업로드는 ‘준비’, 색인은 ‘정렬’, 검색은 ‘발견’, 생성은 ‘설명’.*

---

## 2) 준비물 & 환경 (가볍게 점검)
- ADP 활성화 계정과 모델 쿼터(예: `deepseek-r1`)
- 터미널에서 아래 커맨드를 입력해서 환경을 셋팅합니다.
  ```bash
  export ADP_BASE_URL="https://api.lkeap.tencentcloud.com/v1"
  export ADP_API_KEY="YOUR_ADP_API_KEY"   # 실제 키로 바꿔주세요
  export ADP_MODEL="deepseek-r1"
  ```

**자주 하는 실수**
- `Bearer` 접두사 누락, `/v1` 경로 오타, 모델명 오타

---

## 3) 콘솔 경로 — 손으로 이해하는 색인과 인용
> 이번 파트의 목표는 *“파일을 올리면 ADP가 내부에서 무엇을 하는지”*를 **감각**으로 익히는 것입니다.

### 3-1. 앱 선택/생성
ADP Console → **Application Management**에서 새 앱을 만들거나 기존 앱을 선택하세요. 이름은 *“kb-lab”* 정도로 간단히.

### 3-2. Knowledge Management: 파일을 올릴 때의 생각의 흐름
- **PDF** `Ecommerce_Returns_Policy_and_FAQ.pdf` → 정책/표/일러스트가 섞여 있어 “문서형 지식” 테스트에 적합
- **CSV** `Product_Catalog_Snippet.csv` → SKU/가격 같은 “표 기반 정답” 검증에 적합
- **XLSX** `Store_Locations.xlsx` → 시트/열 이름 정합성이 중요. *빈 행은 최소화*하세요
- (선택) **DB 스냅샷** → 6장에서 생성한 `products_snapshot.md`를 올려 제품 설명을 풍부화

**권장 색인 옵션(왜 이렇게?)**
- Retrieval: **Hybrid** — SKU·코드(정확어)와 설명문(의미)을 모두 잡기 위해
- Chunk: **800–1200 / Overlap 100–200** — 문장+표가 섞인 문서에서 맥락 손실을 줄임
- **Reference Sources = On** — 운영자가 “정말로 근거가 붙었는지” 확인해야 하므로 필수

### 3-3. Debug(대화 테스트): 인용을 읽는 법
아래 질문을 던져 **답변 하단의 인용**이 자연스럽게 붙는지 보세요.
- 정책(PDF): *“반품 가능 기간과 환불 소요 일정을 알려줘.”*
- 카탈로그(CSV): *“SKU-1003 Headphones의 가격은 얼마야?”*
- 매장(XLSX): *“서울점 영업시간과 전화번호 알려줘.”*

**만약 인용이 비거나 엉뚱하다면?**
- 임계치를 낮추거나 색인을 다시 돌립니다. 표는 **시트당 한 표** 원칙이 성능이 좋습니다.

> 체크포인트: “정답”보다 **“출처가 타당한가”**를 먼저 보세요. 그게 나중에 거짓말 방지의 핵심이 됩니다.

---

## 4) API 경로 — 자동화로 신뢰를 ‘굳히기’
> 콘솔에서 지식 연결이 끝났다면, 이제 **같은 앱**을 코드로 호출해봅니다. 목표는 **검증 가능한(JSON) 응답**을 만드는 것입니다.

### 4-1. cURL: KB 전용 JSON 응답 강제
```bash
curl -s -X POST "$ADP_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $ADP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"${ADP_MODEL:-deepseek-r1}"'",
    "messages": [
      {"role":"system","content":"Answer ONLY using the app Knowledge Base. Respond in JSON: {\\"found\\":bool, \\"answer\\\":string, \\"citations\\\":[{\\"file\\\":string, \\"loc\\\":string}]}"}, 
      {"role":"user","content":"반품 가능 기간과 환불 소요 일정을 알려줘"}
    ]
  }' | jq -r
```
**왜 JSON을 강제하나요?** 파이프라인에서 **자동 테스트**가 쉬워집니다. `found=false`면 즉시 fallback(예: 사람 연결, 다른 검색)로 분기할 수 있죠.

### 4-2. Python 예제는 **별도 파일**로 제공
- 비스트리밍: `samples/python/kb_api_non_stream.py`
- 스트리밍: `samples/python/kb_api_stream.py`

> 로컬 실행 방법
> ```bash
> # 공통: .env 로드 (macOS/Linux)
> export $(grep -v '^#' .env | xargs)
>
> # 1) 비스트리밍
> python3 samples/python/kb_api_non_stream.py
>
> # 2) 스트리밍(SSE)
> python3 samples/python/kb_api_stream.py
> ```

**다운로드(샘플 모음 ZIP)**: [kb-python-samples.zip](sandbox:/mnt/data/kb_workshop_python_samples/kb-python-samples.zip)

---

## 5) DB → 텍스트 스냅샷 — 관계형을 ‘읽을거리’로 바꾸기
> 왜 DB를 바로 붙이지 않고 **스냅샷(텍스트)**로 만들까요? 모델은 “문장으로 된 맥락”에서 강합니다. 

### 5-1. 스냅샷 생성 흐름(개념)
- `sample_ecommerce.db` → (스크립트) → `products_snapshot.md` + `products_embeddings.jsonl`
- 스냅샷을 **문서처럼** KB에 업로드하면, 제품 설명 질의에 강해집니다.

### 5-2. 실행 예
- 스크립트 경로: `samples/python/db_to_embeddings.py`
```bash
cp samples/materials/sample_ecommerce.db sample.db
python3 samples/python/db_to_embeddings.py
# 결과: artifacts/embeddings/products_snapshot.md , products_embeddings.jsonl
```
업로드 후 질문해 보세요:
- *“Merino Wool Socks 3‑pack은 어떤 특성이 있어?”*
- *“Trail Running Shoes는 어떤 거리대에 적합해?”*

**주의**: 주문/티켓 상태 같은 **실시간 데이터**는 스냅샷에 넣지 않습니다. 이건 **툴콜**(내부 API 호출)로 연결하세요.

---

## 6) Q&A로 답변을 ‘짧고 일관되게’ 만들기
정책 PDF는 길고 모호할 수 있습니다. `Knowledge_QnA.csv`는 **운영자가 원하는 톤/요약**으로 정답을 “핀셋”처럼 잡아줍니다.
- 업로드 전/후를 비교해 보세요:
  - *“교환은 몇 번까지 무료야?”*
  - *“마음이 바뀌어서 반품하는 경우 환불 퍼센트는?”*
- 기대 효과: **짧고 일관된** 문장, 모호성 감소, 충돌 시 Q&A 우선 규칙 적용 가능

---

## 7) (고급) 태깅/스코프·디버깅 — 운영자가 잡을 수 있는 추가 손잡이
**지식 범위 제한**(테넌트 지원 시)
```json
{
  "model": "deepseek-r1",
  "messages": [...],
  "adp_options": {
    "knowledge": { "tags": ["policy","catalog"], "scope": "kb_only" }
  }
}
```
지원이 없다면 **system 프롬프트**로 범위를 제한하세요.

**디버깅 친화 JSON** — 자동 검증을 위한 형식화
```json
{"role":"system","content":"Answer ONLY from KB. Return JSON: {found:boolean, answer:string, citations:[{file:string,loc:string}], grounding_confidence:0..1}"}
```

**운영 파라미터**
- `temperature/top_p/max_tokens`로 톤/길이를 제어
- 429/5xx 재시도: **지수 백오프 + Jitter**
- 스트리밍은 UX 향상, 논‑스트리밍은 견고성 향상 — 상황에 맞춰 선택

---

## 8) 리캡 & 토론 거리
**오늘 얻은 것**
- KB 연결이 “정답률”이 아니라 **“근거가 있는 정답”**을 만든다는 감각
- 콘솔로 **색인 조정**을 체득, API로 **검증 가능한 JSON** 흐름을 완성

**토론 질문**
- 우리 도메인에서 **Q&A**를 어떻게 구성하면 가장 강력할까?
- 지식 충돌(문서 vs Q&A)이 나면 어떤 규칙으로 우선순위를 둘까?
- 실시간 데이터는 툴콜로 어디까지 끌어올까? (SLA/보안/비용)

**최종 체크리스트**
- [ ] PDF/CSV/XLSX 업로드 후 **Reference Sources**가 안정적으로 표시되는가?
- [ ] API 호출에서 **KB 전용 JSON 응답**(found/answer/citations)을 받는가?
- [ ] Q&A 추가 후 동일 질문의 **일관도/명확성**이 개선되는가?
- [ ] 태그/스코프(가능 시) 또는 프롬프트로 문서 **검색 범위**를 통제했는가?

---

# .env 로드 (macOS/Linux)
export $(grep -v '^#' .env | xargs)

# 비스트리밍
python3 samples/python/kb_api_non_stream.py

# 스트리밍(SSE)
python3 samples/python/kb_api_stream.py

# DB → 스냅샷 (sample_ecommerce.db를 프로젝트 루트로 복사 후)
cp samples/materials/sample_ecommerce.db sample.db
python3 samples/python/db_to_embeddings.py