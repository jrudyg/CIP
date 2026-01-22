"""
Core data structures for PDF metadata extraction results.

All extraction results are stored in dataclasses for type safety and clarity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class ExecutionStatus(Enum):
    """Contract execution status classification"""
    FULLY_EXECUTED = "fully_executed"        # All required signatures present & valid
    PARTIALLY_EXECUTED = "partially_executed" # Some signatures present, not all
    UNSIGNED = "unsigned"                     # No signatures or all fields empty
    INVALID = "invalid"                       # Signatures present but validation failed
    UNKNOWN = "unknown"                       # Cannot determine (encrypted, corrupted, etc.)


@dataclass
class DocumentMetadata:
    """PDF document metadata from /Info dictionary"""
    filename: str
    file_path: str
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    author: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creator: Optional[str] = None          # Application that created PDF
    producer: Optional[str] = None          # PDF producer (Adobe, etc.)
    pdf_version: Optional[str] = None
    page_count: int = 0
    file_size_bytes: int = 0
    is_encrypted: bool = False
    confidence: int = 0                     # 0-100%
    notes: str = ""
    error: Optional[str] = None


@dataclass
class DigitalSignature:
    """Digital signature information extracted from PDF"""
    signature_name: str                     # Field name
    signer_name: Optional[str] = None       # From certificate
    signing_time: Optional[datetime] = None
    signature_type: str = "unknown"         # adbe.pkcs7.detached, DocuSign, etc.
    certificate_issuer: Optional[str] = None
    certificate_subject: Optional[str] = None
    certificate_serial: Optional[str] = None
    certificate_valid_from: Optional[datetime] = None
    certificate_valid_to: Optional[datetime] = None
    is_valid: Optional[bool] = None         # Validation status
    validation_errors: List[str] = field(default_factory=list)
    signature_covers_document: bool = False
    modification_detection: Optional[str] = None
    confidence: int = 0                     # 0-100%
    notes: str = ""


@dataclass
class FormField:
    """PDF form field (AcroForm)"""
    field_name: str
    field_type: str                         # Text, Button, Choice, Signature
    field_value: Optional[str] = None
    is_required: bool = False
    is_read_only: bool = False
    page_number: int = 0
    coordinates: Optional[Dict[str, float]] = None
    confidence: int = 100                   # Form fields are structural data


@dataclass
class Annotation:
    """PDF annotation (comment, highlight, stamp)"""
    annotation_type: str                    # Comment, Highlight, Stamp, etc.
    content: Optional[str] = None
    author: Optional[str] = None
    creation_date: Optional[datetime] = None
    page_number: int = 0
    coordinates: Optional[Dict[str, float]] = None


@dataclass
class PageMetadata:
    """Page-level metadata"""
    page_number: int
    width: float
    height: float
    rotation: int = 0                       # 0, 90, 180, 270
    has_text: bool = False
    has_images: bool = False


@dataclass
class ImageSignatureDetection:
    """Vision API detected signature from scanned document"""
    page_number: int
    signature_detected: bool = False
    signer_name: Optional[str] = None
    date: Optional[str] = None
    location: Optional[Dict[str, float]] = None  # Bounding box
    confidence: int = 0                     # 0-100%
    notes: str = ""


@dataclass
class PDFMetadataResult:
    """Top-level result containing all extracted metadata"""
    document_metadata: DocumentMetadata
    digital_signatures: List[DigitalSignature] = field(default_factory=list)
    form_fields: List[FormField] = field(default_factory=list)
    annotations: List[Annotation] = field(default_factory=list)
    page_metadata: List[PageMetadata] = field(default_factory=list)
    image_signatures: List[ImageSignatureDetection] = field(default_factory=list)

    # Summary flags
    has_digital_signatures: bool = False
    has_valid_signatures: bool = False
    has_form_fields: bool = False
    execution_status: ExecutionStatus = ExecutionStatus.UNKNOWN
    execution_confidence: int = 0           # 0-100%

    # Signature completeness tracking
    total_signature_fields: int = 0         # Total signature fields found
    signed_signature_fields: int = 0        # Number of fields with signatures

    # Metadata
    extraction_timestamp: datetime = field(default_factory=datetime.now)
    processing_time_seconds: float = 0.0
    overall_confidence: int = 0             # 0-100%
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON export"""
        return {
            'document_metadata': {
                'filename': self.document_metadata.filename,
                'file_path': self.document_metadata.file_path,
                'creation_date': self.document_metadata.creation_date.isoformat() if self.document_metadata.creation_date else None,
                'modification_date': self.document_metadata.modification_date.isoformat() if self.document_metadata.modification_date else None,
                'author': self.document_metadata.author,
                'title': self.document_metadata.title,
                'subject': self.document_metadata.subject,
                'keywords': self.document_metadata.keywords,
                'creator': self.document_metadata.creator,
                'producer': self.document_metadata.producer,
                'pdf_version': self.document_metadata.pdf_version,
                'page_count': self.document_metadata.page_count,
                'file_size_bytes': self.document_metadata.file_size_bytes,
                'is_encrypted': self.document_metadata.is_encrypted,
                'confidence': self.document_metadata.confidence,
                'notes': self.document_metadata.notes,
                'error': self.document_metadata.error
            },
            'digital_signatures': [
                {
                    'signature_name': sig.signature_name,
                    'signer_name': sig.signer_name,
                    'signing_time': sig.signing_time.isoformat() if sig.signing_time else None,
                    'signature_type': sig.signature_type,
                    'certificate_issuer': sig.certificate_issuer,
                    'certificate_subject': sig.certificate_subject,
                    'certificate_serial': sig.certificate_serial,
                    'certificate_valid_from': sig.certificate_valid_from.isoformat() if sig.certificate_valid_from else None,
                    'certificate_valid_to': sig.certificate_valid_to.isoformat() if sig.certificate_valid_to else None,
                    'is_valid': sig.is_valid,
                    'validation_errors': sig.validation_errors,
                    'signature_covers_document': sig.signature_covers_document,
                    'modification_detection': sig.modification_detection,
                    'confidence': sig.confidence,
                    'notes': sig.notes
                }
                for sig in self.digital_signatures
            ],
            'form_fields': [
                {
                    'field_name': field.field_name,
                    'field_type': field.field_type,
                    'field_value': field.field_value,
                    'is_required': field.is_required,
                    'is_read_only': field.is_read_only,
                    'page_number': field.page_number,
                    'coordinates': field.coordinates,
                    'confidence': field.confidence
                }
                for field in self.form_fields
            ],
            'has_digital_signatures': self.has_digital_signatures,
            'has_valid_signatures': self.has_valid_signatures,
            'has_form_fields': self.has_form_fields,
            'execution_status': self.execution_status.value,
            'execution_confidence': self.execution_confidence,
            'total_signature_fields': self.total_signature_fields,
            'signed_signature_fields': self.signed_signature_fields,
            'extraction_timestamp': self.extraction_timestamp.isoformat(),
            'processing_time_seconds': self.processing_time_seconds,
            'overall_confidence': self.overall_confidence,
            'error': self.error
        }
