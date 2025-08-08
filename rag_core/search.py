"""
Advanced Search Module for RAG Chatbot
Handles semantic search, filtering, and query parsing
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .vectorstore import VectorStore
from .document import DocumentProcessor
from .web_search import WebSearchEngine, WebSearchIntegration, WebSearchQuery, SearchType


class SearchOperator(Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


@dataclass
class SearchFilter:
    """Represents a search filter"""
    field: str
    operator: str  # "equals", "contains", "in", "date_range", etc.
    value: Any
    negated: bool = False


@dataclass
class SearchResult:
    """Represents a search result with metadata"""
    content: str
    filename: str
    domain: Optional[str]
    file_type: Optional[str]
    chunk_index: int
    score: float
    highlights: List[str] = None
    metadata: Dict[str, Any] = None


class AdvancedSearch:
    """Advanced search functionality with filtering and query parsing"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.vectorstore = VectorStore()
        self.logger = logging.getLogger(__name__)
        
        # Initialize web search integration
        self.web_search_engine = None
        self.web_search_integration = None
        if config and config.get("enable_web_search", True):
            try:
                self.web_search_engine = WebSearchEngine(config.get("web_search", {}))
                self.web_search_integration = WebSearchIntegration(self.web_search_engine)
                self.logger.info("Web search integration enabled")
            except Exception as e:
                self.logger.warning(f"Web search integration not available: {e}")
                self.web_search_engine = None
                self.web_search_integration = None
    
    def parse_query(self, query: str) -> Tuple[str, List[SearchFilter]]:
        """
        Parse advanced query syntax with filters
        Example: "machine learning AND domain:technology OR file_type:pdf"
        """
        filters = []
        clean_query = query
        
        # Extract filters using regex
        filter_patterns = [
            r'domain:(\w+)',
            r'file_type:(\w+)',
            r'date:(\d{4}-\d{2}-\d{2})',
            r'date_range:(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})',
            r'chunk_size:(\d+)',
            r'filename:([^\s]+)',
        ]
        
        for pattern in filter_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                if 'date_range' in pattern:
                    start_date, end_date = match.groups()
                    filters.append(SearchFilter(
                        field='date_range',
                        operator='date_range',
                        value=(start_date, end_date)
                    ))
                else:
                    field = pattern.split(':')[0].split('(')[1]
                    value = match.group(1)
                    filters.append(SearchFilter(
                        field=field,
                        operator='equals',
                        value=value
                    ))
                
                # Remove filter from query
                clean_query = clean_query.replace(match.group(0), '').strip()
        
        # Handle boolean operators
        operators = ['AND', 'OR', 'NOT']
        for op in operators:
            if op in clean_query.upper():
                # Simple boolean parsing - could be enhanced
                clean_query = clean_query.replace(op, ' ').replace(op.lower(), ' ')
        
        return clean_query.strip(), filters
    
    def search_documents(
        self, 
        query: str, 
        filters: List[SearchFilter] = None,
        limit: int = 10,
        min_score: float = 0.1
    ) -> List[SearchResult]:
        """
        Search documents with advanced filtering
        """
        try:
            # Parse query if filters not provided
            if filters is None:
                clean_query, filters = self.parse_query(query)
            else:
                clean_query = query
            
            # Get base results from vector store
            query_results = self.vectorstore.query_collection(clean_query, n_results=limit * 2)  # Get more for filtering
            
            # Check if we got results
            if not query_results or 'documents' not in query_results or not query_results['documents']:
                return [SearchResult(content='No answer found in the provided documents.', filename='', domain=None, file_type=None, chunk_index=0, score=0.0, highlights=[], metadata={})]
            
            # Extract results from ChromaDB response
            documents = query_results['documents'][0]  # First query text
            metadatas = query_results['metadatas'][0] if 'metadatas' in query_results else []
            distances = query_results['distances'][0] if 'distances' in query_results else []
            
            # Convert to SearchResult objects (ignore score)
            search_results = []
            for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                highlights = self._extract_highlights(clean_query, doc)
                search_result = SearchResult(
                    content=doc,
                    filename=metadata.get('filename', 'unknown'),
                    domain=metadata.get('domain'),
                    file_type=metadata.get('file_type'),
                    chunk_index=metadata.get('chunk_index', i),
                    score=0.0,  # Score is now always 0.0
                    highlights=highlights,
                    metadata=metadata
                )
                search_results.append(search_result)
            
            # Apply filters
            if filters:
                search_results = self._apply_filters(search_results, filters)
            
            # No score-based filtering or pre-checks
            if not search_results:
                return [SearchResult(content='No answer found in the provided documents.', filename='', domain=None, file_type=None, chunk_index=0, score=0.0, highlights=[], metadata={})]
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            return []
    
    def search_conversations(
        self, 
        query: str, 
        conversation_history: List[Dict],
        limit: int = 5
    ) -> List[Dict]:
        """
        Search within conversation history
        """
        try:
            results = []
            query_lower = query.lower()
            
            for message in conversation_history:
                content = message.get('content', '').lower()
                if query_lower in content:
                    # Calculate simple relevance score
                    score = content.count(query_lower) / len(content) if content else 0
                    
                    results.append({
                        'message_id': message.get('id'),
                        'role': message.get('role'),
                        'content': message.get('content'),
                        'timestamp': message.get('timestamp'),
                        'score': score,
                        'highlights': self._extract_highlights(query, message.get('content', ''))
                    })
            
            # Sort by score and limit
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Conversation search error: {str(e)}")
            return []
    
    def _apply_filters(self, results: List, filters: List[SearchFilter]) -> List:
        """Apply filters to search results"""
        filtered_results = []
        
        for result in results:
            metadata = getattr(result, 'metadata', {})
            include_result = True
            
            for filter_obj in filters:
                if not self._matches_filter(metadata, filter_obj):
                    include_result = False
                    break
            
            if include_result:
                filtered_results.append(result)
        
        return filtered_results
    
    def _matches_filter(self, metadata: Dict, filter_obj: SearchFilter) -> bool:
        """Check if metadata matches a filter"""
        try:
            if filter_obj.field == 'domain':
                value = metadata.get('domain', '').lower()
                filter_value = filter_obj.value.lower()
                return value == filter_value
            
            elif filter_obj.field == 'file_type':
                value = metadata.get('file_type', '').lower()
                filter_value = filter_obj.value.lower()
                return value == filter_value
            
            elif filter_obj.field == 'filename':
                value = metadata.get('filename', '').lower()
                filter_value = filter_obj.value.lower()
                return filter_value in value
            
            elif filter_obj.field == 'date_range':
                # Simple date filtering - could be enhanced
                return True  # Placeholder
            
            return True
            
        except Exception as e:
            self.logger.error(f"Filter matching error: {str(e)}")
            return True
    
    def _extract_highlights(self, query: str, content: str) -> List[str]:
        """Extract highlighted phrases from content based on query"""
        try:
            highlights = []
            query_terms = query.lower().split()
            
            # Simple highlighting - find query terms in content
            content_lower = content.lower()
            for term in query_terms:
                if len(term) > 2:  # Only highlight meaningful terms
                    start = content_lower.find(term)
                    if start != -1:
                        # Extract context around the term
                        context_start = max(0, start - 20)
                        context_end = min(len(content), start + len(term) + 20)
                        highlight = content[context_start:context_end]
                        highlights.append(highlight)
            
            return highlights[:3]  # Limit highlights
            
        except Exception as e:
            self.logger.error(f"Highlight extraction error: {str(e)}")
            return []
    
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on partial query"""
        try:
            suggestions = []
            
            # Get common domains
            domains = self.vectorstore.get_domains()
            for domain in domains:
                if domain.lower().startswith(partial_query.lower()):
                    suggestions.append(f"domain:{domain}")
            
            # Get common file types
            file_types = ['pdf', 'docx', 'txt', 'csv', 'html', 'json', 'xml', 'md']
            for file_type in file_types:
                if file_type.startswith(partial_query.lower()):
                    suggestions.append(f"file_type:{file_type}")
            
            # Add boolean operators
            if partial_query.lower().endswith(' and'):
                suggestions.append("AND")
            elif partial_query.lower().endswith(' or'):
                suggestions.append("OR")
            elif partial_query.lower().endswith(' not'):
                suggestions.append("NOT")
            
            return suggestions[:5]
            
        except Exception as e:
            self.logger.error(f"Search suggestions error: {str(e)}")
            return []
    
    def hybrid_search(self, query: str, filters: List[SearchFilter] = None, 
                     limit: int = 10, min_score: float = 0.1,
                     include_web_search: bool = True) -> Dict[str, Any]:
        """Perform hybrid search combining local and web results"""
        import time
        
        results = {
            "local_results": [],
            "web_results": [],
            "integrated_content": "",
            "search_time": 0.0,
            "total_results": 0
        }
        
        start_time = time.time()
        
        # Perform local search
        local_results = self.search_documents(query, filters, limit, min_score)
        results["local_results"] = local_results
        
        # Perform web search if enabled
        if include_web_search and self.web_search_integration:
            try:
                web_integration = self.web_search_integration.search_and_integrate(
                    query, {"local_results": local_results}
                )
                results["web_results"] = web_integration["web_search_results"]
                results["integrated_content"] = web_integration["integrated_content"]
                results["web_answer"] = web_integration["web_answer"]
                results["web_search_time"] = web_integration["search_time"]
            except Exception as e:
                self.logger.error(f"Web search failed: {e}")
                results["web_error"] = str(e)
        
        results["search_time"] = time.time() - start_time
        results["total_results"] = len(local_results) + len(results.get("web_results", []))
        
        return results
    
    def search_news(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for recent news articles"""
        if not self.web_search_integration:
            return []
        
        try:
            news_results = self.web_search_integration.search_news(query, max_results)
            return [
                {
                    "title": result.title,
                    "url": result.url,
                    "content": result.content,
                    "source": result.source,
                    "published_date": result.published_date,
                    "domain": result.domain,
                    "relevance_score": result.relevance_score
                }
                for result in news_results
            ]
        except Exception as e:
            self.logger.error(f"News search failed: {e}")
            return []
    
    def search_academic(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for academic papers and research"""
        if not self.web_search_integration:
            return []
        
        try:
            academic_results = self.web_search_integration.search_academic(query, max_results)
            return [
                {
                    "title": result.title,
                    "url": result.url,
                    "content": result.content,
                    "source": result.source,
                    "published_date": result.published_date,
                    "author": result.author,
                    "domain": result.domain,
                    "relevance_score": result.relevance_score
                }
                for result in academic_results
            ]
        except Exception as e:
            self.logger.error(f"Academic search failed: {e}")
            return []


# Global search instance
advanced_search = AdvancedSearch() 