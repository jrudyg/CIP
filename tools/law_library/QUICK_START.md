# Law Library RAG - Quick Start Guide

Get started with the Law Library RAG system in 5 minutes.

## 1. Install Dependencies

```bash
cd 01-active/law-library-rag
pip install -r requirements.txt
```

## 2. Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Anthropic or OpenAI API key
# Example for Anthropic (recommended):
ANTHROPIC_API_KEY=sk-ant-your-key-here
LLM_PROVIDER=anthropic
```

## 3. Ingest Sample Documents

The system includes three sample legal documents:
- **sample_statute.txt**: 42 U.S.C. § 1983 (Civil Rights)
- **sample_contract.txt**: Software Development Agreement
- **sample_case_opinion.txt**: Martinez v. Riverside County (Excessive Force)

```bash
python src/main.py --ingest
```

Expected output:
```
Loaded 3 legal documents

Document Types:
  - statute: 1
  - contract: 1
  - case_law: 1

Created 15 chunks for indexing

Legal documents indexed successfully!
```

## 4. Try Some Queries

### Query 1: Statute Question
```bash
python src/main.py --query "What are the elements of a Section 1983 claim?"
```

### Query 2: Contract Question
```bash
python src/main.py --domain contract --query "What are the payment terms?"
```

### Query 3: Case Law Question
```bash
python src/main.py --domain case_law --query "What was the court's decision on qualified immunity?"
```

### Query 4: Interactive Mode
```bash
python src/main.py --interactive
```

Then try:
- `What remedies are available under Section 1983?`
- `domain contract`
- `What are the termination provisions?`
- `stats`
- `quit`

## 5. Add Your Own Documents

Add your legal documents (PDF, DOCX, TXT) to the `data/documents/` directory:

```bash
# Example: Copy your documents
cp /path/to/your/legal/docs/*.pdf data/documents/

# Re-ingest to index new documents
python src/main.py --ingest
```

## Common Commands Reference

```bash
# Ingest documents
python src/main.py --ingest

# Basic query
python src/main.py --query "your question"

# Filter by document type
python src/main.py --query "your question" --type contract

# Filter by jurisdiction
python src/main.py --query "your question" --jurisdiction California

# Search by citation
python src/main.py --citation "42 U.S.C. § 1983"

# Interactive mode
python src/main.py --interactive

# Specify legal domain
python src/main.py --domain contract --query "your question"
```

## Available Legal Domains

- `general` - General legal research (default)
- `contract` - Contract analysis
- `statute` - Statutory interpretation
- `case_law` - Case law analysis
- `regulation` - Regulatory compliance
- `compliance` - Compliance checking

## Troubleshooting

**Problem**: "No LLM API key configured"
- **Solution**: Add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` to `.env` file

**Problem**: "No documents found to ingest"
- **Solution**: Add PDF, DOCX, or TXT files to `data/documents/` directory

**Problem**: "No relevant documents found"
- **Solution**: Run `python src/main.py --ingest` first to index documents

**Problem**: Unicode errors on Windows
- **Solution**: Known issue, does not affect functionality. Output is still correct.

## Next Steps

1. **Add more documents**: Copy your legal documents to `data/documents/`
2. **Customize domains**: Edit `llm_augmenter.py` to add custom legal analysis prompts
3. **Adjust chunking**: Modify chunk size in `chunker.py` for your documents
4. **Integrate**: Import modules in your own Python scripts

See [README.md](README.md) for complete documentation.

## Example Session

```bash
$ python src/main.py --ingest
Loading legal documents from data/documents
Loaded 3 legal documents

Document Types:
  - statute: 1
  - contract: 1
  - case_law: 1

Created 15 chunks for indexing
Legal documents indexed successfully!

$ python src/main.py --query "What are the remedies under Section 1983?"

================================================================================
QUESTION: What are the remedies under Section 1983?
================================================================================

SOURCES (3 relevant documents):
  1. sample_statute.txt (statute)
     Section: § 1983
     Relevance: 94.23%
  2. sample_statute.txt (statute)
     Section: REMEDIES
     Relevance: 91.15%
  3. sample_case_opinion.txt (case_law)
     Relevance: 78.42%

================================================================================
LEGAL ANALYSIS:
================================================================================

Based on 42 U.S.C. § 1983, successful plaintiffs may recover the following remedies:

**Damages:**
1. **Compensatory Damages** - For actual injuries suffered as a result of
   the constitutional violation
2. **Nominal Damages** - Available even for violations where no actual
   injury can be proven
3. **Punitive Damages** - Available in cases involving malicious or
   reckless conduct by the defendant

**Equitable Relief:**
4. **Injunctive Relief** - To prevent ongoing or future violations of
   constitutional rights (with limited exceptions for judicial officers)
5. **Declaratory Relief** - Declaration of rights and legal relationships

**Attorney's Fees:**
6. **Attorney's Fees and Costs** - Available under 42 U.S.C. § 1988 for
   prevailing parties

The statute specifically notes that injunctive relief cannot be granted
in actions against judicial officers for acts taken in their judicial
capacity, unless a declaratory decree was violated or declaratory relief
was unavailable.

These remedies are designed to provide both compensation for violations
and deterrence against future constitutional violations by state actors.

================================================================================

$ python src/main.py --interactive
[Interactive session starts...]
```

---

**Ready to get started?** Run `python src/main.py --ingest` now!
