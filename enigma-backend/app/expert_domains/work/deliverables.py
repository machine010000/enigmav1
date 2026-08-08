from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DeliverableType(str, Enum):
    """Generic types of deliverables."""
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    DASHBOARD = "dashboard"
    DATASET = "dataset"
    CONFIGURATION = "configuration"
    REPORT = "report"
    CHECKLIST = "checklist"
    CODE = "code"
    DESIGN = "design"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    ARCHIVE = "archive"


class DeliverableFormat(str, Enum):
    """Formats for deliverables."""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    HTML = "html"
    MARKDOWN = "markdown"
    ZIP = "zip"
    TAR = "tar"
    MP4 = "mp4"
    MP3 = "mp3"
    PNG = "png"
    JPG = "jpg"
    SVG = "svg"


class DeliverableStatus(str, Enum):
    """Status for deliverables."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELIVERED = "delivered"


@dataclass(frozen=True)
class Deliverable:
    """A deliverable definition."""
    deliverable_id: str
    name: str
    description: str
    deliverable_type: DeliverableType
    format: DeliverableFormat
    expected_audience: str
    quality_standard: str
    validation_method: str
    acceptance_rules: List[str] = field(default_factory=list)
    required_sections: List[str] = field(default_factory=list)
    optional_sections: List[str] = field(default_factory=list)
    estimated_size: Optional[str] = None
    delivery_format: str = "digital"  # digital, physical, both
    revision_policy: str = "allow"  # allow, restricted, none
    retention_period: Optional[str] = None
    confidentiality: str = "standard"  # standard, confidential, secret
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeliverableInstance:
    """An instance of a deliverable (produced output)."""
    instance_id: str
    deliverable_id: str
    work_id: str
    status: DeliverableStatus = DeliverableStatus.NOT_STARTED
    version: str = "1.0"
    location: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    revision_notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeliverableRequirement:
    """Requirement for a deliverable."""
    requirement_id: str
    deliverable_id: str
    requirement_type: str  # content, format, quality, timeline
    description: str
    is_mandatory: bool = True
    validation_method: str = ""
    priority: str = "medium"  # low, medium, high, critical
