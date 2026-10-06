"""Emergency QR endpoints.

Owner routes  (JWT):   /api/v1/emergency/...
Public routes (token): /api/v1/emergency/scan/{token}  (JSON)  and  /e/{token}  (HTML page)
"""
import time
from collections import defaultdict, deque
from datetime import date
from html import escape
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
# ---- ADJUST THESE TWO IMPORTS to match your repo -------------------------------
from app.api.v1.endpoints.auth import get_current_user
from app.models.models import FamilyMember
# --------------------------------------------------------------------------------
from app.models.emergency import EmergencyAccessLog, EmergencyProfile, EmergencyQRToken
from app.schemas.emergency import (
    AccessLogOut, EmergencyProfileIn, EmergencyProfileOut, EmergencyPublicView, QRIssueOut,
)
from app.services.qr_service import hash_token, new_token, qr_png_base64, qr_svg

router = APIRouter(prefix="/emergency", tags=["Emergency QR"])
public_page_router = APIRouter(tags=["Emergency QR (public page)"])  # mounted at root: /e/{token}

PUBLIC_BASE_URL = getattr(settings, "PUBLIC_BASE_URL", "http://localhost:8000")


# ---------- helpers ---------------------------------------------------------
def _owned_member(db: Session, member_id: int, user) -> FamilyMember:
    m = db.query(FamilyMember).filter(
        FamilyMember.id == member_id, FamilyMember.user_id == user.id
    ).first()
    if not m:
        raise HTTPException(404, "Family member not found")  # same error => no id probing
    return m


def _split(s: str) -> List[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def _age(dob) -> int | None:
    if not dob:
        return None
    if hasattr(dob, "date"):
        dob = dob.date()
    t = date.today()
    return t.year - dob.year - ((t.month, t.day) < (dob.month, dob.day))


# Simple in-memory limiter (per process). Use Redis / slowapi in production.
_hits: dict[str, deque] = defaultdict(deque)


def rate_limit(request: Request, limit: int = 20, window: int = 60):
    ip = request.client.host if request.client else "unknown"
    q, now = _hits[ip], time.time()
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(429, "Too many requests")
    q.append(now)


def _resolve_token(db: Session, token: str) -> FamilyMember:
    row = db.query(EmergencyQRToken).filter(
        EmergencyQRToken.token_hash == hash_token(token),
        EmergencyQRToken.revoked.is_(False),
    ).first()
    if not row:
        raise HTTPException(404, "Invalid or revoked QR code")
    member = db.get(FamilyMember, row.family_member_id)
    if not member:
        raise HTTPException(404, "Invalid or revoked QR code")
    return member


def _build_public_view(db: Session, member: FamilyMember) -> EmergencyPublicView:
    p = db.query(EmergencyProfile).filter_by(family_member_id=member.id).first()
    if not p:
        raise HTTPException(404, "No emergency profile set up")
    # getattr keeps this working whatever your FamilyMember column names are
    return EmergencyPublicView(
        name=getattr(member, "name", None) or getattr(member, "full_name", "Unknown"),
        age=_age(getattr(member, "date_of_birth", None) or getattr(member, "dob", None)),
        sex=getattr(member, "gender", None) or getattr(member, "sex", None),
        blood_group=p.blood_group,
        allergies=_split(p.allergies),
        chronic_conditions=_split(p.chronic_conditions),
        current_medications=_split(p.current_medications),
        implants_devices=_split(p.implants_devices),
        is_pregnant=bool(p.is_pregnant),
        organ_donor=bool(p.organ_donor),
        emergency_contact_name=p.emergency_contact_name,
        emergency_contact_phone=p.emergency_contact_phone,
        notes=p.notes or "",
    )


def _log_access(db: Session, member_id: int, request: Request):
    db.add(EmergencyAccessLog(
        family_member_id=member_id,
        ip_address=request.client.host if request.client else None,
        user_agent=(request.headers.get("user-agent") or "")[:255],
    ))
    db.commit()


# ---------- owner routes (authenticated) --------------------------------------
@router.put("/{member_id}/profile", response_model=EmergencyProfileOut)
def upsert_profile(member_id: int, body: EmergencyProfileIn,
                   db: Session = Depends(get_db), user=Depends(get_current_user)):
    _owned_member(db, member_id, user)
    p = db.query(EmergencyProfile).filter_by(family_member_id=member_id).first()
    if not p:
        p = EmergencyProfile(family_member_id=member_id)
        db.add(p)
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.get("/{member_id}/profile", response_model=EmergencyProfileOut)
def get_profile(member_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _owned_member(db, member_id, user)
    p = db.query(EmergencyProfile).filter_by(family_member_id=member_id).first()
    if not p:
        raise HTTPException(404, "No emergency profile yet")
    return p


@router.post("/{member_id}/qr", response_model=QRIssueOut)
def generate_qr(member_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Create (or regenerate) the QR. Any previous QR for this member stops working."""
    _owned_member(db, member_id, user)
    if not db.query(EmergencyProfile).filter_by(family_member_id=member_id).first():
        raise HTTPException(400, "Fill in the emergency profile before generating a QR")
    db.query(EmergencyQRToken).filter_by(family_member_id=member_id, revoked=False)\
      .update({"revoked": True})
    token = new_token()
    db.add(EmergencyQRToken(family_member_id=member_id, token_hash=hash_token(token)))
    db.commit()
    url = f"{PUBLIC_BASE_URL.rstrip('/')}/e/{token}"
    return QRIssueOut(emergency_url=url, qr_png_base64=qr_png_base64(url))


@router.get("/{member_id}/qr.svg")
def qr_svg_preview(member_id: int, url: str, db: Session = Depends(get_db),
                   user=Depends(get_current_user)):
    """Render an SVG (for printing) for a URL returned by POST /qr. Owner-only."""
    _owned_member(db, member_id, user)
    if not url.startswith(PUBLIC_BASE_URL.rstrip("/") + "/e/"):
        raise HTTPException(400, "Not a valid emergency URL")
    return Response(qr_svg(url), media_type="image/svg+xml")


@router.delete("/{member_id}/qr", status_code=204)
def revoke_qr(member_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _owned_member(db, member_id, user)
    db.query(EmergencyQRToken).filter_by(family_member_id=member_id, revoked=False)\
      .update({"revoked": True})
    db.commit()


@router.get("/{member_id}/access-log", response_model=List[AccessLogOut])
def access_log(member_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _owned_member(db, member_id, user)
    return (db.query(EmergencyAccessLog).filter_by(family_member_id=member_id)
            .order_by(EmergencyAccessLog.accessed_at.desc()).limit(100).all())


# ---------- public routes (no login, token is the credential) -------------------
@router.get("/scan/{token}", response_model=EmergencyPublicView,
            dependencies=[Depends(rate_limit)])
def scan_json(token: str, request: Request, db: Session = Depends(get_db)):
    member = _resolve_token(db, token)
    view = _build_public_view(db, member)
    _log_access(db, member.id, request)
    return view


@public_page_router.get("/e/{token}", response_class=HTMLResponse,
                        dependencies=[Depends(rate_limit)])
def scan_page(token: str, request: Request, db: Session = Depends(get_db)):
    """Mobile-friendly page a paramedic sees after scanning."""
    member = _resolve_token(db, token)
    v = _build_public_view(db, member)
    _log_access(db, member.id, request)

    def row(label, items):
        if not items:
            return ""
        val = ", ".join(escape(i) for i in items) if isinstance(items, list) else escape(str(items))
        return f"<div class='r'><b>{label}</b><span>{val}</span></div>"

    alert = "".join(f"<div class='a'>ALLERGY: {escape(a)}</div>" for a in v.allergies)
    body = "".join([
        row("Age / Sex", " / ".join(str(x) for x in (v.age, v.sex) if x)),
        row("Blood group", v.blood_group),
        row("Conditions", v.chronic_conditions),
        row("Medications", v.current_medications),
        row("Implants / devices", v.implants_devices),
        row("Pregnant", "Yes" if v.is_pregnant else ""),
        row("Organ donor", "Yes" if v.organ_donor else ""),
        row("Notes", v.notes),
    ])
    contact = ""
    if v.emergency_contact_phone:
        tel = escape(v.emergency_contact_phone)
        contact = (f"<a class='c' href='tel:{tel}'>Call {escape(v.emergency_contact_name or 'emergency contact')}"
                   f" &middot; {tel}</a>")
    html = f"""<!doctype html><html><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<meta name='robots' content='noindex,nofollow'><title>Emergency medical info</title>
<style>body{{font-family:system-ui,sans-serif;margin:0;background:#f4f4f5;color:#111}}
header{{background:#b91c1c;color:#fff;padding:14px 16px;font-weight:700}}
main{{padding:12px;max-width:560px;margin:auto}}h1{{margin:8px 0 12px;font-size:22px}}
.a{{background:#fee2e2;border-left:6px solid #b91c1c;padding:10px;margin:6px 0;font-weight:700;border-radius:6px}}
.r{{background:#fff;padding:10px 12px;margin:6px 0;border-radius:8px;display:flex;flex-direction:column}}
.r b{{font-size:12px;text-transform:uppercase;color:#666}}
.c{{display:block;background:#15803d;color:#fff;text-align:center;padding:16px;margin:14px 0;
border-radius:10px;text-decoration:none;font-weight:700}}</style></head><body>
<header>EMERGENCY MEDICAL INFORMATION</header><main><h1>{escape(v.name)}</h1>
{alert}{body}{contact}</main></body></html>"""
    return HTMLResponse(html, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})
