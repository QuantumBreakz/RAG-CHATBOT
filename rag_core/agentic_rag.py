"""
Modern Agentic RAG System

A sophisticated agentic AI system that addresses the core limitations of traditional RAG:
- Context Loss from Chunking
- Poor Performance with Numerical/Tabular Data  
- Inefficient Query Processing
- Limited Tool Selection and Reasoning

This implementation follows modern AI architecture patterns with clear separation of concerns,
comprehensive error handling, and extensible design.
"""

import os
import sys
import json
import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import pandas as pd
import numpy as np
from pathlib import Path
import sqlite3
import tempfile
from concurrent.futures import ThreadPoolExecutor
import hashlib
import pickle
from datetime import datetime
import uuid
from abc import ABC, abstractmethod

# Import existing RAG components
from .document import DocumentProcessor, EnhancedDocument
from .vectorstore import VectorStore
from .llm import LLMHandler
from .search import AdvancedSearch
from .multi_ocr import MultiOCREngine
from .config import logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Types of queries the agent can handle"""
    SEMANTIC_SEARCH = "semantic_search"
    NUMERICAL_ANALYSIS = "numerical_analysis"
    FULL_DOCUMENT = "full_document"
    STRUCTURED_QUERY = "structured_query"
    HYBRID = "hybrid"
    WEB_SEARCH = "web_search"
    TOOL_CALLING = "tool_calling"

class DataSourceType(Enum):
    """Types of data sources"""
    VECTOR_DB = "vector_db"
    SQL_DB = "sql_db"
    FULL_DOCUMENT = "full_document"
    SPREADSHEET = "spreadsheet"
    DATABASE = "database"
    WEB_SEARCH = "web_search"
    TOOL_RESULT = "tool_result"

class AgentRole(Enum):
    """Different agent roles in the system"""
    QUERY_ANALYZER = "query_analyzer"
    SEARCH_AGENT = "search_agent"
    REASONING_AGENT = "reasoning_agent"
    NUMERICAL_AGENT = "numerical_agent"
    TOOL_AGENT = "tool_agent"
    SYNTHESIS_AGENT = "synthesis_agent"

@dataclass
class QueryContext:
    """Context for a query including metadata and reasoning"""
    query: str
    query_type: QueryType
    data_sources: List[DataSourceType]
    reasoning: str
    confidence: float
    metadata: Dict[str, Any]
    processing_time: float = 0.0
    agent_chain: List[AgentRole] = field(default_factory=list)

@dataclass
class AgenticResponse:
    """Response from the agentic RAG system"""
    answer: str
    sources: List[Dict[str, Any]]
    reasoning: str
    query_type: QueryType
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]
    agent_chain: List[AgentRole]
    intermediate_steps: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Tool:
    """Tool definition for the agentic system"""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]
    required_permissions: List[str] = field(default_factory=list)

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, role: AgentRole, config: Dict[str, Any] = None):
        self.role = role
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{role.value}")
    
    @abstractmethod
    async def process(self, context: QueryContext, **kwargs) -> QueryContext:
        """Process the query context and return updated context"""
        pass
    
    def log_activity(self, message: str, level: str = "info"):
        """Log agent activity"""
        getattr(self.logger, level)(f"[{self.role.value}] {message}")

class QueryAnalyzerAgent(BaseAgent):
    """Agent responsible for analyzing and classifying queries"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(AgentRole.QUERY_ANALYZER, config)
        self.classification_patterns = {
            QueryType.NUMERICAL_ANALYSIS: [
                r'\b(sum|average|mean|median|max|min|count|total)\b',
                r'\b(calculate|compute|analyze|statistics)\b',
                r'\b(spreadsheet|excel|csv|table|data)\b'
            ],
            QueryType.STRUCTURED_QUERY: [
                r'\b(find|search|locate|where)\b',
                r'\b(filter|sort|group|order)\b',
                r'\b(specific|exact|precise)\b'
            ],
            QueryType.FULL_DOCUMENT: [
                r'\b(summarize|overview|entire|whole)\b',
                r'\b(document|file|complete)\b',
                r'\b(understand|comprehend|grasp)\b'
            ],
            QueryType.WEB_SEARCH: [
                r'\b(current|recent|latest|news)\b',
                r'\b(real-time|live|up-to-date)\b',
                r'\b(internet|web|online)\b'
            ],
            QueryType.TOOL_CALLING: [
                r'\b(calculate|convert|translate|generate)\b',
                r'\b(tool|function|operation)\b',
                r'\b(perform|execute|run)\b'
            ]
        }
    
    async def process(self, context: QueryContext, **kwargs) -> QueryContext:
        """Analyze query and determine type and data sources"""
        start_time = time.time()
        
        self.log_activity(f"Analyzing query: {context.query[:100]}...")
        
        # Determine query type
        query_type = self._classify_query(context.query)
        
        # Determine required data sources
        data_sources = self._determine_data_sources(context.query, query_type)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(context.query, query_type, data_sources)
        
        # Calculate confidence
        confidence = self._calculate_confidence(context.query, query_type, data_sources)
        
        processing_time = time.time() - start_time
        
        # Update context
        context.query_type = query_type
        context.data_sources = data_sources
        context.reasoning = reasoning
        context.confidence = confidence
        context.processing_time = processing_time
        context.agent_chain.append(self.role)
        
        self.log_activity(f"Query classified as {query_type.value} with confidence {confidence:.2f}")
        
        return context
    
    def _classify_query(self, query: str) -> QueryType:
        """Classify the query type based on patterns"""
        query_lower = query.lower()
        
        # Check for specific patterns
        for query_type, patterns in self.classification_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return query_type
        
        # Default to semantic search
        return QueryType.SEMANTIC_SEARCH
    
    def _determine_data_sources(self, query: str, query_type: QueryType) -> List[DataSourceType]:
        """Determine required data sources based on query type"""
        sources = [DataSourceType.VECTOR_DB]  # Always include vector DB
        
        if query_type == QueryType.NUMERICAL_ANALYSIS:
            sources.extend([DataSourceType.SPREADSHEET, DataSourceType.SQL_DB])
        elif query_type == QueryType.FULL_DOCUMENT:
            sources.append(DataSourceType.FULL_DOCUMENT)
        elif query_type == QueryType.WEB_SEARCH:
            sources.append(DataSourceType.WEB_SEARCH)
        elif query_type == QueryType.TOOL_CALLING:
            sources.append(DataSourceType.TOOL_RESULT)
        
        return sources
    
    def _generate_reasoning(self, query: str, query_type: QueryType, data_sources: List[DataSourceType]) -> str:
        """Generate reasoning for the classification"""
        reasoning_parts = [
            f"Query type: {query_type.value}",
            f"Data sources: {[ds.value for ds in data_sources]}",
            f"Query intent: {self._extract_intent(query)}"
        ]
        return "; ".join(reasoning_parts)
    
    def _extract_intent(self, query: str) -> str:
        """Extract the intent from the query"""
        # Simple intent extraction - can be enhanced with NLP
        query_lower = query.lower()
        
        # Check for explanation intent first (more specific)
        if any(word in query_lower for word in ['explain', 'describe', 'summarize']):
            return "explanation"
        elif any(word in query_lower for word in ['calculate', 'compute', 'analyze']):
            return "computation"
        elif any(word in query_lower for word in ['find', 'search', 'locate']):
            return "search"
        elif any(word in query_lower for word in ['what', 'why', 'when', 'where']):
            return "information_seeking"
        elif 'how' in query_lower:
            # More specific check for "how" - only if it's a genuine question
            if any(word in query_lower for word in ['how are', 'how is', 'how do you']):
                return "general_inquiry"
            else:
                return "information_seeking"
        else:
            return "general_inquiry"
    
    def _calculate_confidence(self, query: str, query_type: QueryType, data_sources: List[DataSourceType]) -> float:
        """Calculate confidence in the classification"""
        # Simple confidence calculation - can be enhanced with ML
        base_confidence = 0.7
        
        # Boost confidence for clear patterns
        query_lower = query.lower()
        patterns = self.classification_patterns.get(query_type, [])
        pattern_matches = sum(1 for pattern in patterns if re.search(pattern, query_lower))
        
        if pattern_matches > 0:
            base_confidence += 0.2
        
        # Boost for multiple data sources
        if len(data_sources) > 1:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)

class SearchAgent(BaseAgent):
    """Agent responsible for searching and retrieving relevant information"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(AgentRole.SEARCH_AGENT, config)
        self.vector_store = VectorStore()
        self.advanced_search = AdvancedSearch()
    
    async def process(self, context: QueryContext, **kwargs) -> QueryContext:
        """Search for relevant information based on query type"""
        start_time = time.time()
        
        self.log_activity(f"Searching for information: {context.query[:100]}...")
        
        search_results = []
        
        # Search based on data sources
        for data_source in context.data_sources:
            if data_source == DataSourceType.VECTOR_DB:
                results = await self._search_vector_db(context.query)
                search_results.extend(results)
            elif data_source == DataSourceType.FULL_DOCUMENT:
                results = await self._search_full_documents(context.query)
                search_results.extend(results)
            elif data_source == DataSourceType.SPREADSHEET:
                results = await self._search_spreadsheets(context.query)
                search_results.extend(results)
            elif data_source == DataSourceType.WEB_SEARCH:
                results = await self._search_web(context.query)
                search_results.extend(results)
        
        # Update context with search results
        context.metadata['search_results'] = search_results
        context.processing_time += time.time() - start_time
        context.agent_chain.append(self.role)
        
        self.log_activity(f"Found {len(search_results)} search results")
        
        return context
    
    async def _search_vector_db(self, query: str) -> List[Dict[str, Any]]:
        """Search vector database"""
        try:
            results = self.vector_store.query_with_expanded_context(
                query, n_results=5, expand=2
            )
            return self._format_search_results(results, "vector_db")
        except Exception as e:
            self.log_activity(f"Vector DB search error: {str(e)}", "error")
            return []
    
    async def _search_full_documents(self, query: str) -> List[Dict[str, Any]]:
        """Search full document context"""
        try:
            # This would use the document context manager
            # For now, return empty results
            return []
        except Exception as e:
            self.log_activity(f"Full document search error: {str(e)}", "error")
            return []
    
    async def _search_spreadsheets(self, query: str) -> List[Dict[str, Any]]:
        """Search spreadsheet data"""
        try:
            # This would use the numerical processor
            # For now, return empty results
            return []
        except Exception as e:
            self.log_activity(f"Spreadsheet search error: {str(e)}", "error")
            return []
    
    async def _search_web(self, query: str) -> List[Dict[str, Any]]:
        """Search web for real-time information"""
        try:
            # This would use web search integration
            # For now, return empty results
            return []
        except Exception as e:
            self.log_activity(f"Web search error: {str(e)}", "error")
            return []
    
    def _format_search_results(self, results: Dict[str, Any], source_type: str) -> List[Dict[str, Any]]:
        """Format search results consistently"""
        formatted_results = []
        
        docs = results.get('documents', [[]])[0]
        metas = results.get('metadatas', [[]])[0]
        sources = results.get('sources', [])
        
        for i in range(min(len(docs), len(metas))):
            formatted_results.append({
                'content': docs[i],
                'metadata': metas[i],
                'source': sources[i] if i < len(sources) else {},
                'source_type': source_type,
                'confidence': sources[i].get('confidence', 0.5) if i < len(sources) else 0.5
            })
        
        return formatted_results

class ReasoningAgent(BaseAgent):
    """Agent responsible for reasoning and analysis"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(AgentRole.REASONING_AGENT, config)
        self.llm_handler = LLMHandler()
    
    async def process(self, context: QueryContext, **kwargs) -> QueryContext:
        """Perform reasoning and analysis on search results"""
        start_time = time.time()
        
        self.log_activity("Performing reasoning and analysis...")
        
        search_results = context.metadata.get('search_results', [])
        
        if not search_results:
            context.reasoning += "; No relevant information found"
            context.confidence *= 0.5
            return context
        
        # Analyze search results
        analysis = await self._analyze_results(context.query, search_results)
        
        # Generate reasoning
        enhanced_reasoning = await self._generate_reasoning(context.query, search_results, analysis)
        
        # Update confidence based on analysis
        confidence_adjustment = self._calculate_confidence_adjustment(analysis)
        
        # Ensure we have a reasonable base confidence if starting from 0
        if context.confidence == 0.0:
            context.confidence = 0.5  # Start with reasonable base confidence
        
        context.confidence = min(context.confidence + confidence_adjustment, 1.0)
        
        # Update context
        context.reasoning = enhanced_reasoning
        context.metadata['analysis'] = analysis
        context.processing_time += time.time() - start_time
        context.agent_chain.append(self.role)
        
        self.log_activity(f"Reasoning completed with confidence adjustment: {confidence_adjustment:.2f}")
        
        return context
    
    async def _analyze_results(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze search results for relevance and quality"""
        analysis = {
            'total_results': len(search_results),
            'high_confidence_results': 0,
            'relevant_results': 0,
            'source_diversity': set(),
            'content_quality': 0.0,
            'relevance_score': 0.0
        }
        
        for result in search_results:
            # Count high confidence results
            if result.get('confidence', 0) > 0.7:
                analysis['high_confidence_results'] += 1
            
            # Count relevant results (simple keyword matching)
            if self._is_relevant(query, result.get('content', '')):
                analysis['relevant_results'] += 1
            
            # Track source diversity
            analysis['source_diversity'].add(result.get('source_type', 'unknown'))
            
            # Calculate content quality (simple heuristic)
            content = result.get('content', '')
            analysis['content_quality'] += len(content) / 1000  # Normalize by length
        
        # Calculate average content quality
        if analysis['total_results'] > 0:
            analysis['content_quality'] /= analysis['total_results']
        
        # Calculate relevance score
        if analysis['total_results'] > 0:
            analysis['relevance_score'] = analysis['relevant_results'] / analysis['total_results']
        
        return analysis
    
    def _is_relevant(self, query: str, content: str) -> bool:
        """Simple relevance check based on keyword overlap"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        overlap = len(query_words.intersection(content_words))
        return overlap > 0
    
    async def _generate_reasoning(self, query: str, search_results: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """Generate enhanced reasoning based on analysis"""
        reasoning_parts = [
            f"Found {analysis['total_results']} search results",
            f"High confidence results: {analysis['high_confidence_results']}",
            f"Relevant results: {analysis['relevant_results']}",
            f"Source diversity: {len(analysis['source_diversity'])} sources",
            f"Content quality: {analysis['content_quality']:.2f}",
            f"Relevance score: {analysis['relevance_score']:.2f}"
        ]
        
        return "; ".join(reasoning_parts)
    
    def _calculate_confidence_adjustment(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence adjustment based on analysis"""
        adjustment = 0.0
        
        # Boost confidence for high relevance
        if analysis['relevance_score'] > 0.7:
            adjustment += 0.1
        
        # Boost for high confidence results
        if analysis['high_confidence_results'] > 0:
            adjustment += 0.05
        
        # Boost for source diversity
        if len(analysis['source_diversity']) > 1:
            adjustment += 0.05
        
        # Penalize for low content quality (but not too harshly)
        if analysis['content_quality'] < 0.1:
            adjustment -= 0.05
        
        return adjustment

class SynthesisAgent(BaseAgent):
    """Agent responsible for synthesizing the final response"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(AgentRole.SYNTHESIS_AGENT, config)
        self.llm_handler = LLMHandler()
    
    async def process(self, context: QueryContext, **kwargs) -> AgenticResponse:
        """Synthesize the final response"""
        start_time = time.time()
        
        self.log_activity("Synthesizing final response...")
        
        search_results = context.metadata.get('search_results', [])
        analysis = context.metadata.get('analysis', {})
        
        # Prepare context for LLM
        llm_context = self._prepare_llm_context(context.query, search_results, analysis)
        
        # Generate answer
        answer = await self._generate_answer(context.query, llm_context)
        
        # Prepare sources
        sources = self._prepare_sources(search_results)
        
        # Create response
        response = AgenticResponse(
            answer=answer,
            sources=sources,
            reasoning=context.reasoning,
            query_type=context.query_type,
            confidence=context.confidence,
            processing_time=context.processing_time + (time.time() - start_time),
            metadata=context.metadata,
            agent_chain=context.agent_chain + [self.role]
        )
        
        self.log_activity("Response synthesis completed")
        
        return response
    
    def _prepare_llm_context(self, query: str, search_results: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """Prepare context for LLM"""
        context_parts = [
            f"Query: {query}",
            f"Analysis: {analysis.get('total_results', 0)} results found",
            f"Relevance score: {analysis.get('relevance_score', 0):.2f}"
        ]
        
        # Add relevant content
        relevant_content = []
        for result in search_results:
            if result.get('confidence', 0) > 0.5:  # Only include high confidence results
                content = result.get('content', '')
                if content:
                    relevant_content.append(content[:500])  # Limit content length
        
        if relevant_content:
            context_parts.append("Relevant information:")
            context_parts.extend(relevant_content)
        
        return "\n\n".join(context_parts)
    
    async def _generate_answer(self, query: str, context: str) -> str:
        """Generate answer using LLM"""
        try:
            answer = ""
            for word in self.llm_handler.call_llm(query, context):
                answer += word
            return answer
        except Exception as e:
            self.log_activity(f"LLM generation error: {str(e)}", "error")
            return f"Error generating response: {str(e)}"
    
    def _prepare_sources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare sources for response"""
        sources = []
        
        for result in search_results:
            if result.get('confidence', 0) > 0.3:  # Only include reasonable confidence sources
                sources.append({
                    'content': result.get('content', ''),
                    'metadata': result.get('metadata', {}),
                    'source': result.get('source', {}),
                    'confidence': result.get('confidence', 0.5),
                    'source_type': result.get('source_type', 'unknown')
                })
        
        return sources

class AgenticRAG:
    """Main agentic RAG system orchestrator"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize agents
        self.query_analyzer = QueryAnalyzerAgent(self.config.get('query_analyzer', {}))
        self.search_agent = SearchAgent(self.config.get('search_agent', {}))
        self.reasoning_agent = ReasoningAgent(self.config.get('reasoning_agent', {}))
        self.synthesis_agent = SynthesisAgent(self.config.get('synthesis_agent', {}))
        
        # Performance tracking
        self.performance_metrics = {
            'total_queries': 0,
            'average_processing_time': 0.0,
            'success_rate': 0.0,
            'query_type_distribution': {},
            'confidence_distribution': []
        }
    
    async def process_query(self, query: str, user_context: Dict[str, Any] = None) -> AgenticResponse:
        """Process a query through the agentic RAG system"""
        start_time = time.time()
        
        self.logger.info(f"Processing agentic query: {query[:100]}...")
        
        try:
            # Initialize query context
            context = QueryContext(
                query=query,
                query_type=QueryType.SEMANTIC_SEARCH,  # Default, will be updated by analyzer
                data_sources=[DataSourceType.VECTOR_DB],  # Default, will be updated by analyzer
                reasoning="",
                confidence=0.0,
                metadata=user_context or {}
            )
            
            # Execute agent chain
            context = await self.query_analyzer.process(context)
            context = await self.search_agent.process(context)
            context = await self.reasoning_agent.process(context)
            response = await self.synthesis_agent.process(context)
            
            # Update performance metrics
            self._update_performance_metrics(response)
            
            self.logger.info(f"Agentic query completed in {response.processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Agentic query failed: {str(e)}")
            
            # Return error response
            return AgenticResponse(
                answer=f"Sorry, I encountered an error processing your query: {str(e)}",
                sources=[],
                reasoning=f"Error occurred during processing: {str(e)}",
                query_type=QueryType.SEMANTIC_SEARCH,
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={'error': str(e)},
                agent_chain=[]
            )
    
    def _update_performance_metrics(self, response: AgenticResponse):
        """Update performance metrics"""
        self.performance_metrics['total_queries'] += 1
        
        # Update average processing time
        current_avg = self.performance_metrics['average_processing_time']
        total_queries = self.performance_metrics['total_queries']
        self.performance_metrics['average_processing_time'] = (
            (current_avg * (total_queries - 1) + response.processing_time) / total_queries
        )
        
        # Update query type distribution
        query_type = response.query_type.value
        self.performance_metrics['query_type_distribution'][query_type] = (
            self.performance_metrics['query_type_distribution'].get(query_type, 0) + 1
        )
        
        # Update confidence distribution
        self.performance_metrics['confidence_distribution'].append(response.confidence)
        
        # Update success rate
        if response.confidence > 0.5:
            self.performance_metrics['success_rate'] = (
                (self.performance_metrics['success_rate'] * (total_queries - 1) + 1) / total_queries
            )
        else:
            self.performance_metrics['success_rate'] = (
                (self.performance_metrics['success_rate'] * (total_queries - 1)) / total_queries
            )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics = {
            'total_queries': 0,
            'average_processing_time': 0.0,
            'success_rate': 0.0,
            'query_type_distribution': {},
            'confidence_distribution': []
        }

# Import re for regex patterns
import re
