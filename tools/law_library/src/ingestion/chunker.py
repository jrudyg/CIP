"""Legal Text Chunker - Split legal documents into semantic chunks"""

import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)


class LegalTextChunker:
    """Split legal text into chunks preserving legal structure"""

    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 300):
        """
        Initialize legal text chunker

        Args:
            chunk_size: Target size for chunks (legal docs need larger chunks)
            chunk_overlap: Overlap between chunks to preserve context
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: Dict) -> List[Dict]:
        """
        Chunk a legal document into semantic pieces

        Args:
            document: Document dict with 'content' and 'metadata'

        Returns:
            List of chunk dicts with enhanced metadata
        """
        content = document['content']
        metadata = document['metadata']
        doc_type = metadata.get('document_type', 'unknown')

        # Choose chunking strategy based on document type
        if doc_type in ['statute', 'regulation']:
            chunks = self._chunk_by_sections(content, metadata)
        elif doc_type == 'contract':
            chunks = self._chunk_by_contract_sections(content, metadata)
        elif doc_type in ['case_law', 'opinion']:
            chunks = self._chunk_by_paragraphs(content, metadata)
        else:
            chunks = self._chunk_by_paragraphs(content, metadata)

        logger.info(f"Split {doc_type} document into {len(chunks)} chunks")
        return chunks

    def _chunk_by_sections(self, content: str, metadata: Dict) -> List[Dict]:
        """
        Chunk statutes and regulations by sections
        Preserves section numbers and headings
        """
        chunks = []

        # Split by section markers (§, Section, Sec.)
        section_pattern = r'(?:§|Section|Sec\.)\s*(\d+(?:\.\d+)*)'
        sections = re.split(f'({section_pattern})', content)

        current_chunk = ""
        current_section = None

        for i, part in enumerate(sections):
            # Check if this is a section marker
            section_match = re.match(section_pattern, part)

            if section_match:
                # Save previous chunk if it exists
                if current_chunk and len(current_chunk) > 100:
                    chunk_metadata = metadata.copy()
                    if current_section:
                        chunk_metadata['section'] = current_section
                    chunks.append({
                        'content': current_chunk.strip(),
                        'metadata': chunk_metadata
                    })

                # Start new chunk with section marker
                current_section = part
                current_chunk = part
            else:
                # Add content to current chunk
                if len(current_chunk) + len(part) > self.chunk_size and current_chunk:
                    # Save current chunk
                    chunk_metadata = metadata.copy()
                    if current_section:
                        chunk_metadata['section'] = current_section
                    chunks.append({
                        'content': current_chunk.strip(),
                        'metadata': chunk_metadata
                    })

                    # Start new chunk with overlap
                    overlap = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                    current_chunk = overlap + part
                else:
                    current_chunk += part

        # Add final chunk
        if current_chunk and len(current_chunk) > 100:
            chunk_metadata = metadata.copy()
            if current_section:
                chunk_metadata['section'] = current_section
            chunks.append({
                'content': current_chunk.strip(),
                'metadata': chunk_metadata
            })

        # If no sections found, fall back to paragraph chunking
        if not chunks:
            return self._chunk_by_paragraphs(content, metadata)

        return chunks

    def _chunk_by_contract_sections(self, content: str, metadata: Dict) -> List[Dict]:
        """
        Chunk contracts by articles, sections, and clauses
        """
        chunks = []

        # Split by articles/sections (more flexible patterns)
        section_pattern = r'(?:ARTICLE|Article|SECTION|Section)\s+([IVXLCDM]+|\d+)[:\.]?\s*([^\n]*)'
        parts = re.split(f'({section_pattern})', content)

        current_chunk = ""
        current_heading = None

        i = 0
        while i < len(parts):
            part = parts[i]

            # Check if this matches a section heading
            heading_match = re.match(section_pattern, part)

            if heading_match:
                # Save previous chunk
                if current_chunk and len(current_chunk) > 100:
                    chunk_metadata = metadata.copy()
                    if current_heading:
                        chunk_metadata['section_heading'] = current_heading
                    chunks.append({
                        'content': current_chunk.strip(),
                        'metadata': chunk_metadata
                    })

                # Start new chunk with heading
                current_heading = part
                current_chunk = part
                i += 1
            else:
                # Regular content
                if len(current_chunk) + len(part) > self.chunk_size and current_chunk:
                    # Save chunk
                    chunk_metadata = metadata.copy()
                    if current_heading:
                        chunk_metadata['section_heading'] = current_heading
                    chunks.append({
                        'content': current_chunk.strip(),
                        'metadata': chunk_metadata
                    })

                    # Start new chunk with overlap
                    overlap = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                    current_chunk = overlap + part
                else:
                    current_chunk += part
                i += 1

        # Add final chunk
        if current_chunk and len(current_chunk) > 100:
            chunk_metadata = metadata.copy()
            if current_heading:
                chunk_metadata['section_heading'] = current_heading
            chunks.append({
                'content': current_chunk.strip(),
                'metadata': chunk_metadata
            })

        # Fallback if no sections detected
        if not chunks:
            return self._chunk_by_paragraphs(content, metadata)

        return chunks

    def _chunk_by_paragraphs(self, content: str, metadata: Dict) -> List[Dict]:
        """
        Chunk by paragraphs with overlap
        Default strategy for opinions, briefs, etc.
        """
        chunks = []

        # Split by paragraphs (double newline or numbered paragraphs)
        paragraphs = re.split(r'\n\s*\n|\n\s*\d+\.\s+', content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            # Check if adding paragraph exceeds chunk size
            if len(current_chunk) + len(para) + 4 > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = chunk_index
                chunks.append({
                    'content': current_chunk.strip(),
                    'metadata': chunk_metadata
                })

                # Start new chunk with overlap
                overlap = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap + '\n\n' + para
                chunk_index += 1
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += '\n\n' + para
                else:
                    current_chunk = para

        # Add final chunk
        if current_chunk:
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_index'] = chunk_index
            chunks.append({
                'content': current_chunk.strip(),
                'metadata': chunk_metadata
            })

        return chunks

    def extract_citations_from_chunk(self, chunk_content: str) -> List[str]:
        """
        Extract citations that appear in a specific chunk
        Useful for citation-based retrieval
        """
        citations = []

        # US Code
        citations.extend(re.findall(r'\d+\s+U\.S\.C\.\s+§\s+\d+(?:\([a-z0-9]+\))?', chunk_content))

        # Case citations
        citations.extend(re.findall(r'[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+,\s+\d+\s+[A-Z]\.\s*(?:\d+d\s+)?\d+', chunk_content))

        # CFR
        citations.extend(re.findall(r'\d+\s+C\.F\.R\.\s+§\s+[\d\.]+', chunk_content))

        # Public Law
        citations.extend(re.findall(r'Pub\.\s+L\.\s+No\.\s+\d+-\d+', chunk_content))

        return list(set(citations))
