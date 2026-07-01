"""
BM25 retriever for text-based search.

Implements BM25 (Best Matching 25) algorithm for ranking documents.
"""

import sys
import re
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict, Counter

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger


class BM25Retriever:
    """
    BM25 text retrieval implementation.
    
    BM25 is a probabilistic ranking function used for document retrieval.
    It ranks documents based on query term frequency and document length.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize BM25 retriever.
        
        Args:
            config: Retrieval configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # BM25 parameters
        bm25_config = config.get('bm25', {})
        self.k1 = bm25_config.get('k1', 1.5)  # Term frequency saturation
        self.b = bm25_config.get('b', 0.75)   # Length normalization
        
        # Tokenization settings
        self.lowercase = bm25_config.get('lowercase', True)
        self.remove_punctuation = bm25_config.get('remove_punctuation', True)
        
        # Index data structures
        self.documents: Dict[str, str] = {}  # chunk_id -> text
        self.doc_frequencies: Dict[str, int] = defaultdict(int)  # term -> doc count
        self.doc_lengths: Dict[str, int] = {}  # chunk_id -> length
        self.inverted_index: Dict[str, Dict[str, int]] = defaultdict(dict)  # term -> {chunk_id: frequency}
        
        # Statistics
        self.total_docs = 0
        self.avg_doc_length = 0.0
        self.indexed = False
        
        self.logger.info("BM25Retriever initialized")
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        if self.lowercase:
            text = text.lower()
        
        if self.remove_punctuation:
            text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split on whitespace
        tokens = text.split()
        
        return tokens
    
    def build_index(self, documents: List[Dict[str, Any]]) -> None:
        """
        Build BM25 index from documents.
        
        Args:
            documents: List of documents with 'chunk_id' and 'document' fields
        """
        self.logger.info(f"Building BM25 index from {len(documents)} documents...")
        
        # Reset index
        self.documents.clear()
        self.doc_frequencies.clear()
        self.doc_lengths.clear()
        self.inverted_index.clear()
        
        total_length = 0
        
        for doc in documents:
            chunk_id = doc.get('chunk_id', '')
            text = doc.get('document', '')
            
            if not chunk_id or not text:
                continue
            
            # Store document
            self.documents[chunk_id] = text
            
            # Tokenize
            tokens = self.tokenize(text)
            doc_length = len(tokens)
            
            # Store document length
            self.doc_lengths[chunk_id] = doc_length
            total_length += doc_length
            
            # Count term frequencies
            term_counts = Counter(tokens)
            
            # Update inverted index
            for term, count in term_counts.items():
                self.inverted_index[term][chunk_id] = count
            
            # Update document frequencies
            for term in term_counts.keys():
                self.doc_frequencies[term] += 1
        
        # Calculate statistics
        self.total_docs = len(self.documents)
        self.avg_doc_length = total_length / self.total_docs if self.total_docs > 0 else 0
        self.indexed = True
        
        self.logger.info(
            f"BM25 index built: {self.total_docs} docs, "
            f"{len(self.inverted_index)} terms, "
            f"avg length: {self.avg_doc_length:.1f}"
        )
    
    def _calculate_idf(self, term: str) -> float:
        """
        Calculate Inverse Document Frequency (IDF) for a term.
        
        IDF = log((N - df + 0.5) / (df + 0.5) + 1)
        where N is total documents and df is document frequency.
        
        Args:
            term: Search term
            
        Returns:
            IDF score
        """
        df = self.doc_frequencies.get(term, 0)
        
        # Avoid division by zero
        if df == 0:
            return 0.0
        
        idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1)
        
        return idf
    
    def _calculate_bm25_score(
        self,
        query_terms: List[str],
        chunk_id: str
    ) -> float:
        """
        Calculate BM25 score for a document.
        
        BM25 = Σ(IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl)))
        
        Args:
            query_terms: Query tokens
            chunk_id: Document ID
            
        Returns:
            BM25 score
        """
        score = 0.0
        doc_length = self.doc_lengths.get(chunk_id, 0)
        
        if doc_length == 0:
            return 0.0
        
        # Normalize document length
        length_norm = 1 - self.b + self.b * (doc_length / self.avg_doc_length)
        
        for term in query_terms:
            # Get term frequency in document
            tf = self.inverted_index.get(term, {}).get(chunk_id, 0)
            
            if tf == 0:
                continue
            
            # Calculate IDF
            idf = self._calculate_idf(term)
            
            # Calculate BM25 component
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * length_norm
            
            score += idf * (numerator / denominator)
        
        return score
    
    def search(
        self,
        query_text: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents using BM25.
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            filters: Metadata filters (not implemented for BM25)
            
        Returns:
            List of search results with scores
        """
        if not self.indexed:
            self.logger.warning("BM25 index not built")
            return []
        
        # Tokenize query
        query_terms = self.tokenize(query_text)
        
        if not query_terms:
            self.logger.warning("No query terms after tokenization")
            return []
        
        # Find candidate documents (documents containing at least one query term)
        candidate_docs: Set[str] = set()
        
        for term in query_terms:
            if term in self.inverted_index:
                candidate_docs.update(self.inverted_index[term].keys())
        
        if not candidate_docs:
            self.logger.info("No documents match query terms")
            return []
        
        # Score candidate documents
        scored_docs = []
        
        for chunk_id in candidate_docs:
            score = self._calculate_bm25_score(query_terms, chunk_id)
            
            if score > 0:
                scored_docs.append({
                    'chunk_id': chunk_id,
                    'document': self.documents[chunk_id],
                    'bm25_score': score,
                    'similarity': score  # For compatibility with vector retriever
                })
        
        # Sort by score
        scored_docs.sort(key=lambda x: x['bm25_score'], reverse=True)
        
        # Return top K
        results = scored_docs[:top_k]
        
        self.logger.info(
            f"BM25 search returned {len(results)} results from {len(candidate_docs)} candidates"
        )
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get BM25 index statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'total_documents': self.total_docs,
            'total_terms': len(self.inverted_index),
            'avg_doc_length': self.avg_doc_length,
            'k1': self.k1,
            'b': self.b,
            'indexed': self.indexed
        }
    
    def clear(self) -> None:
        """Clear the BM25 index."""
        self.documents.clear()
        self.doc_frequencies.clear()
        self.doc_lengths.clear()
        self.inverted_index.clear()
        self.total_docs = 0
        self.avg_doc_length = 0.0
        self.indexed = False
        
        self.logger.info("BM25 index cleared")
