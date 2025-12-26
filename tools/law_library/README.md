# Law Library RAG System

A sophisticated Retrieval-Augmented Generation (RAG) system specialized for legal document analysis, research, and question-answering.

## Features

### Legal Document Support
- **Document Types**: Statutes, contracts, regulations, case law, opinions, briefs
- **File Formats**: PDF, DOCX, TXT
- **Metadata Extraction**: Automatic detection of document type, citations, parties, dates, jurisdiction

### Advanced Legal Processing
- **Citation Extraction**: Automatically identifies US Code, CFR, case citations, Public Law references
- **Section-Aware Chunking**: Preserves legal document structure (sections, articles, clauses)
- **Jurisdiction Detection**: Identifies federal and state jurisdictions
- **Party Extraction**: Extracts parties from contracts and cases

### Specialized Legal Analysis
- **Domain-Specific Analysis**: Contract analysis, statutory interpretation, case law analysis, regulatory compliance
- **Legal Citation Support**: Search by citation, track cross-references
- **Context-Aware Responses**: LLM-powered analysis with legal reasoning and source citations

### Technical Capabilities
- **Vector Database**: ChromaDB for semantic search
- **LLM Integration**: Support for Claude Sonnet 4.5 and GPT-4
- **Interactive Mode**: CLI for interactive legal research
- **Filtering**: Search by document type, jurisdiction, or citation

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Clone or navigate to the project directory**:
   ```bash
   cd 01-active/law-library-rag
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

   Required environment variables:
   ```bash
   # Choose one or both LLM providers
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here

   # Select provider (anthropic or openai)
   LLM_PROVIDER=anthropic

   # Model configuration
   ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
   OPENAI_MODEL=gpt-4
   ```

## Usage

### 1. Ingest Legal Documents

Add your legal documents (PDF, DOCX, TXT) to the `data/documents/` directory, then run:

```bash
python src/main.py --ingest
```

This will:
- Load all documents from `data/documents/`
- Extract legal metadata (citations, parties, jurisdiction, document type)
- Chunk documents intelligently based on legal structure
- Index into the vector database

### 2. Query the System

**Basic Query**:
```bash
python src/main.py --query "What are the requirements under 42 USC 1983?"
```

**Filter by Document Type**:
```bash
python src/main.py --query "breach of contract remedies" --type contract
```

**Filter by Jurisdiction**:
```bash
python src/main.py --query "employment law requirements" --jurisdiction California
```

**Search by Citation**:
```bash
python src/main.py --citation "42 U.S.C. § 1983"
```

### 3. Interactive Mode

For continuous legal research:

```bash
python src/main.py --interactive
```

Interactive commands:
- Type any legal question to get analysis
- `stats` - Show collection statistics
- `domain <type>` - Change legal domain (contract, statute, case_law, regulation, compliance)
- `help` - Show help
- `quit` or `exit` - Exit interactive mode

### 4. Specialized Analysis

**Contract Analysis**:
```bash
python src/main.py --domain contract --query "What are the termination provisions?"
```

**Statutory Interpretation**:
```bash
python src/main.py --domain statute --query "What does section 5 require?"
```

**Case Law Analysis**:
```bash
python src/main.py --domain case_law --query "What was the court's holding?"
```

**Compliance Check**:
```bash
python src/main.py --domain compliance --query "What are the compliance requirements?"
```

## Architecture

### Components

```
law-library-rag/
├── src/
│   ├── main.py                          # Main CLI interface
│   ├── ingestion/
│   │   ├── document_loader.py           # Legal document loader with metadata extraction
│   │   └── chunker.py                   # Legal-aware text chunking
│   ├── retrieval/
│   │   └── vector_store.py              # ChromaDB vector database
│   └── augmentation/
│       └── llm_augmenter.py             # LLM-powered legal analysis
├── data/
│   ├── documents/                       # Legal documents (add your files here)
│   └── vectorstore/                     # ChromaDB persistent storage
├── requirements.txt                     # Python dependencies
├── .env.example                         # Environment configuration template
└── README.md                            # This file
```

### Document Processing Pipeline

1. **Loading**: Documents are loaded and parsed (PDF, DOCX, TXT)
2. **Metadata Extraction**: Legal metadata extracted (type, citations, parties, jurisdiction)
3. **Chunking**: Documents chunked intelligently based on legal structure
4. **Embedding**: Chunks embedded and stored in ChromaDB
5. **Retrieval**: Semantic search retrieves relevant chunks
6. **Analysis**: LLM generates legal analysis with citations

### Legal Metadata

The system automatically extracts:
- **Document Type**: statute, contract, regulation, case_law, opinion, brief
- **Citations**: US Code, CFR, case citations, Public Law references
- **Parties**: Contract parties or case parties
- **Dates**: Effective dates, signing dates
- **Jurisdiction**: Federal or state jurisdiction
- **Sections**: Section numbers and headings

### Legal Domains

The system supports specialized analysis for different legal domains:

| Domain | Description | Use Case |
|--------|-------------|----------|
| `general` | General legal research | Default, multi-purpose |
| `contract` | Contract analysis | Terms, obligations, risks |
| `statute` | Statutory interpretation | Plain meaning, structure |
| `case_law` | Case law analysis | Holdings, reasoning |
| `regulation` | Regulatory compliance | Requirements, obligations |
| `compliance` | Compliance checking | Risk assessment |

## Examples

### Example 1: Contract Analysis

```bash
# Add contract PDFs to data/documents/
python src/main.py --ingest

# Query with contract domain
python src/main.py --domain contract --query "What are the payment terms and conditions?"
```

Output includes:
- Direct answer with specific clause citations
- Risk analysis
- Key terms and obligations
- Source document references

### Example 2: Statutory Research

```bash
# Add statute documents
python src/main.py --ingest

# Query specific statute
python src/main.py --domain statute --query "What are the elements required under Section 1983?"
```

Output includes:
- Plain meaning interpretation
- Required elements
- Statutory structure analysis
- Cross-references

### Example 3: Multi-Jurisdiction Research

```bash
# Interactive mode for continuous research
python src/main.py --interactive

# In interactive mode:
Question: employment discrimination laws
Question: domain statute
Question: What are the federal requirements?
Question: What are the California requirements?
Question: quit
```

## Advanced Features

### Citation Tracking

The system tracks legal citations and enables citation-based search:

```python
# In Python code
from src.retrieval.vector_store import LegalVectorStore

store = LegalVectorStore()
docs = store.search_by_citation("42 U.S.C. § 1983", top_k=10)
```

### Custom Chunking

Legal documents are chunked based on their structure:
- **Statutes/Regulations**: Split by sections (§, Section, Sec.)
- **Contracts**: Split by articles, sections, clauses
- **Opinions/Briefs**: Split by paragraphs with context preservation

Chunking preserves:
- Section numbers and headings
- Legal citations within chunks
- Context overlap for continuity

### Metadata Filtering

Filter searches by metadata:

```python
# Search only contracts
store.search_by_document_type("indemnification clause", "contract")

# Search within jurisdiction
store.search_by_jurisdiction("employment law", "California")
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | None |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `LLM_PROVIDER` | LLM provider (anthropic/openai) | anthropic |
| `ANTHROPIC_MODEL` | Claude model name | claude-sonnet-4-5-20250929 |
| `OPENAI_MODEL` | OpenAI model name | gpt-4 |
| `CHROMA_PERSIST_DIR` | ChromaDB storage directory | data/vectorstore |
| `JURISDICTION` | Default jurisdiction | US |
| `LEGAL_DOMAIN` | Default legal domain | general |

### Chunking Parameters

Customize in code:

```python
chunker = LegalTextChunker(
    chunk_size=1500,      # Target chunk size (legal docs need larger chunks)
    chunk_overlap=300     # Overlap to preserve context
)
```

### Retrieval Parameters

```bash
# Retrieve more chunks for complex questions
python src/main.py --query "complex question" --top-k 10
```

## Legal Disclaimer

This system is designed for legal research and analysis assistance. It does not provide legal advice and should not be used as a substitute for consultation with a qualified attorney. Always verify legal analysis with primary sources and consult with legal professionals for specific legal matters.

## Troubleshooting

### No documents found
- Ensure documents are in `data/documents/` directory
- Verify file formats are PDF, DOCX, or TXT
- Check file permissions

### API errors
- Verify API keys in `.env` file
- Check API key validity and quotas
- Ensure internet connectivity

### Poor search results
- Ingest more documents for better coverage
- Increase `--top-k` parameter
- Use more specific queries
- Filter by document type or jurisdiction

### Unicode errors (Windows)
- Known issue with Windows console encoding
- Does not affect functionality
- Output is still correct despite warning messages

## Development

### Testing

Create test legal documents in `data/documents/`:

```bash
# Example statute
echo "Section 1. Definitions..." > data/documents/test_statute.txt

# Example contract
echo "AGREEMENT between Party A and Party B..." > data/documents/test_contract.txt

# Ingest and test
python src/main.py --ingest
python src/main.py --query "test question"
```

### Extending

To add new legal document types:

1. Update `DOCUMENT_TYPES` in `document_loader.py`
2. Add extraction patterns in `_extract_citations()`
3. Add domain-specific prompts in `llm_augmenter.py`
4. Update chunking logic in `chunker.py` if needed

## License

Part of the Claude Workspace Repository System.

## Support

For issues or questions:
1. Check this README
2. Review code comments in source files
3. Check CCE workspace documentation in `06-documentation/`

---

**Version**: 1.0.0
**Status**: Production-ready
**Last Updated**: 2025-01-16
