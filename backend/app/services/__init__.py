# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create NFC Tag service layer
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P1

"""
NFC Tag service layer - extracted business logic from API routes.

This module contains all business logic for NFC tags:
- URL code generation
- Tag creation with validation
- Tag updates with URL regeneration
- Tag approval/rejection
"""

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models import SKU, CulturalProduct, NFCTag, Video


class NFCTagService:
    """Service for NFC Tag business logic."""

    def __init__(self, db: Session):
        self.db = db

    def generate_url_code(
        self,
        cultural_product: CulturalProduct,
        video: Video,
        sku: SKU | None = None,
    ) -> str:
        """Generate URL code in format {cp_code}_{video_code}_{sku_code}."""
        if sku:
            return f"{cultural_product.code}_{video.code}_{sku.code}"
        return f"{cultural_product.code}_{video.code}"

    def get_nfc_tags(
        self,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        approval_status: str | None = None,
        cultural_product_id: int | None = None,
    ) -> tuple[list[NFCTag], int]:
        """Get NFC tags with filters and pagination."""
        query = self.db.query(NFCTag)
        if status:
            query = query.filter(NFCTag.status == status)
        if approval_status:
            query = query.filter(NFCTag.approval_status == approval_status)
        if cultural_product_id:
            query = query.filter(NFCTag.cultural_product_id == cultural_product_id)

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_nfc_tag_or_404(self, tag_id: int) -> NFCTag:
        """Get NFC tag by ID or raise 404."""
        tag = self.db.query(NFCTag).filter(NFCTag.id == tag_id).first()
        if not tag:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NFC标签不存在")
        return tag

    def create_nfc_tag(
        self,
        cultural_product_id: int,
        video_id: int,
        sku_id: int | None,
        user_id: int,
        expires_at: date | None,
    ) -> NFCTag:
        """Create a new NFC tag with validation."""
        from fastapi import HTTPException, status

        # Verify cultural product exists
        product = self.db.query(CulturalProduct).filter(
            CulturalProduct.id == cultural_product_id
        ).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文创品不存在")

        # Verify video exists
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="视频不存在")

        # Get SKU code if provided
        sku_code = None
        if sku_id:
            sku = self.db.query(SKU).filter(SKU.id == sku_id).first()
            if not sku:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU不存在")
            sku_code = sku.code

        # Generate URL code
        url_code = self.generate_url_code(product, video, sku_code)

        # Check if URL code already exists
        existing = self.db.query(NFCTag).filter(NFCTag.url_code == url_code).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该URL码已存在")

        # Create tag
        tag = NFCTag(
            url_code=url_code,
            cultural_product_id=cultural_product_id,
            video_id=video_id,
            sku_id=sku_id,
            status="active",
            approval_status="pending",
            created_by=user_id,
            expires_at=expires_at,
        )
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def update_nfc_tag(
        self,
        tag_id: int,
        video_id: int | None,
        sku_id: int | None,
        status: str | None,
    ) -> NFCTag:
        """Update NFC tag with URL regeneration if needed."""
        from fastapi import HTTPException, status

        tag = self.get_nfc_tag_or_404(tag_id)

        update_data = {}
        new_video_id = video_id if video_id else tag.video_id
        new_sku_id = sku_id  # Can be None to clear SKU

        if video_id or sku_id is not None:
            # Verify video if changing
            video = self.db.query(Video).filter(Video.id == new_video_id).first()
            if not video:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="视频不存在")

            # Get product for URL generation
            product = self.db.query(CulturalProduct).filter(
                CulturalProduct.id == tag.cultural_product_id
            ).first()
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文创品不存在")

            # Get SKU code
            sku_code = None
            if new_sku_id:
                sku = self.db.query(SKU).filter(SKU.id == new_sku_id).first()
                if not sku:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU不存在")
                sku_code = sku.code
            elif tag.sku_id:
                existing_sku = self.db.query(SKU).filter(SKU.id == tag.sku_id).first()
                if existing_sku:
                    sku_code = existing_sku.code

            # Generate new URL code
            new_url_code = self.generate_url_code(product, video, sku_code)

            # Check for conflicts
            existing = self.db.query(NFCTag).filter(
                NFCTag.url_code == new_url_code,
                NFCTag.id != tag_id,
            ).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该URL码已存在")

            update_data["url_code"] = new_url_code

        if video_id:
            update_data["video_id"] = video_id
        if sku_id is not None:
            update_data["sku_id"] = sku_id
        if status:
            update_data["status"] = status

        for key, value in update_data.items():
            setattr(tag, key, value)

        self.db.commit()
        self.db.refresh(tag)
        return tag

    def delete_nfc_tag(self, tag_id: int) -> None:
        """Delete NFC tag."""
        tag = self.get_nfc_tag_or_404(tag_id)
        self.db.delete(tag)
        self.db.commit()

    def approve_nfc_tag(self, tag_id: int, user_id: int) -> NFCTag:
        """Approve NFC tag."""
        tag = self.get_nfc_tag_or_404(tag_id)

        if tag.approval_status == "approved":
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该标签已审批通过")

        tag.approval_status = "approved"
        tag.approved_by = user_id
        tag.approved_at = datetime.utcnow().date()
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def reject_nfc_tag(self, tag_id: int, user_id: int) -> NFCTag:
        """Reject NFC tag."""
        tag = self.get_nfc_tag_or_404(tag_id)

        if tag.approval_status == "rejected":
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该标签已驳回")

        tag.approval_status = "rejected"
        tag.approved_by = user_id
        tag.approved_at = datetime.utcnow().date()
        self.db.commit()
        self.db.refresh(tag)
        return tag
