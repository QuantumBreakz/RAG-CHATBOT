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
                if datetime.now() - entry.created_at > timedelta(seconds=entry.ttl_seconds):
                    del self.cache[key]
                    if key in self.access_counts:
                        del self.access_counts[key]
                    return None
                
                # Update access info
                entry.accessed_at = datetime.now()
                entry.access_count += 1
                self.access_counts[key] = entry.access_count
                
                # Move to end (LRU)
                self.cache.move_to_end(key)
                
                logger.info(f"Cache hit for query: {query[:50]}...")
                return entry.value
            
            return None
    
    def set(self, query: str, response: Dict[str, Any], context: str = "", 
            session_id: str = "", ttl_seconds: int = CACHE_TTL) -> bool:
        """Set cached response"""
        key = self._generate_key(query, context, session_id)
        value_size = self._calculate_size(response)
        
        with self.lock:
            # Check if we need to evict entries
            current_size = sum(entry.size_bytes for entry in self.cache.values())
            if current_size + value_size > self.max_size * 1000:  # Convert to bytes
                self._evict_entries(value_size)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=response,
                cache_type=CacheType.RESPONSE,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                access_count=1,
                size_bytes=value_size,
                ttl_seconds=ttl_seconds,
                metadata={'query': query[:100], 'context_length': len(context)}
            )
            
            self.cache[key] = entry
            self.access_counts[key] = 1
            
            logger.info(f"Cached response for query: {query[:50]}...")
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_entries = len(self.cache)
            total_size = sum(entry.size_bytes for entry in self.cache.values())
            total_accesses = sum(self.access_counts.values())
            
            if total_entries > 0:
                avg_accesses = total_accesses / total_entries
                hit_rate = sum(1 for entry in self.cache.values() if entry.access_count > 1) / total_entries
            else:
                avg_accesses = 0
                hit_rate = 0
            
            return {
                'total_entries': total_entries,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'total_accesses': total_accesses,
                'average_accesses': avg_accesses,
                'hit_rate': hit_rate,
                'strategy': self.strategy.value,
                'max_size': self.max_size
            }

class EmbeddingCache:
    """Optimized embedding cache with similarity search"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache: Dict[str, np.ndarray] = {}
        self.text_to_key: Dict[str, str] = {}
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
                logger.debug(f"Embedding cache hit for text: {text[:50]}...")
                return self.cache[key]
            return None
    
    def get_similar(self, text: str, threshold: float = 0.95) -> Optional[np.ndarray]:
        """Get similar embedding if available"""
        key = self._generate_key(text)
        
        with self.lock:
            if key in self.cache:
                return self.cache[key]
            
            # Search for similar embeddings
            for cached_text, cached_key in self.text_to_key.items():
                if cached_key in self.cache:
                    cached_embedding = self.cache[cached_key]
                    
                    # Simple text similarity check first
                    if len(text) > 10 and len(cached_text) > 10:
                        text_similarity = self._text_similarity(text, cached_text)
                        if text_similarity > threshold:
                            logger.debug(f"Found similar embedding for text: {text[:50]}...")
                            return cached_embedding
            
            return None
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using word overlap"""
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
            # Check cache size
            if len(self.cache) >= self.max_size:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                
                # Remove from text mapping
                for cached_text, cached_key in list(self.text_to_key.items()):
                    if cached_key == oldest_key:
                        del self.text_to_key[cached_text]
                        break
            
            self.cache[key] = embedding
            self.text_to_key[text] = key
            
            logger.debug(f"Cached embedding for text: {text[:50]}...")
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get embedding cache statistics"""
        with self.lock:
            total_embeddings = len(self.cache)
            total_texts = len(self.text_to_key)
            
            return {
                'total_embeddings': total_embeddings,
                'total_texts': total_texts,
                'max_size': self.max_size,
                'utilization': total_embeddings / self.max_size if self.max_size > 0 else 0
            }

class PerformanceMonitor:
    """Monitor and track performance metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            'response_times': [],
            'embedding_times': [],
            'cache_hit_rates': [],
            'memory_usage': []
        }
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def record_response_time(self, duration: float):
        """Record response time"""
        with self.lock:
            self.metrics['response_times'].append(duration)
            # Keep only last 1000 measurements
            if len(self.metrics['response_times']) > 1000:
                self.metrics['response_times'] = self.metrics['response_times'][-1000:]
    
    def record_embedding_time(self, duration: float):
        """Record embedding generation time"""
        with self.lock:
            self.metrics['embedding_times'].append(duration)
            if len(self.metrics['embedding_times']) > 1000:
                self.metrics['embedding_times'] = self.metrics['embedding_times'][-1000:]
    
    def record_cache_hit_rate(self, hit_rate: float):
        """Record cache hit rate"""
        with self.lock:
            self.metrics['cache_hit_rates'].append(hit_rate)
            if len(self.metrics['cache_hit_rates']) > 100:
                self.metrics['cache_hit_rates'] = self.metrics['cache_hit_rates'][-100:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.lock:
            stats = {}
            
            for metric_name, values in self.metrics.items():
                if values:
                    stats[f'{metric_name}_count'] = len(values)
                    stats[f'{metric_name}_avg'] = sum(values) / len(values)
                    stats[f'{metric_name}_min'] = min(values)
                    stats[f'{metric_name}_max'] = max(values)
                    if len(values) > 1:
                        stats[f'{metric_name}_std'] = np.std(values)
                    else:
                        stats[f'{metric_name}_std'] = 0
                else:
                    stats[f'{metric_name}_count'] = 0
                    stats[f'{metric_name}_avg'] = 0
                    stats[f'{metric_name}_min'] = 0
                    stats[f'{metric_name}_max'] = 0
                    stats[f'{metric_name}_std'] = 0
            
            # Uptime
            stats['uptime_seconds'] = time.time() - self.start_time
            stats['uptime_hours'] = stats['uptime_seconds'] / 3600
            
            return stats

# Global instances
response_cache = ResponseCache()
embedding_cache = EmbeddingCache()
performance_monitor = PerformanceMonitor() 