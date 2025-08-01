"""
Enhanced Caching System for RAG Chatbot
Handles response caching, embedding optimization, and performance monitoring
"""

import hashlib
import json
import time
import pickle
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from rag_core.config import CACHE_TTL, logger
import numpy as np
from collections import OrderedDict
import threading
import queue

class CacheType(Enum):
    """Types of cache entries"""
    RESPONSE = "response"
    EMBEDDING = "embedding"
    QUERY = "query"
    CONTEXT = "context"
    DOCUMENT = "document"

class CacheStrategy(Enum):
    """Cache strategies"""
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    cache_type: CacheType
    created_at: datetime
    accessed_at: datetime
    access_count: int
    size_bytes: int
    ttl_seconds: int
    metadata: Dict[str, Any] = None

def get_file_hash(file_bytes: bytes) -> str:
    """Generate a hash for file content"""
    return hashlib.sha256(file_bytes).hexdigest()

def global_embeddings_exist(file_hash: str) -> bool:
    """Check if global embeddings exist for a file hash"""
    # For now, return False as we don't have a global embeddings cache implemented
    # This can be enhanced later with actual embedding storage
    return False

def load_global_embeddings(file_hash: str) -> Optional[np.ndarray]:
    """Load global embeddings for a file hash"""
    # For now, return None as we don't have a global embeddings cache implemented
    # This can be enhanced later with actual embedding storage
    return None

class ResponseCache:
    """Advanced response caching with multiple strategies"""
    
    def __init__(self, max_size: int = 1000, strategy: CacheStrategy = CacheStrategy.LRU):
        self.max_size = max_size
        self.strategy = strategy
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.access_counts: Dict[str, int] = {}
        self.lock = threading.Lock()
        
    def _generate_key(self, query: str, context: str = "", session_id: str = "") -> str:
        """Generate cache key from query and context"""
        content = f"{query}:{context}:{session_id}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of cache value"""
        try:
            return len(pickle.dumps(value))
        except:
            return 1000  # Default size
    
    def _evict_entries(self, needed_space: int):
        """Evict entries based on strategy"""
        if self.strategy == CacheStrategy.LRU:
            self._evict_lru(needed_space)
        elif self.strategy == CacheStrategy.LFU:
            self._evict_lfu(needed_space)
        elif self.strategy == CacheStrategy.FIFO:
            self._evict_fifo(needed_space)
    
    def _evict_lru(self, needed_space: int):
        """Evict least recently used entries"""
        evicted_size = 0
        keys_to_remove = []
        
        for key, entry in self.cache.items():
            if evicted_size >= needed_space:
                break
            keys_to_remove.append(key)
            evicted_size += entry.size_bytes
        
        for key in keys_to_remove:
            del self.cache[key]
            if key in self.access_counts:
                del self.access_counts[key]
    
    def _evict_lfu(self, needed_space: int):
        """Evict least frequently used entries"""
        evicted_size = 0
        keys_to_remove = []
        
        # Sort by access count
        sorted_keys = sorted(self.access_counts.items(), key=lambda x: x[1])
        
        for key, _ in sorted_keys:
            if evicted_size >= needed_space:
                break
            if key in self.cache:
                keys_to_remove.append(key)
                evicted_size += self.cache[key].size_bytes
        
        for key in keys_to_remove:
            del self.cache[key]
            if key in self.access_counts:
                del self.access_counts[key]
    
    def _evict_fifo(self, needed_space: int):
        """Evict first in, first out entries"""
        evicted_size = 0
        keys_to_remove = []
        
        for key, entry in self.cache.items():
            if evicted_size >= needed_space:
                break
            keys_to_remove.append(key)
            evicted_size += entry.size_bytes
        
        for key in keys_to_remove:
            del self.cache[key]
            if key in self.access_counts:
                del self.access_counts[key]
    
    def get(self, query: str, context: str = "", session_id: str = "") -> Optional[Dict[str, Any]]:
        """Get cached response"""
        key = self._generate_key(query, context, session_id)
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check TTL
                if time.time() - entry.created_at.timestamp() > entry.ttl_seconds:
                    del self.cache[key]
                    if key in self.access_counts:
                        del self.access_counts[key]
                    return None
                
                # Update access info
                entry.accessed_at = datetime.now()
                entry.access_count += 1
                self.access_counts[key] = entry.access_count
                
                # Move to end for LRU
                if self.strategy == CacheStrategy.LRU:
                    self.cache.move_to_end(key)
                
                return entry.value
        
        return None
    
    def set(self, query: str, response: Dict[str, Any], context: str = "", 
            session_id: str = "", ttl_seconds: int = CACHE_TTL) -> bool:
        """Set cached response"""
        key = self._generate_key(query, context, session_id)
        size = self._calculate_size(response)
        
        with self.lock:
            # Check if we need to evict entries
            if size > self.max_size:
                return False
            
            # Evict if necessary
            while len(self.cache) > 0 and size > self.max_size:
                self._evict_entries(size)
            
            entry = CacheEntry(
                key=key,
                value=response,
                cache_type=CacheType.RESPONSE,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                access_count=1,
                size_bytes=size,
                ttl_seconds=ttl_seconds
            )
            
            self.cache[key] = entry
            self.access_counts[key] = 1
            
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_size = sum(entry.size_bytes for entry in self.cache.values())
            avg_access = sum(self.access_counts.values()) / len(self.access_counts) if self.access_counts else 0
            
            return {
                "entries": len(self.cache),
                "total_size_bytes": total_size,
                "max_size": self.max_size,
                "strategy": self.strategy.value,
                "avg_access_count": avg_access,
                "oldest_entry": min(entry.created_at for entry in self.cache.values()) if self.cache else None
            }

class EmbeddingCache:
    """Cache for embeddings with similarity search"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache: Dict[str, np.ndarray] = {}
        self.texts: Dict[str, str] = {}
        self.lock = threading.Lock()
    
    def _generate_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between vectors"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def get(self, text: str) -> Optional[np.ndarray]:
        """Get cached embedding"""
        key = self._generate_key(text)
        
        with self.lock:
            if key in self.cache:
                return self.cache[key]
        
        return None
    
    def get_similar(self, text: str, threshold: float = 0.95) -> Optional[np.ndarray]:
        """Get similar embedding based on text similarity"""
        key = self._generate_key(text)
        
        with self.lock:
            if key in self.cache:
                return self.cache[key]
            
            # Check for similar texts
            for cached_text, embedding in self.cache.items():
                similarity = self._text_similarity(text, self.texts[cached_text])
                if similarity >= threshold:
                    return embedding
        
        return None
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple heuristics"""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def set(self, text: str, embedding: np.ndarray) -> bool:
        """Set cached embedding"""
        key = self._generate_key(text)
        
        with self.lock:
            if len(self.cache) >= self.max_size:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.texts[oldest_key]
            
            self.cache[key] = embedding
            self.texts[key] = text
            
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get embedding cache statistics"""
        with self.lock:
            return {
                "entries": len(self.cache),
                "max_size": self.max_size,
                "memory_usage_mb": sum(emb.nbytes for emb in self.cache.values()) / (1024 * 1024)
            }

class PerformanceMonitor:
    """Monitor performance metrics"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.embedding_times: List[float] = []
        self.cache_hit_rates: List[float] = []
        self.lock = threading.Lock()
    
    def record_response_time(self, duration: float):
        """Record response time"""
        with self.lock:
            self.response_times.append(duration)
            if len(self.response_times) > 1000:
                self.response_times.pop(0)
    
    def record_embedding_time(self, duration: float):
        """Record embedding generation time"""
        with self.lock:
            self.embedding_times.append(duration)
            if len(self.embedding_times) > 1000:
                self.embedding_times.pop(0)
    
    def record_cache_hit_rate(self, hit_rate: float):
        """Record cache hit rate"""
        with self.lock:
            self.cache_hit_rates.append(hit_rate)
            if len(self.cache_hit_rates) > 1000:
                self.cache_hit_rates.pop(0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.lock:
            return {
                "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
                "avg_embedding_time": sum(self.embedding_times) / len(self.embedding_times) if self.embedding_times else 0,
                "avg_cache_hit_rate": sum(self.cache_hit_rates) / len(self.cache_hit_rates) if self.cache_hit_rates else 0,
                "total_requests": len(self.response_times),
                "total_embeddings": len(self.embedding_times)
            }

# Global cache instances
_response_cache = ResponseCache()
_embedding_cache = EmbeddingCache()
_performance_monitor = PerformanceMonitor() 