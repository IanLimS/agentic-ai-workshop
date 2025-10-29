# ADP 콘솔 기반 기본 환경 구성 & 테스트 워크샵 

> 본 워크샵은 **Tencent Cloud ADP(Agent Development Platform)** 콘솔만으로 **지식 기반 Q&A 애플리케이션**을 만들고, 디버그/게시/릴리스/API 연동 정보까지 확인하는 과정을 60–90분에 완료하도록 설계되었습니다. (심화: API 호출은 부록에 간단히 포함)

---

## 🔎 목표 (Goals)
- ADP 활성화 및 **애플리케이션 생성/설정**
- **지식베이스(파일/Q&A) 업로드**와 파싱/인덱싱 확인
- 모델 설정(**DeepSeek‑R1** 권장), **지식기반 답변 강제 모드** 등 구성
- **디버그 창 테스트 → 출처(Reference Sources) 확인**
- **Publish**(테스트→프로덕션 전환) 및 **Release Management**에서 API 연동 정보 확인

> 참고: 본 워크샵은 텐센트 공식 문서의 절차를 기반으로 구성되었습니다.

---

## 🧰 사전 준비 (Prerequisites)
- 텐센트 클라우드 계정 + **ADP 활성화** 권한
- 워크샵용 샘플 파일(권장): `assets/kb/`의 PDF/CSV/XLSX/QnA (본 레포 제공 샘플 사용 가능)
- 브라우저 최신 버전

---

## 0) 환경 활성화 (Enable ADP)
1. 텐센트 클라우드에 로그인 → **ADP 활성화** 페이지로 이동
2. 활성화 완료 시 ADP 콘솔로 자동 리다이렉트

> 활성화 후 좌측 메뉴의 **Application Management**로 이동해 앱 생성 플로우를 시작합니다.


![App Activation](/assets/01_quick_start/001_adp_activation.png)

![App Creation](/assets/01_quick_start/002_create_app.png)


## 1) 애플리케이션 만들기 (Create Application)
1. **Create Application** 클릭
2. 앱 기본 정보(이름/아이콘 등) 입력 후 저장  
   - 저장 시 보안 검토가 수행되며 통과 후 반영됩니다.
3. 생성이 완료되면 앱 상세 페이지로 진입
![New App Creation](/assets/01_quick_start/003_create_new_app.png)

---

## 2) 지식베이스 업로드 (Knowledge Management)
1. 앱 내부 **Knowledge Management**로 이동 → **파일 업로드**  
   - 일반 문서: **pdf, doc, docx, ppt, pptx** (최대 200MB)
   - 표/텍스트: **xlsx, xls, md, txt, csv** (최대 20MB)
   - 이미지(텍스트 포함): **png, jpg, jpeg** (최대 50MB, 가로:세로 ≤ 7:1)
   - 표 파일은 **최대 10,000행/100열**, 시트당 하나의 표 권장, 완전 빈 행 다수는 품질에 영향
2. 업로드 후 문서 파싱/분할/저장이 자동 진행됩니다.
3. **Document 탭**에서 문서의 **문자 수/업데이트 시각/상태**를 확인하고, 
   만료 시간 설정/다운로드/삭제/**검색 범위 설정**도 수행할 수 있습니다.
![Knowedge Management](/assets/01_quick_start/004_knowledge_management.png)

![Import Files](/assets/01_quick_start/005_import_files.png)

---

## 3) 모델 및 답변 정책 설정 (Model & Reply Policy)
1. **Model Configuration → Generative Model** 목록에서 **DeepSeek‑R1** 선택
2. **File**/**Q&A** 스위치를 **On**
3. **지식 기반 외 질문 처리**가 엄격해야 한다면, 
   - *“지식 소스에 벗어난 질문은 (사전 지정한) 안내문으로만 응답”* 모드로 전환
    ![Change Model](/assets/01_quick_start/006_change_model.png)
    ![Set Reasoning](/assets/01_quick_start/007_set_reasoning.png)

---

## 4) 대화 테스트 & 출처 확인 (Debug & References)
1. **Dialogue Test(디버그 창)**에서 질문 입력
2. 답변의 **Reference source(출처)** 버튼을 클릭해 인용 문서/페이지를 확인
   - 업로드한 PDF/CSV/XLSX/QnA가 연결되어 있어야 함
   ![Verify References](/assets/01_quick_start/010_verify_app.png)

---

## 5) 게시 & 릴리스 관리 (Publish & Release Management)
1. 테스트가 충분하다면 **Publish** 클릭 → 현재 테스트 환경의 앱을 **프로덕션 환경**으로 배포
2. **Release Management → API Call Information**에서 아래를 확인
   - **경험(체험) 링크**, 공유용 URL/QR
   - **API Key** 표시(권한에 따라 표시) 및 **API 호출 가이드** 링크
     ![Release Management](/assets/01_quick_start/011_release_app.png)

---

## ✅ 검증 체크리스트 (Verification)
- [ ] Debug에서 **지식 기반** 질문에 대해 정확히 답변하는가?
- [ ] 답변에 **Reference Sources**가 표시되는가?
- [ ] 지식 범위를 벗어난 질문에 대해 **정책대로** 응답하는가?
- [ ] Publish 후 **Release Management**에서 링크/키를 확인했는가?

---

## 🧪 (부록) 간단 API 호출
> 콘솔 중심 워크샵이므로 선택 사항입니다. Release Management에서 API Key 발급을 확인한 뒤 실행하세요.
    ![API Key](/assets/01_quick_start/012_api_key.png)

```bash
# .env에 다음이 있다고 가정
# ADP_BASE_URL=https://api.lkeap.tencentcloud.com/v1
# ADP_API_KEY=...
# ADP_MODEL=deepseek-r1

curl -s -X POST "$ADP_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $ADP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"${ADP_MODEL:-deepseek-r1}"'",
    "messages": [
      {"role":"user","content":"반품 기한과 환불 소요 기간을 알려줘."}
    ]
  }' | jq -r '.choices[0].message.content'
```

---

## 🔧 트러블슈팅 (Troubleshooting)
- 업로드 실패: 파일 형식/크기 조건 재확인, 표 파일의 빈 행 제거 권장
- 인용 안 보임: 검색 임계치 하향, 문서 재색인, KB 검색 범위 확인
- 답변이 지식 밖으로 벗어남: **Reply 정책**을 엄격 모드로 설정
- Publish 비활성: 앱 설정 미완료/검토 대기 가능 → 설정 저장/재시도

---

# ADP Console‑Only Quick Workshop (EN)

> Build a **knowledge‑based QA** app with **Tencent Cloud ADP**, test in the **Debug** window, **Publish** to production, and find API details in **Release Management**. Designed for a 60–90 minute session.

## Goals
- Enable ADP and **create/configure** an application
- **Upload Knowledge** (files/Q&A) and confirm parsing/indexing
- Configure **DeepSeek‑R1** + strict **reply policy** for OOD questions
- Test in **Debug** and verify **Reference Sources**
- **Publish** → check **Release Management** for share links/API key

## Prereqs
- Tencent Cloud account with ADP enabled
- Sample files in `assets/kb/` (PDF/CSV/XLSX/QnA)
- Modern browser

## 0) Enable ADP
- Sign in → **Enable ADP** → redirected to ADP Console → **Application Management**

## 1) Create Application
- Click **Create Application** → fill **name/icon** → save (goes through a security review) → enter the app

## 2) Knowledge Management
- **Upload files**:
  - Documents: **pdf, doc, docx, ppt, pptx** (≤ 200MB)
  - Tables/Text: **xlsx, xls, md, txt, csv** (≤ 20MB)
  - Images with text: **png, jpg, jpeg** (≤ 50MB; aspect ratio ≤ 1:7)
  - Tables: up to **10,000 rows / 100 columns**; prefer one table per sheet; avoid lots of empty rows
- Parsing/chunking/storage runs automatically
- In **Document** tab, view **characters/updated time/status**; set expiry, download/delete, and **set KB search scope**

## 3) Model & Reply Policy
- In **Model Configuration → Generative Model**, select **DeepSeek‑R1**
- Turn on **File** and **Q&A**
- For stricter compliance, switch reply policy to “answer only according to the filled content when the question is beyond KB”

## 4) Debug & References
- Ask questions in **Dialogue Test**; click **Reference source** to verify citations

## 5) Publish & Release Management
- Click **Publish** to deploy from test to production
- Go to **Release Management → API Call Information** to get:
  - **Experience link** / share URL / QR code
  - **API Key** and the **API docs** link

## (Optional) Quick API Smoke Test
```bash
curl -s -X POST "$ADP_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $ADP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"'"${ADP_MODEL:-deepseek-r1}"'","messages":[{"role":"user","content":"What is the return window and refund timeline?"}]}'
```

## Troubleshooting
- Upload errors: validate file type/size; remove empty rows in tables
- No citations: lower match threshold or re‑index; confirm KB search scope
- Out‑of‑domain answers: enforce strict reply policy
- Publish disabled: config incomplete or review pending → save and retry