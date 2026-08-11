"""File upload endpoint - images for products, invoices, etc."""

import os
import uuid
import hashlib
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse

from auth import get_current_user
from models import User

router = APIRouter(prefix="/api/v1")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB
BASE_URL = "http://127.0.0.1:8000"


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Sirf JPG, PNG, WebP, GIF upload karo")

    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File bahut badi hai — 5MB se chhoti honi chahiye")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "jpg"
    filename = f"{uuid.uuid4().hex[:12]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    url = f"{BASE_URL}/uploads/{filename}"
    return {"url": url, "filename": filename, "size": len(contents)}


@router.post("/upload/multiple")
async def upload_multiple(files: list[UploadFile] = File(...), current_user: User = Depends(get_current_user)):
    results = []
    for file in files[:10]:
        if file.content_type not in ALLOWED_TYPES:
            continue
        contents = await file.read()
        if len(contents) > MAX_SIZE:
            continue
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "jpg"
        filename = f"{uuid.uuid4().hex[:12]}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(contents)
        results.append({"url": f"{BASE_URL}/uploads/{filename}", "filename": filename, "size": len(contents)})

    return {"files": results, "count": len(results)}


@router.get("/uploads/{filename}")
async def serve_upload(filename: str):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File nahi mili")
    return FileResponse(filepath)
