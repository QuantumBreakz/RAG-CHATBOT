"""
Test Web Search Integration

Tests for the web search integration functionality using Tavily API.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the modules to test
from rag_core.web_search import (
    WebSearchEngine, WebSearchIntegration, WebSearchQuery, 
    WebSearchResponse, WebSearchResult, SearchType, ContentType
)
from rag_core.search import AdvancedSearch

class TestWebSearchEngine:
    """Test the WebSearchEngine class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock configuration without API key
        self.config = {
            "tavily_api_key": None,
            "cache_ttl": 3600,
            "max_retries": 3,
            "timeout": 30
        }
        self.engine = WebSearchEngine(self.config)
    
    def test_initialization_without_api_key(self):
        """Test WebSearchEngine initialization without API key"""
        assert self.engine is not None
        assert self.engine.enabled == False
        assert self.engine.api_key is None
    
    def test_initialization_with_api_key(self):
        """Test WebSearchEngine initialization with API key"""
        config = {
            "tavily_api_key": "test_api_key",
            "cache_ttl": 3600
        }
        engine = WebSearchEngine(config)
        
        assert engine.enabled == True
        assert engine.api_key == "test_api_key"
    
    def test_create_search_query(self):
        """Test WebSearchQuery creation"""
        query = WebSearchQuery(
            query="test query",
            search_type=SearchType.BASIC,
            max_results=10,
            include_answer=True
        )
        
        assert query.query == "test query"
        assert query.search_type == SearchType.BASIC
        assert query.max_results == 10
        assert query.include_answer == True
    
    def test_create_search_result(self):
        """Test WebSearchResult creation"""
        result = WebSearchResult(
            title="Test Title",
            url="https://example.com",
            content="Test content",
            source="example.com",
            search_type=SearchType.BASIC,
            content_type=ContentType.TEXT,
            relevance_score=0.8
        )
        
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.content == "Test content"
        assert result.relevance_score == 0.8
        assert result.search_type == SearchType.BASIC
        assert result.content_type == ContentType.TEXT
    
    def test_search_disabled(self):
        """Test search when engine is disabled"""
        query = WebSearchQuery(query="test query")
        response = self.engine.search(query)
        
        assert response.query == query
        assert len(response.results) == 0
        assert "not available" in response.answer
        assert response.total_results == 0
    
    @patch('requests.Session.post')
    def test_search_with_mock_api(self, mock_post):
        """Test search with mocked API response"""
        # Configure mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Test Result",
                    "url": "https://example.com",
                    "content": "Test content",
                    "source": "example.com",
                    "score": 0.8
                }
            ],
            "answer": "Test answer",
            "related_questions": ["Question 1", "Question 2"]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Create engine with API key
        config = {"tavily_api_key": "test_key"}
        engine = WebSearchEngine(config)
        
        # Perform search
        query = WebSearchQuery(query="test query")
        response = engine.search(query)
        
        # Verify response
        assert len(response.results) == 1
        assert response.results[0].title == "Test Result"
        assert response.answer == "Test answer"
        assert len(response.related_questions) == 2
    
    def test_cache_functionality(self):
        """Test cache functionality"""
        # Create engine with cache
        config = {"tavily_api_key": "test_key", "cache_ttl": 3600}
        engine = WebSearchEngine(config)
        
        # Test cache stats
        stats = engine.get_cache_stats()
        assert "cache_size" in stats
        assert "enabled" in stats
        
        # Test cache clearing
        engine.clear_cache()
        stats = engine.get_cache_stats()
        assert stats["cache_size"] == 0
    
    def test_content_filtering(self):
        """Test content filtering functionality"""
        # Create result with low relevance score
        result = WebSearchResult(
            title="Test",
            url="https://example.com",
            content="Test",
            source="example.com",
            relevance_score=0.1  # Below threshold
        )
        
        # Test filtering
        should_include = self.engine._should_include_result(result)
        assert should_include == False
        
        # Test with high relevance score
        result.relevance_score = 0.8
        should_include = self.engine._should_include_result(result)
        assert should_include == True

class TestWebSearchIntegration:
    """Test the WebSearchIntegration class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_engine = Mock(spec=WebSearchEngine)
        self.integration = WebSearchIntegration(self.mock_engine)
    
    def test_initialization(self):
        """Test WebSearchIntegration initialization"""
        assert self.integration is not None
        assert self.integration.web_search_engine == self.mock_engine
    
    def test_search_and_integrate(self):
        """Test search and integrate functionality"""
        # Mock web search response
        mock_response = Mock()
        mock_response.results = [
            WebSearchResult(
                title="Web Result",
                url="https://example.com",
                content="Web content",
                source="example.com"
            )
        ]
        mock_response.answer = "Web answer"
        mock_response.search_time = 1.0
        mock_response.total_results = 1
        
        self.mock_engine.search.return_value = mock_response
        
        # Test integration
        result = self.integration.search_and_integrate("test query")
        
        assert "web_search_results" in result
        assert "web_answer" in result
        assert "search_time" in result
        assert "integrated_content" in result
        assert len(result["web_search_results"]) == 1
    
    def test_integrate_content(self):
        """Test content integration"""
        # Create mock response
        mock_response = Mock()
        mock_response.answer = "Test answer"
        mock_response.results = [
            WebSearchResult(
                title="Result 1",
                url="https://example.com/1",
                content="Content 1",
                source="example.com"
            ),
            WebSearchResult(
                title="Result 2",
                url="https://example.com/2",
                content="Content 2",
                source="example.com"
            )
        ]
        
        # Test content integration
        integrated_content = self.integration._integrate_content(mock_response)
        
        assert "Web Search Answer: Test answer" in integrated_content
        assert "Result 1" in integrated_content
        assert "Result 2" in integrated_content
        assert "https://example.com/1" in integrated_content
    
    def test_search_news(self):
        """Test news search functionality"""
        # Mock news results
        mock_results = [
            WebSearchResult(
                title="News 1",
                url="https://news.com/1",
                content="News content 1",
                source="news.com",
                search_type=SearchType.NEWS
            )
        ]
        
        self.mock_engine.search.return_value.results = mock_results
        
        # Test news search
        results = self.integration.search_news("test news", 5)
        
        assert len(results) == 1
        assert results[0].title == "News 1"
        assert results[0].search_type == SearchType.NEWS
    
    def test_search_academic(self):
        """Test academic search functionality"""
        # Mock academic results
        mock_results = [
            WebSearchResult(
                title="Academic Paper",
                url="https://arxiv.org/paper",
                content="Academic content",
                source="arxiv.org",
                search_type=SearchType.ACADEMIC
            )
        ]
        
        self.mock_engine.search.return_value.results = mock_results
        
        # Test academic search
        results = self.integration.search_academic("test academic", 5)
        
        assert len(results) == 1
        assert results[0].title == "Academic Paper"
        assert results[0].search_type == SearchType.ACADEMIC

class TestAdvancedSearchWebIntegration:
    """Test AdvancedSearch integration with web search"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            "enable_web_search": True,
            "web_search": {
                "tavily_api_key": "test_key"
            }
        }
    
    @patch('rag_core.web_search.WebSearchEngine')
    @patch('rag_core.web_search.WebSearchIntegration')
    def test_advanced_search_with_web_integration(self, mock_integration, mock_engine):
        """Test AdvancedSearch with web integration"""
        # Mock web search components
        mock_engine_instance = Mock()
        mock_engine.return_value = mock_engine_instance
        
        mock_integration_instance = Mock()
        mock_integration.return_value = mock_integration_instance
        
        # Mock hybrid search response
        mock_integration_instance.search_and_integrate.return_value = {
            "web_search_results": [],
            "web_answer": "Test answer",
            "search_time": 1.0
        }
        
        # Initialize advanced search
        advanced_search = AdvancedSearch(self.config)
        
        # Test hybrid search
        results = advanced_search.hybrid_search("test query")
        
        assert "local_results" in results
        assert "web_results" in results
        assert "integrated_content" in results
        assert "search_time" in results
    
    def test_advanced_search_without_web_integration(self):
        """Test AdvancedSearch without web integration"""
        config = {"enable_web_search": False}
        advanced_search = AdvancedSearch(config)
        
        # Test hybrid search
        results = advanced_search.hybrid_search("test query")
        
        assert "local_results" in results
        assert "web_results" in results
        assert len(results["web_results"]) == 0  # No web results when disabled

def test_web_search_imports():
    """Test that all web search modules can be imported"""
    try:
        from rag_core.web_search import (
            WebSearchEngine, WebSearchIntegration, WebSearchQuery,
            WebSearchResponse, WebSearchResult, SearchType, ContentType
        )
        assert True  # If we get here, imports worked
    except ImportError as e:
        pytest.fail(f"Failed to import web search modules: {e}")

def test_search_type_enum():
    """Test SearchType enum values"""
    from rag_core.web_search import SearchType
    
    assert SearchType.BASIC.value == "basic"
    assert SearchType.ADVANCED.value == "advanced"
    assert SearchType.NEWS.value == "news"
    assert SearchType.IMAGES.value == "images"
    assert SearchType.VIDEOS.value == "videos"
    assert SearchType.ACADEMIC.value == "academic"

def test_content_type_enum():
    """Test ContentType enum values"""
    from rag_core.web_search import ContentType
    
    assert ContentType.TEXT.value == "text"
    assert ContentType.IMAGE.value == "image"
    assert ContentType.VIDEO.value == "video"
    assert ContentType.NEWS.value == "news"
    assert ContentType.ACADEMIC.value == "academic"

def test_web_search_configuration():
    """Test web search configuration"""
    from rag_core.web_search import WebSearchEngine
    
    # Test default configuration
    engine = WebSearchEngine()
    config = engine.config
    
    # Verify required configuration sections
    assert 'tavily_api_key' in config
    assert 'cache_ttl' in config
    assert 'max_retries' in config
    assert 'timeout' in config
    assert 'content_filtering' in config
    
    # Verify configuration values
    assert config['cache_ttl'] == 3600
    assert config['max_retries'] == 3
    assert config['timeout'] == 30

if __name__ == "__main__":
    # Run basic tests
    test_web_search_imports()
    test_search_type_enum()
    test_content_type_enum()
    test_web_search_configuration()
    print("Web search tests completed successfully!")
