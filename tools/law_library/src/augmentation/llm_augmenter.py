"""Legal LLM Augmenter - Generate legal analysis using retrieved context"""

import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class LegalLLMAugmenter:
    """Generate legal analysis and answers using LLM with retrieved context"""

    # Legal domain system prompts
    LEGAL_SYSTEM_PROMPTS = {
        'general': """You are a legal research assistant. Provide accurate, well-reasoned legal analysis based on the provided documents. Always cite specific sources and sections when making legal arguments. If the answer cannot be determined from the provided context, clearly state this limitation.""",

        'contract': """You are a contract analysis expert. When analyzing contracts:
- Identify key terms, obligations, and rights
- Note important dates, parties, and conditions
- Highlight potential ambiguities or risks
- Reference specific clauses and sections
- Consider standard contract law principles
Always cite the specific contract sections you reference.""",

        'statute': """You are a statutory interpretation expert. When analyzing statutes:
- Identify the plain meaning of the text
- Note definitions and key terms
- Consider the statute's structure and organization
- Identify cross-references and related provisions
- Apply standard canons of statutory construction
Always cite specific section numbers and subsections.""",

        'case_law': """You are a case law analyst. When analyzing judicial opinions:
- Identify the holding and key legal principles
- Note the facts and procedural history
- Distinguish between holding and dicta
- Identify the court's reasoning
- Note any dissents or concurrences
Always cite the case name and relevant portions of the opinion.""",

        'regulation': """You are a regulatory compliance expert. When analyzing regulations:
- Identify compliance requirements and obligations
- Note effective dates and applicability
- Identify definitions and key terms
- Consider the regulatory framework and structure
- Note enforcement mechanisms and penalties
Always cite specific CFR sections and subsections.""",

        'compliance': """You are a legal compliance advisor. When analyzing for compliance:
- Identify applicable legal requirements
- Note potential compliance risks or gaps
- Consider jurisdictional issues
- Identify documentation requirements
- Suggest compliance best practices
Always cite the specific legal authorities that create obligations."""
    }

    def __init__(self, domain: str = 'general'):
        """
        Initialize legal LLM augmenter

        Args:
            domain: Legal domain (general, contract, statute, case_law, regulation, compliance)
        """
        self.domain = domain
        self.client = None
        self.model = None
        self.provider = None

        # Determine provider from environment
        provider = os.getenv('LLM_PROVIDER', 'anthropic').lower()

        # Initialize Anthropic client
        if provider == 'anthropic' and os.getenv('ANTHROPIC_API_KEY'):
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
                self.model = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-5-20250929')
                self.provider = 'anthropic'
                logger.info(f"Initialized Anthropic client with model: {self.model}")
            except ImportError:
                logger.error("anthropic package not installed. Run: pip install anthropic")

        # Fallback to OpenAI
        elif os.getenv('OPENAI_API_KEY'):
            try:
                import openai
                self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
                self.provider = 'openai'
                logger.info(f"Initialized OpenAI client with model: {self.model}")
            except ImportError:
                logger.error("openai package not installed. Run: pip install openai")

        if not self.client:
            logger.warning("No LLM API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")

    def generate_answer(self, question: str, context_documents: List[Dict], analysis_type: Optional[str] = None) -> str:
        """
        Generate legal answer using LLM with retrieved context

        Args:
            question: User's question
            context_documents: Retrieved relevant legal documents
            analysis_type: Optional analysis type override (contract, statute, etc.)

        Returns:
            Generated legal analysis
        """
        if not self.client:
            return "Error: No LLM API key configured. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env"

        # Use specified analysis type or default domain
        domain = analysis_type or self.domain

        # Build context from documents
        context = self._build_legal_context(context_documents)

        # Build prompt
        prompt = self._build_legal_prompt(question, context, domain)

        # Generate answer
        if self.provider == 'anthropic':
            return self._generate_with_claude(prompt, domain)
        else:
            return self._generate_with_openai(prompt, domain)

    def analyze_contract(self, question: str, context_documents: List[Dict]) -> str:
        """
        Specialized contract analysis

        Args:
            question: Contract analysis question
            context_documents: Contract documents

        Returns:
            Contract analysis
        """
        return self.generate_answer(question, context_documents, analysis_type='contract')

    def interpret_statute(self, question: str, context_documents: List[Dict]) -> str:
        """
        Specialized statutory interpretation

        Args:
            question: Statutory interpretation question
            context_documents: Statute documents

        Returns:
            Statutory interpretation
        """
        return self.generate_answer(question, context_documents, analysis_type='statute')

    def analyze_case_law(self, question: str, context_documents: List[Dict]) -> str:
        """
        Specialized case law analysis

        Args:
            question: Case law question
            context_documents: Case law documents

        Returns:
            Case law analysis
        """
        return self.generate_answer(question, context_documents, analysis_type='case_law')

    def check_compliance(self, question: str, context_documents: List[Dict]) -> str:
        """
        Specialized compliance analysis

        Args:
            question: Compliance question
            context_documents: Regulatory documents

        Returns:
            Compliance analysis
        """
        return self.generate_answer(question, context_documents, analysis_type='compliance')

    def _build_legal_context(self, documents: List[Dict]) -> str:
        """Build legal context string from documents with citations"""
        context_parts = []

        for i, doc in enumerate(documents, 1):
            metadata = doc['metadata']

            # Build source citation
            source = metadata.get('filename', metadata.get('source', 'Unknown'))
            doc_type = metadata.get('document_type', 'document')
            section = metadata.get('section', metadata.get('section_heading', ''))

            # Build header with metadata
            header = f"[Source {i}: {source}"
            if doc_type != 'unknown':
                header += f" ({doc_type})"
            if section:
                header += f" - {section}"
            header += "]"

            # Add citation count if available
            citation_count = metadata.get('citation_count', 0)
            if citation_count > 0:
                header += f" [Contains {citation_count} legal citations]"

            # Add jurisdiction if available
            jurisdiction = metadata.get('jurisdiction')
            if jurisdiction:
                header += f" [Jurisdiction: {jurisdiction}]"

            # Build full context entry
            content = doc['content']
            context_parts.append(f"{header}\n{content}")

        return '\n\n---\n\n'.join(context_parts)

    def _build_legal_prompt(self, question: str, context: str, domain: str) -> str:
        """Build legal analysis prompt for LLM"""
        # Get domain-specific instructions
        system_context = self.LEGAL_SYSTEM_PROMPTS.get(domain, self.LEGAL_SYSTEM_PROMPTS['general'])

        prompt = f"""{system_context}

Based on the legal documents provided below, please answer the following question. Provide a thorough analysis with specific citations to the source documents.

LEGAL DOCUMENTS:
{context}

QUESTION: {question}

ANALYSIS:
Please provide your analysis following these guidelines:
1. Answer the question directly and clearly
2. Cite specific sources, sections, and provisions
3. Explain your legal reasoning
4. Note any relevant citations or cross-references in the documents
5. Identify any limitations or gaps in the available information
6. If applicable, discuss different interpretations or potential arguments

Your response:"""

        return prompt

    def _generate_with_claude(self, prompt: str, domain: str) -> str:
        """Generate legal analysis using Claude"""
        try:
            # Get system prompt for domain
            system_prompt = self.LEGAL_SYSTEM_PROMPTS.get(domain, self.LEGAL_SYSTEM_PROMPTS['general'])

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,  # Longer responses for legal analysis
                temperature=0.3,   # Lower temperature for more focused legal analysis
                system=system_prompt,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }]
            )
            return response.content[0].text

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return f"Error generating legal analysis: {e}"

    def _generate_with_openai(self, prompt: str, domain: str) -> str:
        """Generate legal analysis using OpenAI"""
        try:
            # Get system prompt for domain
            system_prompt = self.LEGAL_SYSTEM_PROMPTS.get(domain, self.LEGAL_SYSTEM_PROMPTS['general'])

            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.3,  # Lower temperature for more focused legal analysis
                messages=[
                    {
                        'role': 'system',
                        'content': system_prompt
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error generating legal analysis: {e}"

    def set_domain(self, domain: str):
        """
        Change the legal domain for analysis

        Args:
            domain: Legal domain (general, contract, statute, case_law, regulation, compliance)
        """
        if domain in self.LEGAL_SYSTEM_PROMPTS:
            self.domain = domain
            logger.info(f"Changed legal domain to: {domain}")
        else:
            logger.warning(f"Unknown domain: {domain}. Available: {list(self.LEGAL_SYSTEM_PROMPTS.keys())}")
