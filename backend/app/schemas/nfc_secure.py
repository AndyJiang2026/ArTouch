# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create Pydantic schemas for NFC anti-counterfeiting API
# DATE: 2026-04-22
# ENGINEER: AI Assistant
# RISK-LEVEL: P1

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class VerifyRequest(BaseModel):
    """Request body for NFC tag verification."""
    uid: str = Field(..., min_length=8, max_length=16, description="NFC tag UID (hex string)")
    signature: str = Field(..., min_length=64, max_length=64, description="HMAC signature (hex string, 32 bytes)")
    counter: int = Field(..., ge=1, description="Verification counter value")
    # Optional: challenge/response to prevent replay (future use)
    challenge: str | None = Field(None, max_length=32, description="Challenge nonce if used")

    @field_validator("uid")
    @classmethod
    def validate_uid(cls, v: str) -> str:
        # Must be valid hex string
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("UID must be a valid hexadecimal string")
        return v.lower()

    @field_validator("signature")
    @classmethod
    def validate_signature(cls, v: str) -> str:
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("Signature must be a valid hexadecimal string")
        return v.lower()


class VerifyResponse(BaseModel):
    """Response for NFC tag verification."""
    is_authentic: bool = Field(..., description="Whether the tag is authentic")
    uid: str
    result: str = Field(..., description="ok, signature_invalid, counter_replay, tag_not_found")
    message: str = Field(..., description="Human-readable result message")
    counter: int = Field(..., description="Current counter value on server")
    is_first_verify: bool = Field(False, description="Whether this is the first verification")
    product_name: str | None = Field(None, description="Product name if registered")
    verified_at: datetime | None = Field(None, description="Last verification timestamp")


class RegisterRequest(BaseModel):
    """Request body for registering a new NFC tag with security data."""
    uid: str = Field(..., min_length=8, max_length=16, description="NFC tag UID (hex string)")
    nfc_tag_id: int | None = Field(None, description="Optional: link to existing NFCTag record")
    product_name: str | None = Field(None, max_length=200, description="Product name for display")
    note: str | None = Field(None, max_length=500, description="Optional note")
    # For manual registration (if not using auto-compute)
    key_material: str | None = Field(None, max_length=64, description="Pre-computed key material (optional)")
    signature: str | None = Field(None, max_length=64, description="Pre-computed signature (optional)")
    counter: int = Field(1, ge=1, description="Initial counter value")

    @field_validator("uid")
    @classmethod
    def validate_uid(cls, v: str) -> str:
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("UID must be a valid hexadecimal string")
        return v.lower()


class RegisterResponse(BaseModel):
    """Response for NFC tag registration."""
    uid: str
    key_material: str = Field(..., description="Derived key material (hex, for writing to tag)")
    signature: str = Field(..., description="Initial signature (hex, for writing to tag)")
    counter: int
    # Pages to write to on NTAG 216
    ndef_url: str = Field(..., description="NDEF URL to write to tag pages 4+")
    protected_pages: dict = Field(..., description="Protected page data to write to tag")
    message: str


class TagInfoResponse(BaseModel):
    """Response for tag info query."""
    uid: str
    is_registered: bool
    is_active: bool | None = None
    counter: int | None = None
    product_name: str | None = None
    registered_at: datetime | None = None
    last_verified_at: datetime | None = None
    total_verifications: int = Field(0, description="Total successful verifications")
    nfc_tag_id: int | None = None
    url_code: str | None = None

    class Config:
        from_attributes = True
