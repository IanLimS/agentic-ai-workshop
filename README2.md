

# ADP Workshop — Extended Labs Assets

This doc packages the extra materials you asked for and shows exactly how to wire them into the workshop repo and ADP.

> TL;DR: Download the assets from chat, then place them under the paths below and follow the commands.

---

## 2) Knowledge Embedding

### 2.1 File‑based Knowledge Base (tables + illustration)
**Files (put into `assets/kb/`):**
- `Ecommerce_Returns_Policy_and_FAQ.pdf` (A4, includes a returns policy table and simple illustrations)
- `Product_Catalog_Snippet.csv`
- `Knowledge_QnA.csv`
- `Store_Locations.xlsx`

**Recommended KB settings (Console → Knowledge Base):**
- Retrieval: *Hybrid* (or *Semantic* if your tenant prefers)
- Chunk size: 800–1200 chars; Overlap: 100–200
- Matching threshold: start with *Medium*; lower if citations fail
- Turn on **Reference Sources** and validate citations in Debug

**Suggested queries to demo**
- *“What’s the return window and refund timeline?”* (Expect: 30 days / 5–7 business days + citations)
- *“List Seoul store hours and phone.”* (XLSX table extraction)
- *“Show Headphones SKU and price.”* (CSV table extraction)

**Copy assets into your repo**
```bash
mkdir -p assets/kb
# (Download links are in chat. Save to ~/Downloads first.)
cp ~/Downloads/Ecommerce_Returns_Policy_and_FAQ.pdf assets/kb/
cp ~/Downloads/Product_Catalog_Snippet.csv assets/kb/
cp ~/Downloads/Knowledge_QnA.csv assets/kb/
cp ~/Downloads/Store_Locations.xlsx assets/kb/
```

---

### 2.2 Database → Embeddings (+ snapshot to KB)
**Sample DB:** `assets/kb/sample_ecommerce.db` (tables: products, customers, orders, tickets)

**Place it and run the embedding script**
```bash
mkdir -p assets/kb artifacts/embeddings samples/python
cp ~/Downloads/sample_ecommerce.db assets/kb/
# If not present yet, add the script from README (Advanced Labs) or this repo’s samples:
# samples/python/db_to_embeddings.py

# OpenAI embeddings example
export OPENAI_API_KEY=sk-...
export OPENAI_EMBEDDINGS_MODEL=text-embedding-3-large
python3 samples/python/db_to_embeddings.py

# Outputs
# artifacts/embeddings/products_embeddings.jsonl (vectors for FAISS/PGVector)
# artifacts/embeddings/products_snapshot.md     (upload this to ADP KB)
```
Then upload `products_snapshot.md` to the ADP Knowledge Base and re‑test citations with product‑related questions.

> Tip: Keep vectors locally for fast prototyping; ADP continues to provide citations using the snapshot.

---

## 3) Workflow — n8n (E‑commerce Customer Support)
**File:** `assets/workflows/n8n_ecommerce_support_workflow.json`

**Import to n8n**
1. n8n → *Import from File* → select the JSON
2. Set env vars on the HTTP nodes or globally:
   - `ADP_BASE_URL=https://api.lkeap.tencentcloud.com/v1`
   - `ADP_API_KEY=***`
   - `ADP_MODEL=deepseek-r1`
3. Activate the **Webhook** node and note the URL

**Quick test**
```bash
curl -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{"question":"How do I return my order and how long is the refund?"}'
```
Flow: Webhook → Classify → Search KB (JSON‑only answer) → IF(found) else → LLM fallback → Respond

**Copy into repo**
```bash
mkdir -p assets/workflows
cp ~/Downloads/n8n_ecommerce_support_workflow.json assets/workflows/
```

---

## 5) MCP / Plugin — AWS S3 Presign & List
**OpenAPI spec:** `plugins/s3/openapi_s3_presign.json`  
**Server (FastAPI):** `plugins/s3/s3_presign_server.py`

**Deploy the server**
```bash
pip install fastapi uvicorn boto3
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=ap-northeast-2
python plugins/s3/s3_presign_server.py  # -> http://localhost:8080
```

**Register the plugin in ADP**
1. Open `plugins/s3/openapi_s3_presign.json` and set `servers[0].url` to your public base URL.
2. ADP Console → **Plugin → Register → From OpenAPI**
3. In your workflow, add a **Tool** node and call:
   - `POST /s3/presign` with `{ "bucket":"my-bkt", "key":"demo.txt", "operation":"put_object" }` → returns `url`
   - `POST /s3/list_objects` with `{ "bucket":"my-bkt", "prefix":"inbox/" }` → returns object list

**Security notes**
- Use a dedicated IAM user/role scoped to the bucket/prefix
- Consider private networking/VPC‑only access
- Rotate credentials regularly

**Copy plugin assets into repo**
```bash
mkdir -p plugins/s3
cp ~/Downloads/openapi_s3_presign.json plugins/s3/
cp ~/Downloads/s3_presign_server.py plugins/s3/
```

---

## Download Links (provided in chat)
- Knowledge (PDF/CSV/XLSX/DB)
  - Ecommerce_Returns_Policy_and_FAQ.pdf
  - Product_Catalog_Snippet.csv
  - Knowledge_QnA.csv
  - Store_Locations.xlsx
  - sample_ecommerce.db
- Workflow
  - n8n_ecommerce_support_workflow.json
- Plugin
  - openapi_s3_presign.json
  - s3_presign_server.py

> After copying, commit the assets: `git add assets plugins && git commit -m "add KB samples, n8n workflow, and S3 plugin"`

---

# 🇰🇷 한글 요약 (Korean Summary)

## 2) 지식 임베딩
- **파일 기반 KB**: PDF(표+삽화), 제품 CSV, QnA CSV, 매장 XLSX → `assets/kb/` 에 넣고 KB 업로드, 하이브리드 검색/인용 확인
- **DB 기반**: `sample_ecommerce.db` → `db_to_embeddings.py` 실행 → `products_snapshot.md`를 KB에 업로드

## 3) 워크플로 (n8n)
- `n8n_ecommerce_support_workflow.json` 임포트 → ADP Base URL/Key/Model 설정 → Webhook로 질문 POST

## 5) MCP/플러그인 (S3)
- `s3_presign_server.py` 배포(로컬 또는 퍼블릭) → `openapi_s3_presign.json`의 서버 URL 수정 → ADP Plugin 등록 → Tool 노드에서 presign/list 호출

필요 시 본문 커맨드대로 `assets/`, `plugins/` 경로를 만든 뒤 파일을 복사하고 커밋하세요.