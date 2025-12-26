"""Legal document ingestion modules"""

from .document_loader import LegalDocumentLoader
from .chunker import LegalTextChunker

__all__ = ['LegalDocumentLoader', 'LegalTextChunker']
