"""
Context builder for RAG pipeline.

Assembles and optimizes context from retrieved documents.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger


class ContextBuilder:
    """
    Builds optimized context from retrieved documents.
    
    Features:
    - Deduplication
    - Relevance sorting
    - Token budgeting
    - Metadata inclusion
    - Section prioritization
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize context builder.
        
        Args:
            config: Assistant configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Context configuration
        context_config = config.get('context', {})
        self.max_tokens = context_config.get('max_tokens', 4000)
        self.deduplicate = context_config.get('deduplicate', True)
        self.sort_by_relevance = context_config.get('sort_by_relevance', True)
        self.include_metadata = context_config.get('include_metadata', True)
        self.prioritize_sections = context_config.get('prioritize_sections', True)
        
        self.logger.info("ContextBuilder initialized")
    
    def build_context(
        self,
        retrieved_docs: List[Dict[str, Any]],
        query: str = ""
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Build context from retrieved documents.
        
        Args:
            retrieved_docs: List of retrieved document chunks
            query: Original query (for relevance)
            
        Returns:
            Tuple of (context_string, metadata)
        """
        if not retrieved_docs:
            self.logger.warning("No documents to build context")
            return "", {'num_docs': 0, 'total_tokens': 0}
        
        # Deduplicate if enabled
        if self.deduplicate:
            retrieved_docs = self._deduplicate_documents(retrieved_docs)
        
        # Sort by relevance if enabled
        if self.sort_by_relevance:
            retrieved_docs = self._sort_by_relevance(retrieved_docs)
        
        # Prioritize sections if enabled
        if self.prioritize_sections:
            retrieved_docs = self._prioritize_sections(retrieved_docs)
        
        # Build context string with token budget
        context_string, used_docs = self._assemble_context(retrieved_docs)
        
        # Collect metadata
        metadata = self._collect_metadata(used_docs)
        
        self.logger.info(
            f"Built context: {len(used_docs)} docs, "
            f"~{metadata['total_tokens']} tokens"
        )
        
        return context_string, metadata
    
    def _deduplicate_documents(
        self,
        docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate documents.
        
        Args:
            docs: Document list
            
        Returns:
            Deduplicated list
        """
        seen_content = set()
        seen_ids = set()
        unique_docs = []
        
        for doc in docs:
            chunk_id = doc.get('chunk_id', '')
            content = doc.get('document', '')
            
            # Check for duplicate by ID or content
            content_hash = hash(content[:200])  # Hash first 200 chars
            
            if chunk_id not in seen_ids and content_hash not in seen_content:
                unique_docs.append(doc)
                seen_ids.add(chunk_id)
                seen_content.add(content_hash)
        
        removed = len(docs) - len(unique_docs)
        if removed > 0:
            self.logger.debug(f"Removed {removed} duplicate documents")
        
        return unique_docs
    
    def _sort_by_relevance(
        self,
        docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Sort documents by relevance score.
        
        Args:
            docs: Document list
            
        Returns:
            Sorted list
        """
        # Sort by similarity score (higher is better)
        return sorted(
            docs,
            key=lambda x: x.get('similarity', 0.0),
            reverse=True
        )
    
    def _prioritize_sections(
        self,
        docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize certain document sections.
        
        Args:
            docs: Document list
            
        Returns:
            Reordered list
        """
        # Priority sections (higher priority first)
        priority_sections = [
            'summary',
            'overview',
            'definition',
            'symptoms',
            'causes',
            'treatment',
            'prevention'
        ]
        
        prioritized = []
        others = []
        
        for doc in docs:
            metadata = doc.get('metadata', {})
            section = metadata.get('section', '').lower()
            
            # Check if document is from priority section
            is_priority = any(
                priority in section
                for priority in priority_sections
            )
            
            if is_priority:
                prioritized.append(doc)
            else:
                others.append(doc)
        
        # Combine: prioritized first, then others
        return prioritized + others
    
    def _assemble_context(
        self,
        docs: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Assemble context string with token budgeting.
        
        Args:
            docs: Document list
            
        Returns:
            Tuple of (context_string, used_documents)
        """
        context_parts = []
        used_docs = []
        current_tokens = 0
        
        for i, doc in enumerate(docs):
            content = doc.get('document', '')
            metadata = doc.get('metadata', {})
            
            # Estimate tokens (rough: 1 token ≈ 4 characters)
            doc_tokens = len(content) // 4
            
            # Check token budget
            if current_tokens + doc_tokens > self.max_tokens:
                self.logger.debug(
                    f"Token budget exceeded, using {i} of {len(docs)} documents"
                )
                break
            
            # Build document section
            doc_section = self._format_document(doc, i + 1)
            
            context_parts.append(doc_section)
            used_docs.append(doc)
            current_tokens += doc_tokens
        
        context_string = "\n\n".join(context_parts)
        
        return context_string, used_docs
    
    def _format_document(
        self,
        doc: Dict[str, Any],
        index: int
    ) -> str:
        """
        Format a single document for context.
        
        Args:
            doc: Document dictionary
            index: Document index
            
        Returns:
            Formatted document string
        """
        content = doc.get('document', '')
        metadata = doc.get('metadata', {})
        
        if self.include_metadata:
            # Build metadata header
            source = metadata.get('source', 'Unknown')
            doc_id = metadata.get('document_id', 'Unknown')
            section = metadata.get('section', '')
            
            header = f"[Document {index}]"
            if source:
                header += f" Source: {source}"
            if doc_id:
                header += f" | ID: {doc_id}"
            if section:
                header += f" | Section: {section}"
            
            return f"{header}\n{content}"
        else:
            return f"[Document {index}]\n{content}"
    
    def _collect_metadata(
        self,
        docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Collect metadata from used documents.
        
        Args:
            docs: Used documents
            
        Returns:
            Metadata dictionary
        """
        sources = set()
        doc_ids = set()
        sections = defaultdict(int)
        
        total_tokens = 0
        
        for doc in docs:
            metadata = doc.get('metadata', {})
            content = doc.get('document', '')
            
            sources.add(metadata.get('source', 'Unknown'))
            doc_ids.add(metadata.get('document_id', 'Unknown'))
            
            section = metadata.get('section', 'Unknown')
            sections[section] += 1
            
            total_tokens += len(content) // 4
        
        return {
            'num_docs': len(docs),
            'sources': list(sources),
            'doc_ids': list(doc_ids),
            'sections': dict(sections),
            'total_tokens': total_tokens
        }
    
    def format_for_prompt(
        self,
        context: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Format context for prompt inclusion.
        
        Args:
            context: Context string
            metadata: Context metadata
            
        Returns:
            Formatted context
        """
        if not context:
            return "No relevant context found."
        
        header = (
            f"Retrieved {metadata['num_docs']} relevant documents "
            f"from sources: {', '.join(metadata['sources'])}\n\n"
        )
        
        return header + context
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
