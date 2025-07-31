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
    
    def __init__(self):
        self.vectorstore = VectorStore()
        self.logger = logging.getLogger(__name__)
    
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
            results = self.vectorstore.search(clean_query, n_results=limit * 2)  # Get more for filtering
            
            # Apply filters
            if filters:
                results = self._apply_filters(results, filters)
            
            # Convert to SearchResult objects
            search_results = []
            for i, result in enumerate(results[:limit]):
                if hasattr(result, 'metadata'):
                    metadata = result.metadata
                else:
                    metadata = {}
                
                # Extract highlights
                highlights = self._extract_highlights(clean_query, result.page_content)
                
                search_result = SearchResult(
                    content=result.page_content,
                    filename=metadata.get('filename', 'unknown'),
                    domain=metadata.get('domain'),
                    file_type=metadata.get('file_type'),
                    chunk_index=metadata.get('chunk_index', i),
                    score=getattr(result, 'score', 0.0),
                    highlights=highlights,
                    metadata=metadata
                )
                search_results.append(search_result)
            
            # Filter by minimum score
            search_results = [r for r in search_results if r.score >= min_score]
            
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


# Global search instance
advanced_search = AdvancedSearch() 