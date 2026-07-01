"""
Citation manager for medical AI assistant.

Generates and validates citations for medical information.
"""

import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger


@dataclass
class Citation:
    """Citation information."""
    
    chunk_id: str
    source: str
    document_id: str
    section: str = ""
    similarity: float = 0.0
    rank: int = 0


class CitationManager:
    """
    Manages citations for medical information.
    
    Features:
    - Citation generation
    - Citation formatting
    - Citation verification
    - Source tracking
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize citation manager.
        
        Args:
            config: Assistant configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Citation configuration
        citation_config = config.get('citations', {})
        self.enabled = citation_config.get('enabled', True)
        self.format = citation_config.get('format', 'inline')
        self.include_chunk_id = citation_config.get('include_chunk_id', True)
        self.include_source = citation_config.get('include_source', True)
        self.include_section = citation_config.get('include_section', True)
        self.include_confidence = citation_config.get('include_confidence', False)
        self.verify_citations = citation_config.get('verify_citations', True)
        
        self.logger.info("CitationManager initialized")
    
    def generate_citations(
        self,
        retrieved_docs: List[Dict[str, Any]]
    ) -> List[Citation]:
        """
        Generate citations from retrieved documents.
        
        Args:
            retrieved_docs: Retrieved documents
            
        Returns:
            List of Citation objects
        """
        citations = []
        
        for i, doc in enumerate(retrieved_docs):
            metadata = doc.get('metadata', {})
            
            citation = Citation(
                chunk_id=doc.get('chunk_id', 'Unknown'),
                source=metadata.get('source', 'Unknown'),
                document_id=metadata.get('document_id', 'Unknown'),
                section=metadata.get('section', ''),
                similarity=doc.get('similarity', 0.0),
                rank=i + 1
            )
            
            citations.append(citation)
        
        return citations
    
    def format_citation(
        self,
        citation: Citation,
        index: int = None
    ) -> str:
        """
        Format a citation.
        
        Args:
            citation: Citation object
            index: Citation index (for numbered format)
            
        Returns:
            Formatted citation string
        """
        parts = []
        
        if self.format == 'inline':
            # Inline format: [Source: MedQuAD - Diabetes Info]
            if self.include_source:
                parts.append(f"Source: {citation.source}")
            
            if self.include_section and citation.section:
                parts.append(citation.section)
            
            if self.include_chunk_id:
                parts.append(f"ID: {citation.chunk_id}")
            
            return f"[{' - '.join(parts)}]"
        
        elif self.format == 'footnote':
            # Footnote format: [1]
            return f"[{index}]" if index is not None else f"[{citation.rank}]"
        
        elif self.format == 'references':
            # References format: full citation at end
            parts.append(f"{citation.rank}. ")
            parts.append(f"Source: {citation.source}")
            
            if citation.document_id:
                parts.append(f"Document ID: {citation.document_id}")
            
            if citation.section:
                parts.append(f"Section: {citation.section}")
            
            if self.include_confidence:
                parts.append(f"Relevance: {citation.similarity:.2%}")
            
            return " | ".join(parts)
        
        return f"[Source: {citation.source}]"
    
    def format_citations_section(
        self,
        citations: List[Citation]
    ) -> str:
        """
        Format citations section for response.
        
        Args:
            citations: List of citations
            
        Returns:
            Formatted citations section
        """
        if not citations or not self.enabled:
            return ""
        
        if self.format == 'references':
            lines = ["## Sources\n"]
            
            for citation in citations:
                lines.append(self.format_citation(citation))
            
            return "\n".join(lines)
        
        else:
            # For inline/footnote, sources summary
            sources = set(c.source for c in citations)
            return f"\n\n**Sources**: {', '.join(sorted(sources))}"
    
    def embed_citations(
        self,
        response: str,
        citations: List[Citation]
    ) -> str:
        """
        Embed citations into response text.
        
        Args:
            response: Response text
            citations: Available citations
            
        Returns:
            Response with embedded citations
        """
        if not self.enabled or not citations:
            return response
        
        # For now, append citations section at end
        # In production, could use NLP to embed inline at claim points
        
        citations_text = self.format_citations_section(citations)
        
        if citations_text:
            return response + "\n" + citations_text
        
        return response
    
    def verify_citation(
        self,
        claim: str,
        citation: Citation,
        document_content: str
    ) -> bool:
        """
        Verify that a citation supports a claim.
        
        Args:
            claim: Claim to verify
            citation: Citation
            document_content: Content of cited document
            
        Returns:
            True if citation appears valid
        """
        if not self.verify_citations:
            return True
        
        # Simple verification: check if key terms from claim appear in document
        claim_terms = set(
            term.lower()
            for term in re.findall(r'\b\w+\b', claim)
            if len(term) > 3  # Ignore short words
        )
        
        doc_terms = set(
            term.lower()
            for term in re.findall(r'\b\w+\b', document_content)
        )
        
        # Check overlap
        overlap = claim_terms & doc_terms
        overlap_ratio = len(overlap) / len(claim_terms) if claim_terms else 0
        
        # Consider valid if >30% of terms match
        is_valid = overlap_ratio >= 0.3
        
        if not is_valid:
            self.logger.warning(
                f"Citation verification failed: {citation.chunk_id} "
                f"(overlap: {overlap_ratio:.2%})"
            )
        
        return is_valid
    
    def get_citation_map(
        self,
        citations: List[Citation]
    ) -> Dict[str, Citation]:
        """
        Create citation lookup map.
        
        Args:
            citations: List of citations
            
        Returns:
            Dictionary mapping chunk_id to Citation
        """
        return {c.chunk_id: c for c in citations}
    
    def extract_source_list(
        self,
        citations: List[Citation]
    ) -> List[str]:
        """
        Extract unique source list.
        
        Args:
            citations: List of citations
            
        Returns:
            Sorted list of unique sources
        """
        sources = set(c.source for c in citations)
        return sorted(sources)
    
    def get_statistics(
        self,
        citations: List[Citation]
    ) -> Dict[str, Any]:
        """
        Get citation statistics.
        
        Args:
            citations: List of citations
            
        Returns:
            Statistics dictionary
        """
        if not citations:
            return {
                'total_citations': 0,
                'unique_sources': 0,
                'avg_similarity': 0.0
            }
        
        sources = set(c.source for c in citations)
        avg_similarity = sum(c.similarity for c in citations) / len(citations)
        
        return {
            'total_citations': len(citations),
            'unique_sources': len(sources),
            'sources': list(sources),
            'avg_similarity': avg_similarity,
            'min_similarity': min(c.similarity for c in citations),
            'max_similarity': max(c.similarity for c in citations)
        }
