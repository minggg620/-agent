"""
Zero Realm Social Agent - Challenge 4 Monitor Module
Semantic Search: Semantic similarity recall engine for information matching
"""

import asyncio
import hashlib
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, ClassVar
from dataclasses import dataclass, asdict
from enum import Enum
import re

from pydantic import BaseModel, Field
from core.config import settings
from core.logger import get_logger
from core.shared_memory import get_shared_memory

logger = get_logger(__name__)


class SimilarityMethod(Enum):
    """Methods for calculating semantic similarity."""
    COSINE_SIMILARITY = "cosine_similarity"
    JACCARD_SIMILARITY = "jaccard_similarity"
    TF_IDF = "tf_idf"
    WORD_EMBEDDING = "word_embedding"
    BERT_EMBEDDING = "bert_embedding"
    HYBRID = "hybrid"


class SearchMode(Enum):
    """Search modes for semantic search."""
    EXACT_MATCH = "exact_match"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    HYBRID_SEARCH = "hybrid_search"
    CONTEXT_AWARE = "context_aware"


class IndexStatus(Enum):
    """Index status types."""
    BUILDING = "building"
    READY = "ready"
    UPDATING = "updating"
    ERROR = "error"


@dataclass
class SemanticVector:
    """Semantic vector representation."""
    vector_id: str
    content: str
    vector: List[float]
    keywords: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    source: Optional[str]
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class SearchResult:
    """Search result with similarity score."""
    content: str
    similarity_score: float  # 0-1
    vector_id: str
    keywords: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    source: Optional[str]


@dataclass
class SearchQuery:
    """Search query with parameters."""
    query_id: str
    query_text: str
    keywords: List[str]
    similarity_threshold: float  # 0-1
    max_results: int
    search_mode: SearchMode
    similarity_method: SimilarityMethod
    context: Optional[Dict[str, Any]]
    created_at: datetime
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


class SemanticSearch(BaseModel):
    """Semantic similarity recall engine for information matching."""
    
    shared_memory: ClassVar = get_shared_memory()
    
    # Search configuration
    default_similarity_threshold: float = Field(default=0.7, description="Default similarity threshold")
    max_search_results: int = Field(default=50, description="Maximum search results")
    vector_dimension: int = Field(default=300, description="Vector dimension for embeddings")
    index_update_interval: int = Field(default=3600, description="Index update interval (seconds)")
    
    # Similarity weights
    keyword_weight: float = Field(default=0.4, description="Weight for keyword matching")
    semantic_weight: float = Field(default=0.6, description="Weight for semantic similarity")
    
    # Search state
    semantic_vectors: Dict[str, SemanticVector] = Field(default_factory=dict)
    keyword_index: Dict[str, Set[str]] = Field(default_factory=dict)  # keyword -> vector_ids
    index_status: IndexStatus = Field(default=IndexStatus.READY)
    last_index_update: datetime = Field(default_factory=datetime.now)
    
    # Performance metrics
    search_count: int = Field(default=0)
    average_search_time: float = Field(default=0.0)
    cache_hit_rate: float = Field(default=0.0)
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_index()
    
    def _initialize_index(self) -> None:
        """Initialize the semantic search index."""
        self.index_status = IndexStatus.BUILDING
        
        # Pre-process some common keywords
        common_keywords = [
            "AI", "artificial intelligence", "machine learning", "deep learning",
            "cybersecurity", "security", "privacy", "data", "information",
            "technology", "innovation", "research", "development", "analysis",
            "threat", "vulnerability", "attack", "defense", "protection",
            "policy", "regulation", "compliance", "governance", "ethics"
        ]
        
        for keyword in common_keywords:
            self.keyword_index[keyword.lower()] = set()
        
        self.index_status = IndexStatus.READY
        logger.info("Semantic search index initialized")
    
    async def add_content(self, content: str, keywords: List[str] = None,
                         metadata: Dict[str, Any] = None, source: str = None) -> str:
        """Add content to semantic search index."""
        vector_id = f"vector_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        # Extract keywords if not provided
        if keywords is None:
            keywords = await self._extract_keywords(content)
        
        # Generate semantic vector
        vector = await self._generate_semantic_vector(content)
        
        # Create semantic vector object
        semantic_vector = SemanticVector(
            vector_id=vector_id,
            content=content,
            vector=vector,
            keywords=keywords,
            metadata=metadata or {},
            timestamp=datetime.now(),
            source=source
        )
        
        # Add to index
        self.semantic_vectors[vector_id] = semantic_vector
        
        # Update keyword index
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower not in self.keyword_index:
                self.keyword_index[keyword_lower] = set()
            self.keyword_index[keyword_lower].add(vector_id)
        
        # Store in shared memory
        vector_key = f"semantic_vector:{vector_id}"
        self.shared_memory.set(vector_key, asdict(semantic_vector), tags=["semantic", "vector"])
        
        logger.debug(f"Added content to semantic index: {vector_id}")
        return vector_id
    
    async def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content."""
        # Simple keyword extraction (in real implementation, use NLP)
        words = re.findall(r'\b\w+\b', content.lower())
        
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Return top keywords by frequency
        from collections import Counter
        keyword_counts = Counter(keywords)
        return [kw for kw, count in keyword_counts.most_common(10)]
    
    async def _generate_semantic_vector(self, content: str) -> List[float]:
        """Generate semantic vector for content."""
        # Simple vector generation (in real implementation, use word embeddings or BERT)
        # For demonstration, we'll create a simple TF-IDF-like vector
        
        # Normalize content
        normalized_content = content.lower()
        words = re.findall(r'\b\w+\b', normalized_content)
        
        # Create word frequency dictionary
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Generate vector of fixed dimension
        vector = [0.0] * self.vector_dimension
        
        # Simple hash-based vector generation
        for word, freq in word_freq.items():
            # Use word hash to determine vector position
            word_hash = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
            position = word_hash % self.vector_dimension
            
            # Add frequency to vector position
            vector[position] += freq
        
        # Normalize vector
        vector_sum = sum(abs(x) for x in vector)
        if vector_sum > 0:
            vector = [x / vector_sum for x in vector]
        
        return vector
    
    async def search(self, query_text: str, keywords: List[str] = None,
                    similarity_threshold: float = None, max_results: int = None,
                    search_mode: SearchMode = SearchMode.HYBRID_SEARCH,
                    similarity_method: SimilarityMethod = SimilarityMethod.COSINE_SIMILARITY) -> List[SearchResult]:
        """Perform semantic search."""
        start_time = datetime.now()
        
        # Set defaults
        similarity_threshold = similarity_threshold or self.default_similarity_threshold
        max_results = max_results or self.max_search_results
        
        # Extract query keywords if not provided
        if keywords is None:
            keywords = await self._extract_keywords(query_text)
        
        # Generate query vector
        query_vector = await self._generate_semantic_vector(query_text)
        
        # Perform search based on mode
        if search_mode == SearchMode.EXACT_MATCH:
            results = await self._exact_match_search(query_text, keywords, max_results)
        elif search_mode == SearchMode.SEMANTIC_SIMILARITY:
            results = await self._semantic_similarity_search(query_vector, similarity_threshold, max_results, similarity_method)
        elif search_mode == SearchMode.HYBRID_SEARCH:
            results = await self._hybrid_search(query_text, keywords, query_vector, similarity_threshold, max_results, similarity_method)
        else:  # CONTEXT_AWARE
            results = await self._context_aware_search(query_text, keywords, query_vector, similarity_threshold, max_results)
        
        # Update search metrics
        search_time = (datetime.now() - start_time).total_seconds()
        self.search_count += 1
        self.average_search_time = (self.average_search_time * (self.search_count - 1) + search_time) / self.search_count
        
        logger.debug(f"Semantic search completed: {len(results)} results in {search_time:.3f}s")
        return results
    
    async def _exact_match_search(self, query_text: str, keywords: List[str], max_results: int) -> List[SearchResult]:
        """Perform exact match search."""
        results = []
        
        for vector_id, semantic_vector in self.semantic_vectors.items():
            # Check for exact text match
            if query_text.lower() in semantic_vector.content.lower():
                similarity_score = 1.0
                result = SearchResult(
                    content=semantic_vector.content,
                    similarity_score=similarity_score,
                    vector_id=vector_id,
                    keywords=semantic_vector.keywords,
                    metadata=semantic_vector.metadata,
                    timestamp=semantic_vector.timestamp,
                    source=semantic_vector.source
                )
                results.append(result)
        
        # Sort by similarity score and return top results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:max_results]
    
    async def _semantic_similarity_search(self, query_vector: List[float], similarity_threshold: float,
                                        max_results: int, similarity_method: SimilarityMethod) -> List[SearchResult]:
        """Perform semantic similarity search."""
        results = []
        
        for vector_id, semantic_vector in self.semantic_vectors.items():
            # Calculate similarity based on method
            if similarity_method == SimilarityMethod.COSINE_SIMILARITY:
                similarity_score = self._calculate_cosine_similarity(query_vector, semantic_vector.vector)
            elif similarity_method == SimilarityMethod.JACCARD_SIMILARITY:
                similarity_score = self._calculate_jaccard_similarity(query_vector, semantic_vector.vector)
            else:
                similarity_score = self._calculate_cosine_similarity(query_vector, semantic_vector.vector)
            
            # Check threshold
            if similarity_score >= similarity_threshold:
                result = SearchResult(
                    content=semantic_vector.content,
                    similarity_score=similarity_score,
                    vector_id=vector_id,
                    keywords=semantic_vector.keywords,
                    metadata=semantic_vector.metadata,
                    timestamp=semantic_vector.timestamp,
                    source=semantic_vector.source
                )
                results.append(result)
        
        # Sort by similarity score and return top results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:max_results]
    
    async def _hybrid_search(self, query_text: str, keywords: List[str], query_vector: List[float],
                          similarity_threshold: float, max_results: int,
                          similarity_method: SimilarityMethod) -> List[SearchResult]:
        """Perform hybrid search combining keyword and semantic similarity."""
        results = []
        
        for vector_id, semantic_vector in self.semantic_vectors.items():
            # Calculate keyword similarity
            keyword_score = self._calculate_keyword_similarity(keywords, semantic_vector.keywords)
            
            # Calculate semantic similarity
            if similarity_method == SimilarityMethod.COSINE_SIMILARITY:
                semantic_score = self._calculate_cosine_similarity(query_vector, semantic_vector.vector)
            else:
                semantic_score = self._calculate_cosine_similarity(query_vector, semantic_vector.vector)
            
            # Calculate combined score
            combined_score = (keyword_score * self.keyword_weight + semantic_score * self.semantic_weight)
            
            # Check threshold
            if combined_score >= similarity_threshold:
                result = SearchResult(
                    content=semantic_vector.content,
                    similarity_score=combined_score,
                    vector_id=vector_id,
                    keywords=semantic_vector.keywords,
                    metadata=semantic_vector.metadata,
                    timestamp=semantic_vector.timestamp,
                    source=semantic_vector.source
                )
                results.append(result)
        
        # Sort by similarity score and return top results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:max_results]
    
    async def _context_aware_search(self, query_text: str, keywords: List[str], query_vector: List[float],
                                 similarity_threshold: float, max_results: int) -> List[SearchResult]:
        """Perform context-aware search."""
        # For demonstration, use hybrid search with additional context considerations
        results = await self._hybrid_search(query_text, keywords, query_vector, similarity_threshold, max_results, SimilarityMethod.COSINE_SIMILARITY)
        
        # Apply context-based re-ranking
        current_time = datetime.now()
        re_ranked_results = []
        
        for result in results:
            # Time-based boost (recent content gets boost)
            time_diff = (current_time - result.timestamp).total_seconds() / 3600  # hours
            time_boost = max(0.1, 1.0 - time_diff / 168)  # Decay over 1 week
            
            # Re-rank score
            re_ranked_score = result.similarity_score * time_boost
            
            re_ranked_result = SearchResult(
                content=result.content,
                similarity_score=re_ranked_score,
                vector_id=result.vector_id,
                keywords=result.keywords,
                metadata=result.metadata,
                timestamp=result.timestamp,
                source=result.source
            )
            re_ranked_results.append(re_ranked_result)
        
        # Sort by re-ranked score
        re_ranked_results.sort(key=lambda x: x.similarity_score, reverse=True)
        return re_ranked_results[:max_results]
    
    def _calculate_cosine_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vector1) != len(vector2):
            return 0.0
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vector1, vector2))
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vector1))
        magnitude2 = math.sqrt(sum(b * b for b in vector2))
        
        # Calculate cosine similarity
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _calculate_jaccard_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate Jaccard similarity between two vectors."""
        # Convert to binary vectors (non-zero = 1)
        binary1 = set(i for i, v in enumerate(vector1) if v > 0)
        binary2 = set(i for i, v in enumerate(vector2) if v > 0)
        
        # Calculate Jaccard similarity
        intersection = len(binary1 & binary2)
        union = len(binary1 | binary2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_keyword_similarity(self, query_keywords: List[str], content_keywords: List[str]) -> float:
        """Calculate keyword similarity."""
        if not query_keywords or not content_keywords:
            return 0.0
        
        query_set = set(kw.lower() for kw in query_keywords)
        content_set = set(kw.lower() for kw in content_keywords)
        
        intersection = len(query_set & content_set)
        union = len(query_set | content_set)
        
        return intersection / union if union > 0 else 0.0
    
    async def find_similar_content(self, content: str, limit: int = 10,
                                similarity_threshold: float = 0.7) -> List[SearchResult]:
        """Find content similar to given content."""
        # Generate vector for content
        content_vector = await self._generate_semantic_vector(content)
        
        # Search for similar content
        results = await self._semantic_similarity_search(
            content_vector, similarity_threshold, limit, SimilarityMethod.COSINE_SIMILARITY
        )
        
        return results
    
    async def calculate_similarity(self, content1: str, content2: str,
                                method: SimilarityMethod = SimilarityMethod.COSINE_SIMILARITY) -> float:
        """Calculate similarity between two content pieces."""
        # Generate vectors
        vector1 = await self._generate_semantic_vector(content1)
        vector2 = await self._generate_semantic_vector(content2)
        
        # Calculate similarity based on method
        if method == SimilarityMethod.COSINE_SIMILARITY:
            return self._calculate_cosine_similarity(vector1, vector2)
        elif method == SimilarityMethod.JACCARD_SIMILARITY:
            return self._calculate_jaccard_similarity(vector1, vector2)
        else:
            return self._calculate_cosine_similarity(vector1, vector2)
    
    async def update_index(self) -> None:
        """Update the semantic search index."""
        self.index_status = IndexStatus.UPDATING
        
        try:
            # Recalculate vectors for all content
            for vector_id, semantic_vector in self.semantic_vectors.items():
                new_vector = await self._generate_semantic_vector(semantic_vector.content)
                semantic_vector.vector = new_vector
            
            # Update keyword index
            self.keyword_index.clear()
            for semantic_vector in self.semantic_vectors.values():
                for keyword in semantic_vector.keywords:
                    keyword_lower = keyword.lower()
                    if keyword_lower not in self.keyword_index:
                        self.keyword_index[keyword_lower] = set()
                    self.keyword_index[keylower].add(semantic_vector.vector_id)
            
            self.last_index_update = datetime.now()
            self.index_status = IndexStatus.READY
            
            logger.info("Semantic search index updated successfully")
            
        except Exception as e:
            self.index_status = IndexStatus.ERROR
            logger.error(f"Failed to update semantic search index: {e}")
    
    async def get_search_statistics(self) -> Dict[str, Any]:
        """Get semantic search statistics."""
        total_vectors = len(self.semantic_vectors)
        
        # Keyword distribution
        keyword_dist = {}
        for keyword, vector_ids in self.keyword_index.items():
            keyword_dist[keyword] = len(vector_ids)
        
        # Vector source distribution
        source_dist = {}
        for semantic_vector in self.semantic_vectors.values():
            source = semantic_vector.source or "unknown"
            source_dist[source] = source_dist.get(source, 0) + 1
        
        # Average vector density
        if self.semantic_vectors:
            total_non_zero = sum(
                sum(1 for v in sv.vector if v > 0) 
                for sv in self.semantic_vectors.values()
            )
            avg_density = total_non_zero / (len(self.semantic_vectors) * self.vector_dimension)
        else:
            avg_density = 0.0
        
        return {
            "total_vectors": total_vectors,
            "index_status": self.index_status.value,
            "last_index_update": self.last_index_update.isoformat(),
            "search_count": self.search_count,
            "average_search_time": self.average_search_time,
            "cache_hit_rate": self.cache_hit_rate,
            "keyword_distribution": keyword_dist,
            "source_distribution": source_dist,
            "average_vector_density": avg_density,
            "vector_dimension": self.vector_dimension
        }
    
    async def export_index(self, file_path: str) -> bool:
        """Export semantic search index to file."""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "search_statistics": await self.get_search_statistics(),
                "semantic_vectors": {
                    vector_id: asdict(sv) for vector_id, sv in self.semantic_vectors.items()
                },
                "keyword_index": {
                    keyword: list(vector_ids) for keyword, vector_ids in self.keyword_index.items()
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Semantic search index exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export semantic search index: {e}")
            return False
    
    async def cleanup_old_vectors(self, days_to_keep: int = 30) -> int:
        """Clean up old semantic vectors."""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        old_vectors = [
            vector_id for vector_id, sv in self.semantic_vectors.items()
            if sv.timestamp < cutoff_time
        ]
        
        # Remove old vectors
        for vector_id in old_vectors:
            del self.semantic_vectors[vector_id]
        
        # Update keyword index
        for keyword in self.keyword_index:
            self.keyword_index[keyword] -= set(old_vectors)
        
        logger.info(f"Cleaned up {len(old_vectors)} old semantic vectors")
        return len(old_vectors)


# Global instance
semantic_search = SemanticSearch()


def get_semantic_search() -> SemanticSearch:
    """Get the global semantic search instance."""
    return semantic_search
