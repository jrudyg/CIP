#!/usr/bin/env python3
"""
Law Library RAG System
Legal Document Q&A and Analysis System
"""

import argparse
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

from ingestion.document_loader import LegalDocumentLoader
from ingestion.chunker import LegalTextChunker
from retrieval.vector_store import LegalVectorStore
from augmentation.llm_augmenter import LegalLLMAugmenter

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LawLibraryRAG:
    """Legal Document RAG Q&A System"""

    def __init__(
        self,
        data_dir='data/documents',
        persist_dir='data/vectorstore',
        legal_domain='general'
    ):
        """
        Initialize Law Library RAG System

        Args:
            data_dir: Directory containing legal documents
            persist_dir: Directory for vector store persistence
            legal_domain: Legal domain for analysis (general, contract, statute, etc.)
        """
        self.data_dir = Path(data_dir)
        self.persist_dir = Path(persist_dir)
        self.legal_domain = legal_domain

        # Initialize components
        self.vector_store = LegalVectorStore(persist_dir=str(self.persist_dir))
        self.augmenter = LegalLLMAugmenter(domain=legal_domain)
        self.chunker = LegalTextChunker(chunk_size=1500, chunk_overlap=300)

        logger.info(f"Law Library RAG initialized for domain: {legal_domain}")

    def ingest_documents(self):
        """Ingest all legal documents from data directory"""
        logger.info(f"Loading legal documents from {self.data_dir}")

        if not self.data_dir.exists():
            logger.error(f"Directory not found: {self.data_dir}")
            print(f"\nError: Directory not found: {self.data_dir}")
            print(f"Please create the directory and add legal documents (PDF, DOCX, TXT)\n")
            return False

        # Load documents
        loader = LegalDocumentLoader(str(self.data_dir))
        documents = loader.load_all()

        if not documents:
            logger.warning("No documents found to ingest")
            print(f"\nNo legal documents found in {self.data_dir}")
            print("Please add PDF, DOCX, or TXT files to the directory\n")
            return False

        logger.info(f"Loaded {len(documents)} legal documents")
        print(f"\nLoaded {len(documents)} legal documents")

        # Display document type breakdown
        doc_types = {}
        for doc in documents:
            doc_type = doc['metadata'].get('document_type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

        print("\nDocument Types:")
        for doc_type, count in sorted(doc_types.items()):
            print(f"  - {doc_type}: {count}")

        # Chunk documents
        chunks = []
        for doc in documents:
            doc_chunks = self.chunker.chunk_document(doc)
            chunks.extend(doc_chunks)

        logger.info(f"Created {len(chunks)} chunks")
        print(f"\nCreated {len(chunks)} chunks for indexing")

        # Add to vector store
        self.vector_store.add_documents(chunks)
        logger.info("Legal documents indexed successfully")
        print("\nLegal documents indexed successfully!")

        # Display collection stats
        stats = self.vector_store.get_collection_stats()
        print(f"\nCollection Statistics:")
        print(f"  Total chunks: {stats['total_documents']}")
        if 'document_types' in stats:
            print(f"  Document types: {stats['document_types']}")
        if 'jurisdictions' in stats:
            print(f"  Jurisdictions: {stats['jurisdictions']}")

        return True

    def query(
        self,
        question: str,
        top_k: int = 5,
        document_type: str = None,
        jurisdiction: str = None
    ):
        """
        Query the legal RAG system

        Args:
            question: User's legal question
            top_k: Number of relevant chunks to retrieve
            document_type: Optional filter by document type
            jurisdiction: Optional filter by jurisdiction
        """
        logger.info(f"Query: {question}")
        print(f"\n{'='*80}")
        print(f"QUESTION: {question}")
        print(f"{'='*80}\n")

        # Retrieve relevant documents with filters
        if document_type:
            relevant_docs = self.vector_store.search_by_document_type(
                question, document_type, top_k=top_k
            )
        elif jurisdiction:
            relevant_docs = self.vector_store.search_by_jurisdiction(
                question, jurisdiction, top_k=top_k
            )
        else:
            relevant_docs = self.vector_store.search(question, top_k=top_k)

        if not relevant_docs:
            error_msg = "No relevant documents found. Please ingest documents first using --ingest"
            logger.warning(error_msg)
            print(f"\n{error_msg}\n")
            return error_msg

        logger.info(f"Retrieved {len(relevant_docs)} relevant chunks")

        # Display sources
        print(f"SOURCES ({len(relevant_docs)} relevant documents):")
        for i, doc in enumerate(relevant_docs, 1):
            metadata = doc['metadata']
            source = metadata.get('filename', 'Unknown')
            doc_type = metadata.get('document_type', 'unknown')
            section = metadata.get('section', metadata.get('section_heading', ''))
            relevance = doc.get('relevance_score', 0)

            print(f"  {i}. {source} ({doc_type})")
            if section:
                print(f"     Section: {section}")
            if relevance:
                print(f"     Relevance: {relevance:.2%}")

        print(f"\n{'='*80}")
        print("LEGAL ANALYSIS:")
        print(f"{'='*80}\n")

        # Generate answer with legal analysis
        answer = self.augmenter.generate_answer(
            question=question,
            context_documents=relevant_docs
        )

        print(answer)
        print(f"\n{'='*80}\n")

        return answer

    def interactive_mode(self):
        """Run in interactive Q&A mode"""
        print("\n" + "="*80)
        print("LAW LIBRARY RAG - Interactive Mode")
        print("="*80)
        print(f"Legal Domain: {self.legal_domain}")
        print("\nCommands:")
        print("  - Type your question to get legal analysis")
        print("  - 'stats' - Show collection statistics")
        print("  - 'domain <type>' - Change legal domain (contract, statute, case_law, etc.)")
        print("  - 'help' - Show this help message")
        print("  - 'quit' or 'exit' - Exit interactive mode")
        print("="*80 + "\n")

        while True:
            try:
                question = input("Question: ").strip()

                if not question:
                    continue

                if question.lower() in ['quit', 'exit', 'q']:
                    print("\nExiting Law Library RAG. Goodbye!\n")
                    break

                if question.lower() == 'help':
                    print("\nAvailable commands:")
                    print("  - Ask any legal question")
                    print("  - 'stats' - Show collection statistics")
                    print("  - 'domain <type>' - Change domain")
                    print("  - 'quit' - Exit\n")
                    continue

                if question.lower() == 'stats':
                    stats = self.vector_store.get_collection_stats()
                    print("\nCollection Statistics:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
                    print()
                    continue

                if question.lower().startswith('domain '):
                    new_domain = question.split(maxsplit=1)[1].strip()
                    self.augmenter.set_domain(new_domain)
                    self.legal_domain = new_domain
                    print(f"\nChanged legal domain to: {new_domain}\n")
                    continue

                # Process question
                self.query(question)

            except KeyboardInterrupt:
                print("\n\nExiting Law Library RAG. Goodbye!\n")
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}")
                print(f"\nError: {e}\n")

    def search_by_citation(self, citation: str, top_k: int = 5):
        """
        Search for documents citing a specific legal authority

        Args:
            citation: Legal citation (e.g., "42 U.S.C. § 1983")
            top_k: Number of results
        """
        print(f"\nSearching for documents citing: {citation}\n")

        results = self.vector_store.search_by_citation(citation, top_k=top_k)

        if not results:
            print("No documents found citing this authority\n")
            return

        print(f"Found {len(results)} documents:\n")
        for i, doc in enumerate(results, 1):
            metadata = doc['metadata']
            source = metadata.get('filename', 'Unknown')
            doc_type = metadata.get('document_type', 'unknown')
            print(f"{i}. {source} ({doc_type})")

        print()


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(
        description='Law Library RAG - Legal Document Q&A System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest legal documents
  python src/main.py --ingest

  # Query the system
  python src/main.py --query "What are the requirements under 42 USC 1983?"

  # Interactive mode
  python src/main.py --interactive

  # Search by document type
  python src/main.py --query "breach of contract remedies" --type contract

  # Search by citation
  python src/main.py --citation "42 U.S.C. § 1983"
        """
    )

    parser.add_argument('--ingest', action='store_true',
                       help='Ingest legal documents from data directory')
    parser.add_argument('--query', type=str,
                       help='Query the legal RAG system')
    parser.add_argument('--citation', type=str,
                       help='Search for documents citing a specific legal authority')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive Q&A mode')
    parser.add_argument('--data-dir', default='data/documents',
                       help='Legal documents directory (default: data/documents)')
    parser.add_argument('--top-k', type=int, default=5,
                       help='Number of chunks to retrieve (default: 5)')
    parser.add_argument('--domain', default='general',
                       choices=['general', 'contract', 'statute', 'case_law', 'regulation', 'compliance'],
                       help='Legal domain for analysis (default: general)')
    parser.add_argument('--type', dest='doc_type',
                       help='Filter by document type (statute, contract, case_law, etc.)')
    parser.add_argument('--jurisdiction',
                       help='Filter by jurisdiction (e.g., California, Federal)')

    args = parser.parse_args()

    # Initialize RAG system
    rag = LawLibraryRAG(
        data_dir=args.data_dir,
        legal_domain=args.domain
    )

    # Execute commands
    if args.ingest:
        success = rag.ingest_documents()
        sys.exit(0 if success else 1)

    elif args.query:
        rag.query(
            args.query,
            top_k=args.top_k,
            document_type=args.doc_type,
            jurisdiction=args.jurisdiction
        )

    elif args.citation:
        rag.search_by_citation(args.citation, top_k=args.top_k)

    elif args.interactive:
        rag.interactive_mode()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
