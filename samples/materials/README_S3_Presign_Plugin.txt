# S3 Presign Plugin

1) Deploy `s3_presign_server.py` (FastAPI) where ADP can reach it (e.g., Cloud Run/EC2).
2) Open `openapi_s3_presign.json` and set `"servers"[0]."url"` to your deployed base URL.
3) Register this OpenAPI spec as a Plugin in ADP Console (Plugin → Register → From OpenAPI).
4) In your workflow, add a **Tool** node calling:
   - POST /s3/presign (generate upload/download URL)
   - POST /s3/list_objects (list bucket/prefix)

Security notes:
- Scope the microservice to a dedicated IAM user with **least privilege** (bucket‑scoped.
- Rotate credentials; consider VPC‑only access / private networking.
