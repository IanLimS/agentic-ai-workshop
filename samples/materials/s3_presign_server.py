#!/usr/bin/env python3
"""
Simple S3 presign/list microservice for ADP Plugin (OpenAPI-backed).
Requires: pip install fastapi uvicorn boto3
AWS creds: set via environment (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION)
"""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
from botocore.client import Config

app = FastAPI(title="S3 Presign Helper", version="1.0.0")

class PresignReq(BaseModel):
    bucket: str
    key: str
    operation: str  # 'get_object' | 'put_object'
    expires_in: int = 900

class ListReq(BaseModel):
    bucket: str
    prefix: str | None = None

def s3_client():
    region = os.getenv("AWS_REGION") or "ap-northeast-2"
    return boto3.client("s3", region_name=region, config=Config(signature_version="s3v4"))

@app.post("/s3/presign")
def presign(req: PresignReq):
    s3 = s3_client()
    if req.operation not in ("get_object","put_object"):
        raise HTTPException(400, "operation must be get_object or put_object")
    params = {"Bucket": req.bucket, "Key": req.key}
    url = s3.generate_presigned_url(ClientMethod=req.operation, Params=params, ExpiresIn=req.expires_in)
    # For PUT we can also return URL only (no fields needed). For POST forms, use generate_presigned_post.
    return {"url": url, "fields": {}}

@app.post("/s3/list_objects")
def list_objects(req: ListReq):
    s3 = s3_client()
    kwargs = {"Bucket": req.bucket}
    if req.prefix:
        kwargs["Prefix"] = req.prefix
    resp = s3.list_objects_v2(**kwargs)
    out = []
    for c in resp.get("Contents", []):
        out.append({"key": c["Key"], "size": c["Size"]})
    return {"objects": out}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
