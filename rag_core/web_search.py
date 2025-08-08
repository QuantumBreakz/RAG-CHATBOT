"""
Web Search Integration Module

This module provides web search capabilities using the Tavily API to enhance
the RAG system with real-time information access.
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import requests
from datetime import datetime, timedelta
import hashlib
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class SearchType(Enum):
    """Types of web search"""
    BASIC = "basic"
    ADVANCED = "advanced"
    NEWS = "news"
    IMAGES = "images"
    VIDEOS = "videos"
    ACADEMIC = "academic"

class ContentType(Enum):
    """Types of content that can be searched"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    NEWS = "news"
    ACADEMIC = "academic"

@dataclass
class WebSearchResult:
    """Result from a web search"""
    title: str
    url: str
    content: str
    source: str
    published_date: Optional[str] = None
    author: Optional[str] = None
    domain: Optional[str] = None
    search_type: SearchType = SearchType.BASIC
    content_type: ContentType = ContentType.TEXT
    relevance_score: float = 0.0
    freshness_score: float = 0.0
    authority_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WebSearchQuery:
    """Web search query with parameters"""
    query: str
    search_type: SearchType = SearchType.BASIC
    max_results: int = 10
    include_domains: List[str] = field(default_factory=list)
    exclude_domains: List[str] = field(default_factory=list)
    include_answer: bool = True
    include_raw_content: bool = False
    include_images: bool = False
    search_depth: str = "basic"  # "basic" or "advanced"
    language: str = "en"
    region: str = "us"
    time_period: Optional[str] = None  # "1d", "1w", "1m", "1y"
    safesearch: str = "moderate"  # "off", "moderate", "strict"

@dataclass
class WebSearchResponse:
    """Complete web search response"""
    query: WebSearchQuery
    results: List[WebSearchResult]
    answer: Optional[str] = None
    related_questions: List[str] = field(default_factory=list)
    search_time: float = 0.0
    total_results: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class WebSearchEngine:
    """Web search engine using Tavily API"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.api_key = self.config.get("tavily_api_key")
        self.base_url = "https://api.tavily.com"
        self.session = requests.Session()
        self.cache = {}
        self.cache_ttl = self.config.get("cache_ttl", 3600)  # 1 hour default
        self.logger = logging.getLogger(__name__)
        
        if not self.api_key:
            self.logger.warning("Tavily API key not found. Web search will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            self.logger.info("Web search engine initialized with Tavily API")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for web search"""
        return {
            "tavily_api_key": os.environ.get("TAVILY_API_KEY"),
            "cache_ttl": 3600,  # 1 hour
            "max_retries": 3,
            "timeout": 30,
            "rate_limit_delay": 1.0,
            "default_search_type": SearchType.BASIC,
            "default_max_results": 10,
            "content_filtering": {
                "min_relevance_score": 0.3,
                "max_age_days": 365,
                "exclude_domains": ["facebook.com", "twitter.com", "instagram.com"]
            }
        }
    
    def search(self, query: WebSearchQuery) -> WebSearchResponse:
        """Perform a web search using Tavily API"""
        if not self.enabled:
            return self._create_disabled_response(query)
        
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(query)
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if time.time() - cached_result["timestamp"] < self.cache_ttl:
                    self.logger.info("Returning cached web search result")
                    return cached_result["response"]
            
            # Prepare API request
            api_params = self._prepare_api_params(query)
            
            # Make API request
            response = self._make_api_request(api_params)
            
            # Process response
            search_response = self._process_api_response(response, query)
            search_response.search_time = time.time() - start_time
            
            # Cache the result
            self.cache[cache_key] = {
                "response": search_response,
                "timestamp": time.time()
            }
            
            return search_response
            
        except Exception as e:
            self.logger.error(f"Web search failed: {e}")
            return self._create_error_response(query, str(e))
    
    def _prepare_api_params(self, query: WebSearchQuery) -> Dict[str, Any]:
        """Prepare parameters for Tavily API request"""
        params = {
            "api_key": self.api_key,
            "query": query.query,
            "search_depth": query.search_depth,
            "include_answer": query.include_answer,
            "include_raw_content": query.include_raw_content,
            "include_images": query.include_images,
            "max_results": query.max_results,
            "language": query.language,
            "region": query.region,
            "safesearch": query.safesearch
        }
        
        # Add optional parameters
        if query.include_domains:
            params["include_domains"] = query.include_domains
        if query.exclude_domains:
            params["exclude_domains"] = query.exclude_domains
        if query.time_period:
            params["time_period"] = query.time_period
        
        return params
    
    def _make_api_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request to Tavily"""
        url = f"{self.base_url}/search"
        
        for attempt in range(self.config.get("max_retries", 3)):
            try:
                response = self.session.post(
                    url,
                    json=params,
                    timeout=self.config.get("timeout", 30)
                )
                response.raise_for_status()
                
                # Rate limiting
                if attempt < self.config.get("max_retries", 3) - 1:
                    time.sleep(self.config.get("rate_limit_delay", 1.0))
                
                return response.json()
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"API request attempt {attempt + 1} failed: {e}")
                if attempt == self.config.get("max_retries", 3) - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def _process_api_response(self, response: Dict[str, Any], query: WebSearchQuery) -> WebSearchResponse:
        """Process Tavily API response"""
        results = []
        
        # Process search results
        for result_data in response.get("results", []):
            result = self._create_search_result(result_data, query.search_type)
            if self._should_include_result(result):
                results.append(result)
        
        # Create response object
        search_response = WebSearchResponse(
            query=query,
            results=results,
            answer=response.get("answer"),
            related_questions=response.get("related_questions", []),
            total_results=len(results),
            metadata={
                "api_response": response,
                "processed_at": datetime.now().isoformat()
            }
        )
        
        return search_response
    
    def _create_search_result(self, result_data: Dict[str, Any], search_type: SearchType) -> WebSearchResult:
        """Create WebSearchResult from API response data"""
        # Extract domain from URL
        domain = None
        if result_data.get("url"):
            try:
                domain = urlparse(result_data["url"]).netloc
            except:
                pass
        
        # Determine content type
        content_type = ContentType.TEXT
        if search_type == SearchType.IMAGES:
            content_type = ContentType.IMAGE
        elif search_type == SearchType.VIDEOS:
            content_type = ContentType.VIDEO
        elif search_type == SearchType.NEWS:
            content_type = ContentType.NEWS
        elif search_type == SearchType.ACADEMIC:
            content_type = ContentType.ACADEMIC
        
        return WebSearchResult(
            title=result_data.get("title", ""),
            url=result_data.get("url", ""),
            content=result_data.get("content", ""),
            source=result_data.get("source", ""),
            published_date=result_data.get("published_date"),
            author=result_data.get("author"),
            domain=domain,
            search_type=search_type,
            content_type=content_type,
            relevance_score=result_data.get("score", 0.0),
            metadata=result_data
        )
    
    def _should_include_result(self, result: WebSearchResult) -> bool:
        """Check if result should be included based on filtering criteria"""
        config = self.config.get("content_filtering", {})
        
        # Check minimum relevance score
        min_score = config.get("min_relevance_score", 0.3)
        if result.relevance_score < min_score:
            return False
        
        # Check domain exclusions
        exclude_domains = config.get("exclude_domains", [])
        if result.domain and any(domain in result.domain for domain in exclude_domains):
            return False
        
        # Check age limit
        max_age_days = config.get("max_age_days", 365)
        if result.published_date:
            try:
                published = datetime.fromisoformat(result.published_date.replace('Z', '+00:00'))
                age_days = (datetime.now() - published).days
                if age_days > max_age_days:
                    return False
            except:
                pass  # If date parsing fails, include the result
        
        return True
    
    def _generate_cache_key(self, query: WebSearchQuery) -> str:
        """Generate cache key for query"""
        query_str = f"{query.query}_{query.search_type.value}_{query.max_results}"
        return hashlib.md5(query_str.encode()).hexdigest()
    
    def _create_disabled_response(self, query: WebSearchQuery) -> WebSearchResponse:
        """Create response when web search is disabled"""
        return WebSearchResponse(
            query=query,
            results=[],
            answer="Web search is not available. Please configure Tavily API key.",
            search_time=0.0,
            total_results=0,
            metadata={"error": "Web search disabled"}
        )
    
    def _create_error_response(self, query: WebSearchQuery, error: str) -> WebSearchResponse:
        """Create error response"""
        return WebSearchResponse(
            query=query,
            results=[],
            answer=f"Web search failed: {error}",
            search_time=0.0,
            total_results=0,
            metadata={"error": error}
        )
    
    def clear_cache(self):
        """Clear the search cache"""
        self.cache.clear()
        self.logger.info("Web search cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.cache),
            "cache_ttl": self.cache_ttl,
            "enabled": self.enabled
        }

class WebSearchIntegration:
    """Integration layer for web search with RAG system"""
    
    def __init__(self, web_search_engine: WebSearchEngine):
        self.web_search_engine = web_search_engine
        self.logger = logging.getLogger(__name__)
    
    def search_and_integrate(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search web and integrate with RAG context"""
        # Create search query
        search_query = WebSearchQuery(
            query=query,
            search_type=SearchType.BASIC,
            max_results=5,
            include_answer=True
        )
        
        # Perform web search
        search_response = self.web_search_engine.search(search_query)
        
        # Integrate with RAG context
        integrated_result = {
            "web_search_results": search_response.results,
            "web_answer": search_response.answer,
            "search_time": search_response.search_time,
            "total_web_results": search_response.total_results,
            "rag_context": context or {},
            "integrated_content": self._integrate_content(search_response, context)
        }
        
        return integrated_result
    
    def _integrate_content(self, search_response: WebSearchResponse, context: Dict[str, Any] = None) -> str:
        """Integrate web search results with RAG context"""
        content_parts = []
        
        # Add web search answer if available
        if search_response.answer:
            content_parts.append(f"Web Search Answer: {search_response.answer}")
        
        # Add top web results
        if search_response.results:
            content_parts.append("\nWeb Search Results:")
            for i, result in enumerate(search_response.results[:3], 1):
                content_parts.append(f"{i}. {result.title}")
                content_parts.append(f"   URL: {result.url}")
                content_parts.append(f"   Content: {result.content[:200]}...")
                content_parts.append("")
        
        # Add RAG context if available
        if context and context.get("local_results"):
            content_parts.append("\nLocal Knowledge Base Results:")
            for i, result in enumerate(context["local_results"][:3], 1):
                content_parts.append(f"{i}. {result.get('content', '')[:200]}...")
        
        return "\n".join(content_parts)
    
    def search_news(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        """Search for recent news articles"""
        search_query = WebSearchQuery(
            query=query,
            search_type=SearchType.NEWS,
            max_results=max_results,
            time_period="1w"  # Last week
        )
        
        response = self.web_search_engine.search(search_query)
        return response.results
    
    def search_academic(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        """Search for academic papers and research"""
        search_query = WebSearchQuery(
            query=query,
            search_type=SearchType.ACADEMIC,
            max_results=max_results
        )
        
        response = self.web_search_engine.search(search_query)
        return response.results
    
    def search_images(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        """Search for images"""
        search_query = WebSearchQuery(
            query=query,
            search_type=SearchType.IMAGES,
            max_results=max_results,
            include_images=True
        )
        
        response = self.web_search_engine.search(search_query)
        return response.results
