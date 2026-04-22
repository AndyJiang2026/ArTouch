# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create NFC anti-counterfeiting verification API - verify/register/tag-info endpoints
# DATE: 2026-04-22
# ENGINEER: AI Assistant
# RISK-LEVEL: P1

import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import settings
from app.models import NfcTagSecure, VerificationLog
from app.schemas.nfc_secure import (
    RegisterRequest,
    RegisterResponse,
    TagInfoResponse,
    VerifyRequest,
    VerifyResponse,
)

router = APIRouter(prefix="/api/nfc", tags=["NFC安全验证"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# In production, load from secure vault (e.g., HashiCorp Vault, AWS KMS)
# This is the server-side master key - NEVER exposed to clients
DEFAULT_MASTER_KEY = secrets.token_hex(16)  # 32 bytes, loaded from env in real deployment
NFC_BASE_URL = settings.NFC_BASE_URL

# HMAC-SHA256 key derivation: K_tag = HMAC(master_key, uid)
# Anti-counterfeiting signature: Sig = HMAC(K_tag, uid || counter)

# NTAG 216 page layout for protected data:
#   Page 18 (4B): Key Material (written as hex, stored as hex in DB)
#   Page 19 (4B): Signature part 1
#   Page 20 (4B): Signature part 2 + Counter (shared page for space)
# These pages should be password-protected or permanently locked after init.


def _get_master_key() -> bytes:
    """Load master key from environment variable."""
    key = settings.NFC_MASTER_KEY if hasattr(settings, 'NFC_MASTER_KEY') else DEFAULT_MASTER_KEY
    return key.encode('utf-8')


def _derive_key_material(uid: str) -> str:
    """Derive per-tag key: K_tag = HMAC-SHA256(master_key, uid)."""
    master = _get_master_key()
    uid_bytes = uid.encode('utf-8')
    mac = hmac.new(master, uid_bytes, hashlib.sha256)
    return mac.hexdigest()  # 64 hex chars = 32 bytes


def _compute_signature(key_material: str, uid: str, counter: int) -> str:
    """Compute anti-counterfeiting signature: Sig = HMAC-SHA256(key_material, uid || counter)."""
    key_bytes = key_material.encode('utf-8')
    # Concatenate uid and counter in a deterministic way
    message = f"{uid.lower()}{counter}".encode('utf-8')
    mac = hmac.new(key_bytes, message, hashlib.sha256)
    return mac.hexdigest()  # 64 hex chars = 32 bytes


def _get_client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/verify", response_model=VerifyResponse)
def verify_tag(
    body: VerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> VerifyResponse:
    """
    Verify NFC tag authenticity (async, non-blocking).

    Flow:
    1. Look up tag by UID
    2. Verify signature matches server-computed value
    3. Check counter (must be >= DB record to prevent replay)
    4. Log the attempt
    5. Return result (does NOT block video playback)
    """
    client_ip = _get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")[:500]

    # Step 1: Find tag in database
    tag_secure = db.query(NfcTagSecure).filter(
        NfcTagSecure.uid == body.uid.lower()
    ).first()

    if not tag_secure:
        # Don't log for non-existent tags (no associated record)
        return VerifyResponse(
            is_authentic=False,
            uid=body.uid,
            result="tag_not_found",
            message="该标签未注册，请联系生产商",
            counter=0,
            is_first_verify=False,
        )

    if not tag_secure.is_active:
        _log_verification(
            db=db,
            uid=body.uid,
            tag_secure_id=tag_secure.id,
            result="tag_revoked",
            detail="Tag has been revoked",
            client_ip=client_ip,
            user_agent=user_agent,
            submitted_sig=body.signature,
            submitted_ctr=body.counter,
            is_success=0,
        )
        return VerifyResponse(
            is_authentic=False,
            uid=body.uid,
            result="tag_revoked",
            message="该标签已被吊销",
            counter=tag_secure.counter,
            is_first_verify=False,
            product_name=tag_secure.product_name,
        )

    # Step 2: Verify signature
    expected_sig = _compute_signature(tag_secure.key_material, tag_secure.uid, tag_secure.counter)
    sig_match = hmac.compare_digest(body.signature.lower(), expected_sig.lower())

    if not sig_match:
        _log_verification(
            db=db,
            uid=body.uid,
            tag_secure_id=tag_secure.id,
            result="signature_invalid",
            detail=f"Signature mismatch: expected={expected_sig[:16]}..., got={body.signature[:16]}...",
            client_ip=client_ip,
            user_agent=user_agent,
            submitted_sig=body.signature,
            submitted_ctr=body.counter,
            is_success=0,
        )
        return VerifyResponse(
            is_authentic=False,
            uid=body.uid,
            result="signature_invalid",
            message="防伪验证失败，标签数据可能被篡改",
            counter=tag_secure.counter,
            is_first_verify=False,
            product_name=tag_secure.product_name,
        )

    # Step 3: Check counter replay
    is_first = (body.counter == 1 and tag_secure.counter == 1)
    if body.counter < tag_secure.counter:
        _log_verification(
            db=db,
            uid=body.uid,
            tag_secure_id=tag_secure.id,
            result="counter_replay",
            detail=f"Replay detected: submitted={body.counter}, stored={tag_secure.counter}",
            client_ip=client_ip,
            user_agent=user_agent,
            submitted_sig=body.signature,
            submitted_ctr=body.counter,
            is_success=0,
        )
        return VerifyResponse(
            is_authentic=False,
            uid=body.uid,
            result="counter_replay",
            message="检测到重复验证，疑似录音重放攻击",
            counter=tag_secure.counter,
            is_first_verify=False,
            product_name=tag_secure.product_name,
        )

    # Step 4: Update counter (increment by submitted delta, or +1)
    delta = max(1, body.counter - tag_secure.counter + 1)
    tag_secure.counter += delta
    tag_secure.last_verified_at = datetime.utcnow()
    db.commit()

    # Step 5: Log successful verification
    _log_verification(
        db=db,
        uid=body.uid,
        tag_secure_id=tag_secure.id,
        result="ok",
        detail="Verification successful",
        client_ip=client_ip,
        user_agent=user_agent,
        submitted_sig=body.signature,
        submitted_ctr=body.counter,
        is_success=1,
    )

    return VerifyResponse(
        is_authentic=True,
        uid=body.uid,
        result="ok",
        message="验证成功，正品确认",
        counter=tag_secure.counter,
        is_first_verify=is_first,
        product_name=tag_secure.product_name,
        verified_at=tag_secure.last_verified_at,
    )


def _log_verification(
    db: Session,
    uid: str,
    tag_secure_id: int | None,
    result: str,
    detail: str,
    client_ip: str | None,
    user_agent: str,
    submitted_sig: str,
    submitted_ctr: int,
    is_success: int,
) -> None:
    """Log a verification attempt to the database."""
    log = VerificationLog(
        tag_secure_id=tag_secure_id,
        uid=uid.lower(),
        result=result,
        detail=detail[:500] if detail else None,
        client_ip=client_ip,
        user_agent=user_agent,
        submitted_signature=submitted_sig[:64] if submitted_sig else None,
        submitted_counter=submitted_ctr,
        is_success=is_success,
        verified_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()


@router.post("/register", response_model=RegisterResponse)
def register_tag(
    body: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    """
    Register a new NFC tag and generate cryptographic material.
    This is called during factory initialization (offline, secure environment).

    Returns key material, signature, and page data to write to the NTAG 216 tag.
    """
    uid = body.uid.lower()

    # Check if already registered
    existing = db.query(NfcTagSecure).filter(NfcTagSecure.uid == uid).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"UID {uid} already registered",
        )

    # Derive key material
    key_material = body.key_material or _derive_key_material(uid)
    initial_counter = body.counter
    signature = body.signature or _compute_signature(key_material, uid, initial_counter)

    # Build NDEF URL
    ndef_url = f"{NFC_BASE_URL}/{uid}"

    # Protected page data (for writing to NTAG 216 pages 18-20)
    protected_pages = {
        "page_18": key_material[:8],   # First 8 chars = 4 bytes
        "page_19": key_material[8:16], # Next 8 chars = 4 bytes
        "page_20": key_material[16:24], # Next 8 chars = 4 bytes (partial key)
        "page_21": key_material[24:32], # Remaining key
        "page_22": signature[:8],       # Sig part 1
        "page_23": signature[8:16],    # Sig part 2
        "page_24": signature[16:24],   # Sig part 3
        "page_25": signature[24:32],   # Sig part 4 + counter bytes
        # NOTE: In actual NTAG 216 writing, data must be formatted per NXP spec
        # This is simplified for demonstration - actual implementation needs
        # NXP NTAG 216 datasheet page locking and T2T formatting
    }

    # Save to database
    tag_secure = NfcTagSecure(
        uid=uid,
        nfc_tag_id=body.nfc_tag_id,
        key_material=key_material,
        signature=signature,
        counter=initial_counter,
        master_key_id="default",
        product_name=body.product_name,
        note=body.note,
        registered_at=datetime.utcnow(),
        is_active=1,
    )
    db.add(tag_secure)
    db.commit()
    db.refresh(tag_secure)

    return RegisterResponse(
        uid=uid,
        key_material=key_material,
        signature=signature,
        counter=initial_counter,
        ndef_url=ndef_url,
        protected_pages=protected_pages,
        message=f"标签 {uid} 注册成功，请将对应数据写入NTAG 216",
    )


@router.get("/tags/{uid}", response_model=TagInfoResponse)
def get_tag_info(
    uid: str,
    db: Session = Depends(get_db),
) -> TagInfoResponse:
    """
    Query NFC tag registration info by UID.
    Public endpoint (no auth required for anti-counterfeiting lookup).
    """
    uid = uid.lower()
    tag_secure = db.query(NfcTagSecure).filter(NfcTagSecure.uid == uid).first()

    if not tag_secure:
        return TagInfoResponse(
            uid=uid,
            is_registered=False,
        )

    # Count successful verifications
    total_verifs = db.query(func.count(VerificationLog.id)).filter(
        VerificationLog.uid == uid,
        VerificationLog.is_success == 1,
    ).scalar() or 0

    url_code = None
    if tag_secure.nfc_tag:
        url_code = tag_secure.nfc_tag.url_code

    return TagInfoResponse(
        uid=tag_secure.uid,
        is_registered=True,
        is_active=bool(tag_secure.is_active),
        counter=tag_secure.counter,
        product_name=tag_secure.product_name,
        registered_at=tag_secure.registered_at,
        last_verified_at=tag_secure.last_verified_at,
        total_verifications=total_verifs,
        nfc_tag_id=tag_secure.nfc_tag_id,
        url_code=url_code,
    )


@router.get("/logs/{uid}", response_model=list[dict[str, Any]])
def get_verification_logs(
    uid: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Get verification logs for a UID (admin only in production).
    For debugging and audit purposes.
    """
    uid = uid.lower()
    logs = db.query(VerificationLog).filter(
        VerificationLog.uid == uid
    ).order_by(
        VerificationLog.verified_at.desc()
    ).offset(skip).limit(limit).all()

    return [
        {
            "id": log.id,
            "result": log.result,
            "detail": log.detail,
            "is_success": bool(log.is_success),
            "client_ip": log.client_ip,
            "submitted_counter": log.submitted_counter,
            "verified_at": log.verified_at.isoformat() if log.verified_at else None,
        }
        for log in logs
    ]
