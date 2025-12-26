"""Legal Vector Store - ChromaDB for legal document similarity search"""

import logging
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class LegalVectorStore:
    """Vector database for legal document semantic search"""

    def __init__(self, persist_dir: str = 'data/vectorstore', collection_name: str = 'legal_documents'):
        """
        Initialize legal vector store

        Args:
            persist_dir: Directory for persistent storage
            collection_name: Name of the ChromaDB collection
        """
        self.persist_dir = persist_dir
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(f"Initialized legal vector store: {collection_name}")

    def add_documents(self, documents: List[Dict]):
        """
        Add legal documents to vector store with enhanced metadata

        Args:
            documents: List of dicts with 'content' and 'metadata'
        """
        if not documents:
            logger.warning("No documents to add")
            return

        # Clear existing collection first (for re-indexing)
        count = self.collection.count()
        if count > 0:
            logger.info(f"Clearing {count} existing documents for re-indexing")
            self.clear()

        # Prepare data
        ids = []
        contents = []
        metadatas = []

        for i, doc in enumerate(documents):
            # Generate unique ID
            source = doc['metadata'].get('filename', f'doc_{i}')
            chunk_id = doc['metadata'].get('chunk_index', doc['metadata'].get('section', i))
            doc_id = f"{source}_{chunk_id}_{i}"

            # Prepare metadata (ChromaDB only accepts string/int/float values)
            metadata = self._prepare_metadata(doc['metadata'])

            ids.append(doc_id)
            contents.append(doc['content'])
            metadatas.append(metadata)

        # Add to collection in batches (ChromaDB performs better with batching)
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_contents = contents[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]

            self.collection.add(
                ids=batch_ids,
                documents=batch_contents,
                metadatas=batch_metadatas
            )

        logger.info(f"Added {len(documents)} legal documents to vector store")

    def search(self, query: str, top_k: int = 5, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Search for relevant legal documents

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters (e.g., {"document_type": "contract"})

        Returns:
            List of relevant document dicts with content, metadata, and relevance scores
        """
        try:
            # Build where clause for filtering
            where = filters if filters else None

            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, self.collection.count()),
                where=where
            )

            # Format results
            documents = []
            if results['documents'][0]:
                for i, content in enumerate(results['documents'][0]):
                    doc = {
                        'content': content,
                        'metadata': results['metadatas'][0][i],
                        'relevance_score': 1 - results['distances'][0][i] if 'distances' in results else None,
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    }
                    documents.append(doc)

            logger.info(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
            return documents

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def search_by_citation(self, citation: str, top_k: int = 5) -> List[Dict]:
        """
        Search for documents containing a specific legal citation

        Args:
            citation: Legal citation to search for
            top_k: Number of results to return

        Returns:
            List of documents containing the citation
        """
        # Search with citation as query
        query = f"documents citing {citation}"
        return self.search(query, top_k=top_k)

    def search_by_document_type(self, query: str, doc_type: str, top_k: int = 5) -> List[Dict]:
        """
        Search within a specific document type

        Args:
            query: Search query
            doc_type: Document type (statute, contract, case_law, etc.)
            top_k: Number of results

        Returns:
            List of relevant documents of the specified type
        """
        filters = {"document_type": doc_type}
        return self.search(query, top_k=top_k, filters=filters)

    def search_by_jurisdiction(self, query: str, jurisdiction: str, top_k: int = 5) -> List[Dict]:
        """
        Search within a specific jurisdiction

        Args:
            query: Search query
            jurisdiction: Jurisdiction (e.g., "California", "Federal")
            top_k: Number of results

        Returns:
            List of relevant documents from the jurisdiction
        """
        filters = {"jurisdiction": jurisdiction}
        return self.search(query, top_k=top_k, filters=filters)

    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the legal document collection

        Returns:
            Dict with collection statistics
        """
        count = self.collection.count()

        stats = {
            'total_documents': count,
            'collection_name': self.collection_name,
            'persist_dir': self.persist_dir
        }

        # Try to get document type breakdown
        try:
            # Get sample of documents to analyze
            sample = self.collection.peek(limit=min(count, 100))
            if sample['metadatas']:
                doc_types = {}
                jurisdictions = {}

                for metadata in sample['metadatas']:
                    # Count document types
                    doc_type = metadata.get('document_type', 'unknown')
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

                    # Count jurisdictions
                    jurisdiction = metadata.get('jurisdiction', 'unknown')
                    if jurisdiction != 'unknown':
                        jurisdictions[jurisdiction] = jurisdictions.get(jurisdiction, 0) + 1

                stats['document_types'] = doc_types
                stats['jurisdictions'] = jurisdictions

        except Exception as e:
            logger.warning(f"Could not get detailed stats: {e}")

        return stats

    def clear(self):
        """Clear all documents from store"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Legal vector store cleared")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")

    def _prepare_metadata(self, metadata: Dict) -> Dict:
        """
        Prepare metadata for ChromaDB (only string/int/float values)

        Args:
            metadata: Original metadata dict

        Returns:
            Cleaned metadata dict
        """
        clean_metadata = {}

        for key, value in metadata.items():
            # Skip complex types (lists, dicts, None)
            if value is None:
                continue
            elif isinstance(value, (list, dict)):
                # Convert to string representation
                clean_metadata[key] = str(value)
            elif isinstance(value, (str, int, float, bool)):
                clean_metadata[key] = value
            else:
                # Convert other types to string
                clean_metadata[key] = str(value)

        return clean_metadata
