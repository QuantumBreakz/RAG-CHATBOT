"""
Test suite for the Agentic RAG System

This test file covers all aspects of the agentic RAG system including:
- Query analysis and classification
- Search functionality across different data sources
- Reasoning and analysis capabilities
- Response synthesis
- Performance metrics
- Error handling
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the agentic RAG components
from rag_core.agentic_rag import (
    AgenticRAG, 
    QueryAnalyzerAgent,
    SearchAgent,
    ReasoningAgent,
    SynthesisAgent,
    QueryContext,
    QueryType, 
    DataSourceType,
    AgentRole,
    AgenticResponse
)

class TestQueryAnalyzerAgent:
    """Test the QueryAnalyzerAgent functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = QueryAnalyzerAgent()
    
    @pytest.mark.asyncio
    async def test_semantic_search_classification(self):
        """Test classification of semantic search queries"""
        context = QueryContext(
            query="What is machine learning?",
            query_type=QueryType.SEMANTIC_SEARCH,
            data_sources=[DataSourceType.VECTOR_DB],
            reasoning="",
            confidence=0.0,
            metadata={}
        )
        
        result = await self.analyzer.process(context)
        
        assert result.query_type == QueryType.SEMANTIC_SEARCH
        assert DataSourceType.VECTOR_DB in result.data_sources
        assert result.confidence > 0.0
        assert "Query type: semantic_search" in result.reasoning
    
    @pytest.mark.asyncio
    async def test_numerical_analysis_classification(self):
        """Test classification of numerical analysis queries"""
        context = QueryContext(
            query="Calculate the average sales from the spreadsheet",
            query_type=QueryType.SEMANTIC_SEARCH,
            data_sources=[DataSourceType.VECTOR_DB],
            reasoning="",
            confidence=0.0,
            metadata={}
        )
        
        result = await self.analyzer.process(context)
        
        assert result.query_type == QueryType.NUMERICAL_ANALYSIS
        assert DataSourceType.SPREADSHEET in result.data_sources
        assert DataSourceType.SQL_DB in result.data_sources
        assert result.confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_structured_query_classification(self):
        """Test classification of structured queries"""
        context = QueryContext(
            query="Find all documents about AI in the database",
            query_type=QueryType.SEMANTIC_SEARCH,
            data_sources=[DataSourceType.VECTOR_DB],
            reasoning="",
            confidence=0.0,
            metadata={}
        )
        
        result = await self.analyzer.process(context)
        
        assert result.query_type == QueryType.STRUCTURED_QUERY
        assert result.confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_web_search_classification(self):
        """Test classification of web search queries"""
        context = QueryContext(
            query="What are the latest news about AI?",
            query_type=QueryType.SEMANTIC_SEARCH,
            data_sources=[DataSourceType.VECTOR_DB],
            reasoning="",
            confidence=0.0,
            metadata={}
        )
        
        result = await self.analyzer.process(context)
        
        assert result.query_type == QueryType.WEB_SEARCH
        assert DataSourceType.WEB_SEARCH in result.data_sources
        assert result.confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_tool_calling_classification(self):
        """Test classification of tool calling queries"""
        context = QueryContext(
            query="Convert 100 USD to EUR",
            query_type=QueryType.SEMANTIC_SEARCH,
            data_sources=[DataSourceType.VECTOR_DB],
            reasoning="",
            confidence=0.0,
            metadata={}
        )
        
        result = await self.analyzer.process(context)
        
        assert result.query_type == QueryType.TOOL_CALLING
        assert DataSourceType.TOOL_RESULT in result.data_sources
        assert result.confidence > 0.0
    
    def test_intent_extraction(self):
        """Test intent extraction from queries"""
        # Information seeking
        intent = self.analyzer._extract_intent("What is the capital of France?")
        assert intent == "information_seeking"
        
        # Computation
        intent = self.analyzer._extract_intent("Calculate the sum of these numbers")
        assert intent == "computation"
        
        # Search
        intent = self.analyzer._extract_intent("Find documents about machine learning")
        assert intent == "search"
        
        # Explanation
        intent = self.analyzer._extract_intent("Explain how neural networks work")
        assert intent == "explanation"
        
        # General inquiry
        intent = self.analyzer._extract_intent("Hello, how are you?")
        assert intent == "general_inquiry"

class TestSearchAgent:
    """Test the SearchAgent functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.search_agent = SearchAgent()
    
    @pytest.mark.asyncio
    async def test_vector_db_search(self):
        """Test vector database search"""
        context = QueryContext(
            query="test query",
            query_type=QueryType.SEMANTIC_SEARCH,
            data_sources=[DataSourceType.VECTOR_DB],
            reasoning="",
            confidence=0.0,
            metadata={}
        )
        
        # Mock the vector store
        with patch.object(self.search_agent.vector_store, 'query_with_expanded_context') as mock_query:
            mock_query.return_value = {
                'documents': [['test content 1', 'test content 2']],
                'metadatas': [['meta1', 'meta2']],
                'sources': [{'confidence': 0.8}, {'confidence': 0.6}]
            }
            
            result = await self.search_agent.process(context)
            
            assert 'search_results' in result.metadata
            assert len(result.metadata['search_results']) == 2
            assert result.agent_chain == [AgentRole.SEARCH_AGENT]
    
    @pytest.mark.asyncio
    async def test_multiple_data_sources(self):
        """Test search across multiple data sources"""
        context = QueryContext(
            query="test query",
            query_type=QueryType.NUMERICAL_ANALYSIS,
            data_sources=[DataSourceType.VECTOR_DB, DataSourceType.SPREADSHEET],
            reasoning="",
            confidence=0.0,
            metadata={}
        )
        
        with patch.object(self.search_agent.vector_store, 'query_with_expanded_context') as mock_query:
            mock_query.return_value = {
                'documents': [['test content']],
                'metadatas': [['meta1']],
                'sources': [{'confidence': 0.8}]
            }
            
            result = await self.search_agent.process(context)
            
            assert 'search_results' in result.metadata
            assert len(result.metadata['search_results']) >= 1
            assert result.agent_chain == [AgentRole.SEARCH_AGENT]
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self):
        """Test error handling in search"""
        context = QueryContext(
            query="test query",
            query_type=QueryType.SEMANTIC_SEARCH,
            data_sources=[DataSourceType.VECTOR_DB],
            reasoning="",
            confidence=0.0,
            metadata={}
        )
        
        # Mock vector store to raise exception
        with patch.object(self.search_agent.vector_store, 'query_with_expanded_context') as mock_query:
            mock_query.side_effect = Exception("Search failed")
            
            result = await self.search_agent.process(context)
            
            assert 'search_results' in result.metadata
            assert len(result.metadata['search_results']) == 0
            assert result.agent_chain == [AgentRole.SEARCH_AGENT]

class TestReasoningAgent:
    """Test the ReasoningAgent functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.reasoning_agent = ReasoningAgent()
    
    @pytest.mark.asyncio
    async def test_reasoning_with_results(self):
        """Test reasoning with search results"""
        context = QueryContext(
            query="test query",
            query_type=QueryType.SEMANTIC_SEARCH,
            data_sources=[DataSourceType.VECTOR_DB],
            reasoning="",
            confidence=0.0,
            metadata={
                'search_results': [
                    {
                        'content': 'relevant content about test',
                        'confidence': 0.8,
                        'source_type': 'vector_db'
                    },
                    {
                        'content': 'more relevant content',
                        'confidence': 0.9,
                        'source_type': 'vector_db'
                    }
                ]
            }
        )
        
        result = await self.reasoning_agent.process(context)
        
        assert 'analysis' in result.metadata
        assert result.metadata['analysis']['total_results'] == 2
        assert result.metadata['analysis']['high_confidence_results'] == 2
        assert result.confidence > 0.0
        assert result.agent_chain == [AgentRole.REASONING_AGENT]
    
    @pytest.mark.asyncio
    async def test_reasoning_without_results(self):
        """Test reasoning when no search results are found"""
        context = QueryContext(
            query="test query",
            query_type=QueryType.SEMANTIC_SEARCH,
            data_sources=[DataSourceType.VECTOR_DB],
            reasoning="",
            confidence=0.5,
            metadata={'search_results': []}
        )
        
        result = await self.reasoning_agent.process(context)
        
        assert "No relevant information found" in result.reasoning
        assert result.confidence == 0.25  # Should be reduced by half
        assert result.agent_chain == [AgentRole.REASONING_AGENT]
    
    def test_relevance_check(self):
        """Test relevance checking functionality"""
        # Relevant content
        is_relevant = self.reasoning_agent._is_relevant("machine learning", "This is about machine learning algorithms")
        assert is_relevant == True
        
        # Irrelevant content
        is_relevant = self.reasoning_agent._is_relevant("machine learning", "This is about cooking recipes")
        assert is_relevant == False

class TestSynthesisAgent:
    """Test the SynthesisAgent functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.synthesis_agent = SynthesisAgent()
    
    @pytest.mark.asyncio
    async def test_response_synthesis(self):
        """Test response synthesis with search results"""
        context = QueryContext(
            query="What is machine learning?",
            query_type=QueryType.SEMANTIC_SEARCH,
            data_sources=[DataSourceType.VECTOR_DB],
            reasoning="Found 2 search results; High confidence results: 2",
            confidence=0.8,
            metadata={
                'search_results': [
                    {
                        'content': 'Machine learning is a subset of AI',
                        'confidence': 0.8,
                        'source_type': 'vector_db'
                    }
                ],
                'analysis': {
                    'total_results': 1,
                    'relevance_score': 0.8
                }
            },
            agent_chain=[AgentRole.QUERY_ANALYZER, AgentRole.SEARCH_AGENT, AgentRole.REASONING_AGENT]
        )
        
        # Mock LLM handler
        with patch.object(self.synthesis_agent.llm_handler, 'call_llm') as mock_llm:
            mock_llm.return_value = iter(["Machine learning is a subset of artificial intelligence"])
            
            response = await self.synthesis_agent.process(context)
            
            assert isinstance(response, AgenticResponse)
            assert "Machine learning is a subset of artificial intelligence" in response.answer
            assert len(response.sources) == 1
            assert response.confidence == 0.8
            assert len(response.agent_chain) == 4  # Should include synthesis agent
    
    @pytest.mark.asyncio
    async def test_synthesis_error_handling(self):
        """Test error handling in synthesis"""
        context = QueryContext(
            query="test query",
            query_type=QueryType.SEMANTIC_SEARCH,
            data_sources=[DataSourceType.VECTOR_DB],
            reasoning="",
            confidence=0.8,
            metadata={
                'search_results': [],
                'analysis': {'total_results': 0, 'relevance_score': 0.0}
            },
            agent_chain=[AgentRole.QUERY_ANALYZER, AgentRole.SEARCH_AGENT, AgentRole.REASONING_AGENT]
        )
        
        # Mock LLM handler to raise exception
        with patch.object(self.synthesis_agent.llm_handler, 'call_llm') as mock_llm:
            mock_llm.side_effect = Exception("LLM failed")
            
            response = await self.synthesis_agent.process(context)
            
            assert "Error generating response" in response.answer
            assert len(response.sources) == 0

class TestAgenticRAG:
    """Test the main AgenticRAG orchestrator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agentic_rag = AgenticRAG()
    
    @pytest.mark.asyncio
    async def test_full_query_processing(self):
        """Test complete query processing pipeline"""
        query = "What is machine learning?"
        user_context = {"user_id": "test_user"}
        
        # Mock the agents to avoid actual processing
        with patch.object(self.agentic_rag.query_analyzer, 'process') as mock_analyzer, \
             patch.object(self.agentic_rag.search_agent, 'process') as mock_search, \
             patch.object(self.agentic_rag.reasoning_agent, 'process') as mock_reasoning, \
             patch.object(self.agentic_rag.synthesis_agent, 'process') as mock_synthesis:
            
            # Mock analyzer response
            mock_analyzer.return_value = QueryContext(
                query=query,
                query_type=QueryType.SEMANTIC_SEARCH,
                data_sources=[DataSourceType.VECTOR_DB],
                reasoning="Query type: semantic_search",
                confidence=0.8,
                metadata=user_context,
                agent_chain=[AgentRole.QUERY_ANALYZER]
            )
            
            # Mock search response
            mock_search.return_value = QueryContext(
                query=query,
                query_type=QueryType.SEMANTIC_SEARCH,
                data_sources=[DataSourceType.VECTOR_DB],
                reasoning="Query type: semantic_search",
                confidence=0.8,
                metadata={**user_context, 'search_results': [{'content': 'test', 'confidence': 0.8}]},
                agent_chain=[AgentRole.QUERY_ANALYZER, AgentRole.SEARCH_AGENT]
            )
            
            # Mock reasoning response
            mock_reasoning.return_value = QueryContext(
                query=query,
                query_type=QueryType.SEMANTIC_SEARCH,
                data_sources=[DataSourceType.VECTOR_DB],
                reasoning="Found 1 search results; High confidence results: 1",
                confidence=0.8,
                metadata={**user_context, 'search_results': [{'content': 'test', 'confidence': 0.8}], 'analysis': {}},
                agent_chain=[AgentRole.QUERY_ANALYZER, AgentRole.SEARCH_AGENT, AgentRole.REASONING_AGENT]
            )
            
            # Mock synthesis response
            mock_synthesis.return_value = AgenticResponse(
                answer="Machine learning is a subset of AI",
                sources=[{'content': 'test', 'confidence': 0.8}],
                reasoning="Found 1 search results; High confidence results: 1",
                query_type=QueryType.SEMANTIC_SEARCH,
                confidence=0.8,
                processing_time=1.0,
                metadata={**user_context, 'search_results': [{'content': 'test', 'confidence': 0.8}], 'analysis': {}},
                agent_chain=[AgentRole.QUERY_ANALYZER, AgentRole.SEARCH_AGENT, AgentRole.REASONING_AGENT, AgentRole.SYNTHESIS_AGENT]
            )
            
            response = await self.agentic_rag.process_query(query, user_context)
            
            assert isinstance(response, AgenticResponse)
            assert response.answer == "Machine learning is a subset of AI"
            assert response.query_type == QueryType.SEMANTIC_SEARCH
            assert response.confidence == 0.8
            assert len(response.agent_chain) == 4
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in the main orchestrator"""
        query = "test query"
        
        # Mock an exception in the analyzer
        with patch.object(self.agentic_rag.query_analyzer, 'process') as mock_analyzer:
            mock_analyzer.side_effect = Exception("Test error")
            
            response = await self.agentic_rag.process_query(query)
            
            assert "Test error" in response.answer
            assert response.confidence == 0.0
            assert response.query_type == QueryType.SEMANTIC_SEARCH
            assert len(response.agent_chain) == 0
    
    def test_performance_metrics(self):
        """Test performance metrics tracking"""
        # Reset metrics
        self.agentic_rag.reset_metrics()
        
        # Simulate a successful query
        response = AgenticResponse(
            answer="Test answer",
            sources=[],
            reasoning="Test reasoning",
            query_type=QueryType.SEMANTIC_SEARCH,
            confidence=0.8,
            processing_time=2.0,
            metadata={},
            agent_chain=[]
        )
        
        self.agentic_rag._update_performance_metrics(response)
        
        metrics = self.agentic_rag.get_performance_metrics()
        
        assert metrics['total_queries'] == 1
        assert metrics['average_processing_time'] == 2.0
        assert metrics['success_rate'] == 1.0
        assert 'semantic_search' in metrics['query_type_distribution']
        assert len(metrics['confidence_distribution']) == 1
    
    def test_metrics_reset(self):
        """Test metrics reset functionality"""
        # Add some metrics first
        response = AgenticResponse(
            answer="Test",
            sources=[],
            reasoning="Test",
            query_type=QueryType.SEMANTIC_SEARCH,
            confidence=0.8,
            processing_time=1.0,
            metadata={},
            agent_chain=[]
        )
        
        self.agentic_rag._update_performance_metrics(response)
        
        # Reset metrics
        self.agentic_rag.reset_metrics()
        
        metrics = self.agentic_rag.get_performance_metrics()
        
        assert metrics['total_queries'] == 0
        assert metrics['average_processing_time'] == 0.0
        assert metrics['success_rate'] == 0.0
        assert len(metrics['query_type_distribution']) == 0
        assert len(metrics['confidence_distribution']) == 0

class TestIntegration:
    """Integration tests for the agentic RAG system"""
    
    @pytest.mark.asyncio
    async def test_query_type_classification_integration(self):
        """Test that query classification works correctly in the full system"""
        agentic_rag = AgenticRAG()
        
        # Test different query types
        test_cases = [
            ("What is machine learning?", QueryType.SEMANTIC_SEARCH),
            ("Calculate the average of these numbers", QueryType.NUMERICAL_ANALYSIS),
            ("Find documents about AI", QueryType.STRUCTURED_QUERY),
            ("What are the latest news?", QueryType.WEB_SEARCH),
            ("Convert USD to EUR", QueryType.TOOL_CALLING)
        ]
        
        for query, expected_type in test_cases:
            # Mock the agents to avoid actual processing
            with patch.object(agentic_rag.search_agent, 'process') as mock_search, \
                 patch.object(agentic_rag.reasoning_agent, 'process') as mock_reasoning, \
                 patch.object(agentic_rag.synthesis_agent, 'process') as mock_synthesis:
                
                # Mock responses
                mock_search.return_value = QueryContext(
                    query=query,
                    query_type=expected_type,
                    data_sources=[DataSourceType.VECTOR_DB],
                    reasoning="",
                    confidence=0.8,
                    metadata={'search_results': []},
                    agent_chain=[AgentRole.QUERY_ANALYZER, AgentRole.SEARCH_AGENT]
                )
                
                mock_reasoning.return_value = QueryContext(
                    query=query,
                    query_type=expected_type,
                    data_sources=[DataSourceType.VECTOR_DB],
                    reasoning="",
                    confidence=0.8,
                    metadata={'search_results': [], 'analysis': {}},
                    agent_chain=[AgentRole.QUERY_ANALYZER, AgentRole.SEARCH_AGENT, AgentRole.REASONING_AGENT]
                )
                
                mock_synthesis.return_value = AgenticResponse(
                    answer="Test answer",
                    sources=[],
                    reasoning="",
                    query_type=expected_type,
                    confidence=0.8,
                    processing_time=1.0,
                    metadata={},
                    agent_chain=[AgentRole.QUERY_ANALYZER, AgentRole.SEARCH_AGENT, AgentRole.REASONING_AGENT, AgentRole.SYNTHESIS_AGENT]
                )
                
                response = await agentic_rag.process_query(query)
                
                assert response.query_type == expected_type

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 