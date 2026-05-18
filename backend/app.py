import base64
import json
import os
import traceback
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from services.segformer_inference import run_segmentation, run_segmentation_batch

from database import Base, engine, get_db, SessionLocal
from auth import router as auth_router, get_current_user, get_password_hash
from models import User, SegmentationHistory

DEBUG = True

BASE_DIR    = Path.cwd()
HISTORY_DIR = BASE_DIR / "history_images"

HISTORY_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="ArchAnalyse API")

Base.metadata.create_all(bind=engine)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:80",
        "http://localhost",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.mount("/history_images", StaticFiles(directory=str(HISTORY_DIR)), name="history_images")

SAFE_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")

def sanitize_filename(name: str, default: str = "upload.pdf") -> str:
    safe = "".join(c for c in name if c in SAFE_CHARS)
    return safe or default

def save_b64_image(b64_str: str, dest: Path) -> str:
    data = base64.b64decode(b64_str)
    with open(dest, "wb") as f:
        f.write(data)
    return dest.name


# ── Admin initialisation on startup ─────────────────────────────────────────
# Creates one admin account if it doesn't exist yet.
# Change ADMIN_USERNAME / ADMIN_PASSWORD via environment variables before deploying.

@app.on_event("startup")
def create_default_admin():
    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    admin_email    = os.environ.get("ADMIN_EMAIL",    "admin@archanalyse.com")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == admin_username).first()
        if not existing:
            admin = User(
                username=admin_username,
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                is_admin=True,
                is_approved=True,
            )
            db.add(admin)
            db.commit()
            print(f"[startup] Admin account '{admin_username}' created.")
        else:
            print(f"[startup] Admin account '{admin_username}' already exists.")
    finally:
        db.close()


# ── Admin helper ─────────────────────────────────────────────────────────────
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ── Admin routes ─────────────────────────────────────────────────────────────

@app.get("/api/admin/pending")
def list_pending_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Return all users who have registered but not yet been approved."""
    users = db.query(User).filter(User.is_approved == False, User.is_admin == False).all()
    return [
        {"id": u.id, "username": u.username, "email": u.email, "created_at": u.created_at.isoformat() if u.created_at else None}
        for u in users
    ]


@app.get("/api/admin/users")
def list_all_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Return all non-admin users (approved and pending)."""
    users = db.query(User).filter(User.is_admin == False).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_approved": u.is_approved,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@app.post("/api/admin/approve/{user_id}")
def approve_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Approve a pending user so they can log in."""
    user = db.query(User).filter(User.id == user_id, User.is_admin == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_approved:
        raise HTTPException(status_code=400, detail="User is already approved")
    user.is_approved = True
    db.commit()
    return {"message": f"User '{user.username}' has been approved."}


@app.delete("/api/admin/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Remove a user (revoke access). Cannot delete another admin."""
    user = db.query(User).filter(User.id == user_id, User.is_admin == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": f"User '{user.username}' has been removed."}


# ── Core routes ───────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/history")
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(SegmentationHistory)
        .filter(SegmentationHistory.user_id == current_user.id)
        .order_by(SegmentationHistory.created_at.desc())
        .all()
    )
    return [
        {
            "id":            r.id,
            "filename":      r.filename,
            "wall_pct":      r.wall_pct,
            "width":         r.width,
            "height":        r.height,
            "created_at":    r.created_at.isoformat() if r.created_at else None,
            "original_url":  f"/history_images/{Path(r.original_path).name}",
            "overlay_url":   f"/history_images/{Path(r.overlay_path).name}",
            "extracted_url": f"/history_images/{Path(r.extracted_path).name}",
        }
        for r in records
    ]


@app.delete("/api/history/{record_id}")
def delete_history(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(SegmentationHistory).filter(
        SegmentationHistory.id == record_id,
        SegmentationHistory.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    for path_str in (record.original_path, record.overlay_path, record.extracted_path):
        p = Path(path_str)
        if p.exists():
            p.unlink()
    db.delete(record)
    db.commit()
    return {"message": "deleted"}


# ── Wall Segmentation ─────────────────────────────────────────────────────────

@app.post("/api/segment")
async def segment_walls(image: UploadFile = File(...)):
    try:
        if not (image.content_type or "").startswith("image/"):
            raise HTTPException(status_code=400, detail="Please upload an image file.")
        image_bytes = await image.read()
        result = run_segmentation(image_bytes)
        return JSONResponse({"status": "ok", **result})
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print("SEGMENT FAILED\n", tb)
        if DEBUG:
            return JSONResponse({"status": "error", "detail": str(e), "traceback": tb}, status_code=500)
        raise HTTPException(status_code=500, detail="Segmentation failed")


@app.post("/api/segment-batch")
async def segment_batch(
    images: List[UploadFile] = File(...),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not images:
        raise HTTPException(status_code=400, detail="No images provided")

    items = []
    for upload in images:
        if not (upload.content_type or "").startswith("image/"):
            continue
        data = await upload.read()
        items.append((upload.filename or "image.png", data))

    if not items:
        raise HTTPException(status_code=400, detail="No valid image files found")

    user_id = current_user.id if current_user else None

    def generate():
        for result in run_segmentation_batch(items):
            if user_id and not result.get("error"):
                try:
                    local_db = SessionLocal()
                    try:
                        uid       = uuid.uuid4().hex[:8]
                        safe_name = sanitize_filename(result["filename"], "image.png")
                        base      = f"{user_id}_{uid}_{safe_name}"

                        orig_path      = HISTORY_DIR / f"orig_{base}.png"
                        overlay_path   = HISTORY_DIR / f"overlay_{base}.png"
                        extracted_path = HISTORY_DIR / f"extracted_{base}.png"

                        save_b64_image(result["original"],  orig_path)
                        save_b64_image(result["overlay"],   overlay_path)
                        save_b64_image(result["extracted"], extracted_path)

                        record = SegmentationHistory(
                            user_id=user_id,
                            filename=result["filename"],
                            original_path=str(orig_path),
                            overlay_path=str(overlay_path),
                            extracted_path=str(extracted_path),
                            wall_pct=str(result.get("wall_pct", "0")),
                            width=result.get("width", 0),
                            height=result.get("height", 0),
                        )
                        local_db.add(record)
                        local_db.commit()
                    finally:
                        local_db.close()
                except Exception as e:
                    print(f"Failed to save history: {e}")

            yield json.dumps(result) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


# ── Segmentation PDF Export ───────────────────────────────────────────────────
from export_pdf import build_segment_pdf_from_b64, build_segment_pdf_from_files
from pydantic import BaseModel as PydanticBase


class SegmentExportRequest(PydanticBase):
    filename: str
    wall_pct: str
    width: int
    height: int
    original: str
    overlay: str
    extracted: str


@app.post("/api/export-segment-pdf")
def export_segment_pdf(payload: SegmentExportRequest):
    try:
        pdf_bytes = build_segment_pdf_from_b64(
            filename=payload.filename,
            wall_pct=payload.wall_pct,
            width=payload.width,
            height=payload.height,
            original_b64=payload.original,
            overlay_b64=payload.overlay,
            extracted_b64=payload.extracted,
        )
        safe = sanitize_filename(Path(payload.filename).stem, "result") + "_segmentation.pdf"
        return Response(
            content=pdf_bytes, media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe}"'},
        )
    except Exception as e:
        tb = traceback.format_exc()
        print("EXPORT PDF FAILED\n", tb)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history/{record_id}/pdf")
def export_history_pdf(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(SegmentationHistory).filter(
        SegmentationHistory.id == record_id,
        SegmentationHistory.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    for p in (record.original_path, record.overlay_path, record.extracted_path):
        if not Path(p).exists():
            raise HTTPException(status_code=404, detail=f"Image file missing: {p}")

    try:
        pdf_bytes = build_segment_pdf_from_files(
            filename=record.filename,
            wall_pct=record.wall_pct,
            width=record.width,
            height=record.height,
            original_path=record.original_path,
            overlay_path=record.overlay_path,
            extracted_path=record.extracted_path,
        )
        safe = sanitize_filename(Path(record.filename).stem, "result") + "_segmentation.pdf"
        return Response(
            content=pdf_bytes, media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe}"'},
        )
    except Exception as e:
        tb = traceback.format_exc()
        print("HISTORY PDF FAILED\n", tb)
        raise HTTPException(status_code=500, detail=str(e))