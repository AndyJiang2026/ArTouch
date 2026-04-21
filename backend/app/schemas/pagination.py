# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create generic paginated response schema
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P2

"""Generic pagination schemas."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response with items and total count.

    This allows the frontend to correctly display pagination controls
    instead of always showing page size as the total.
    """
    items: list[T]
    total: int
    page: int
    page_size: int
