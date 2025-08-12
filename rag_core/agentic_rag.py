"""
Modern Agentic RAG System

A sophisticated agentic AI system that addresses the core limitations of traditional RAG:
- Context Loss from Chunking: Uses full document context and expanded vector search
- Poor Performance with Numerical/Tabular Data: Specialized numerical analysis agents
- Inefficient Query Processing: Multi-agent pipeline with specialized roles
- Limited Tool Selection and Reasoning: Extensible tool system with reasoning agents

This implementation follows modern AI architecture patterns with clear separation of concerns,
comprehensive error handling, and extensible design.

ARCHITECTURE OVERVIEW:
1. Query Analysis: Classifies query type and determines required data sources
2. Multi-Source Retrieval: Searches vector DB, documents, spreadsheets, web, etc.
3. Reasoning & Analysis: Evaluates relevance, quality, and confidence of results
4. Synthesis: Generates final answer using LLM with curated context
5. Performance Tracking: Monitors metrics across all queries

AGENT CHAIN:
QueryAnalyzerAgent → SearchAgent → ReasoningAgent → SynthesisAgent

Each agent has a specific role and can modify the QueryContext as it flows through the system.
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
import re
from abc import ABC, abstractmethod

# Import existing RAG components
# These are the core building blocks that the agentic system orchestrates
from .document import DocumentProcessor, EnhancedDocument  # Document processing and enhancement
from .vectorstore import VectorStore  # Vector database for semantic search
from .llm import LLMHandler  # Language model interface for generation
from .search import AdvancedSearch  # Advanced search capabilities
from .multi_ocr import MultiOCREngine  # Multi-engine OCR for document processing
from .config import logger  # Centralized logging configuration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryType(Enum):
    """
    Types of queries the agent can handle.
    
    Each query type determines:
    - Which data sources to search
    - How to process and analyze results
    - What reasoning strategies to apply
    - How to synthesize the final response
    
    The QueryAnalyzerAgent uses pattern matching to classify queries into these types.
    """
    SEMANTIC_SEARCH = "semantic_search"      # General semantic similarity search in vector DB
    NUMERICAL_ANALYSIS = "numerical_analysis" # Calculations, statistics, spreadsheet operations
    FULL_DOCUMENT = "full_document"          # Complete document understanding/summarization
    STRUCTURED_QUERY = "structured_query"    # Specific, targeted searches with filters
    HYBRID = "hybrid"                        # Combination of multiple query types
    WEB_SEARCH = "web_search"                # Real-time information from the web
    TOOL_CALLING = "tool_calling"            # Execute specific tools or functions

class DataSourceType(Enum):
    """
    Types of data sources that can be searched.
    
    The SearchAgent uses these to determine which retrieval methods to employ.
    Multiple sources can be searched for a single query to provide comprehensive results.
    """
    VECTOR_DB = "vector_db"        # Semantic vector database (ChromaDB, Pinecone, etc.)
    SQL_DB = "sql_db"             # Structured SQL database for tabular data
    FULL_DOCUMENT = "full_document" # Complete document context (not chunked)
    SPREADSHEET = "spreadsheet"    # Excel, CSV, or other tabular data formats
    DATABASE = "database"          # Generic database interface
    WEB_SEARCH = "web_search"      # Real-time web search results
    TOOL_RESULT = "tool_result"    # Results from executing tools or functions

class AgentRole(Enum):
    """
    Different agent roles in the system.
    
    Each agent has a specific responsibility in the processing pipeline.
    The agent_chain in QueryContext tracks which agents have processed the query.
    """
    QUERY_ANALYZER = "query_analyzer"    # Analyzes and classifies the query
    SEARCH_AGENT = "search_agent"        # Retrieves relevant information from data sources
    REASONING_AGENT = "reasoning_agent"  # Analyzes results and adjusts confidence
    NUMERICAL_AGENT = "numerical_agent"  # Handles numerical calculations and analysis
    TOOL_AGENT = "tool_agent"            # Executes tools and functions
    SYNTHESIS_AGENT = "synthesis_agent"  # Generates the final response

@dataclass
class QueryContext:
    """
    Context for a query including metadata and reasoning.
    
    This is the central data structure that flows through the agent chain.
    Each agent can read and modify this context as needed.
    
    Attributes:
        query: The original user query string
        query_type: Classification of the query type (determined by QueryAnalyzerAgent)
        data_sources: List of data sources to search (determined by QueryAnalyzerAgent)
        reasoning: Human-readable explanation of the processing decisions
        confidence: Confidence score (0.0 to 1.0) in the current analysis
        metadata: Additional data that agents can store and access
        processing_time: Cumulative time spent processing (updated by each agent)
        agent_chain: List of agents that have processed this query (for tracking)
    """
    query: str                                    # Original user query
    query_type: QueryType                        # Classified query type
    data_sources: List[DataSourceType]           # Data sources to search
    reasoning: str                               # Explanation of processing decisions
    confidence: float                            # Confidence score (0.0 to 1.0)
    metadata: Dict[str, Any]                     # Additional data for agents
    processing_time: float = 0.0                 # Cumulative processing time
    agent_chain: List[AgentRole] = field(default_factory=list)  # Processing history

@dataclass
class AgenticResponse:
    """
    Response from the agentic RAG system.
    
    This is the final, immutable response returned to the user.
    It contains all the information needed to understand how the answer was generated.
    
    Attributes:
        answer: The final generated answer to the user's query
        sources: List of sources used to generate the answer (for citations)
        reasoning: Explanation of how the answer was derived
        query_type: The type of query that was processed
        confidence: Final confidence score in the answer quality
        processing_time: Total time spent processing the query
        metadata: Additional data about the processing
        agent_chain: Complete list of agents that processed the query
        intermediate_steps: Detailed steps taken during processing (for debugging)
    """
    answer: str                                   # Final generated answer
    sources: List[Dict[str, Any]]                # Sources used (for citations)
    reasoning: str                               # Explanation of the answer
    query_type: QueryType                        # Type of query processed
    confidence: float                            # Final confidence score
    processing_time: float                       # Total processing time
    metadata: Dict[str, Any]                     # Processing metadata
    agent_chain: List[AgentRole]                 # Complete agent processing chain
    intermediate_steps: List[Dict[str, Any]] = field(default_factory=list)  # Debug info

@dataclass
class Tool:
    """
    Tool definition for the agentic system.
    
    Tools are functions that agents can call to perform specific operations.
    This is part of the extensible architecture for adding new capabilities.
    
    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description of what the tool does
        function: The actual function to execute
        parameters: Schema defining the tool's parameters
        required_permissions: List of permissions needed to use this tool
    """
    name: str                                    # Tool identifier
    description: str                             # What the tool does
    function: Callable                           # Function to execute
    parameters: Dict[str, Any]                   # Parameter schema
    required_permissions: List[str] = field(default_factory=list)  # Required permissions

class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    
    This abstract base class defines the common interface and functionality
    that all agents must implement. It provides logging, configuration,
    and a standard processing interface.
    
    Each agent:
    1. Has a specific role in the processing pipeline
    2. Can be configured with custom parameters
    3. Must implement the process() method
    4. Has access to logging functionality
    5. Can modify the QueryContext as it flows through
    """
    
    def __init__(self, role: AgentRole, config: Dict[str, Any] = None):
        """
        Initialize the agent with its role and configuration.
        
        Args:
            role: The agent's role in the processing pipeline
            config: Optional configuration dictionary for the agent
        """
        self.role = role                                    # Agent's role (e.g., QUERY_ANALYZER)
        self.config = config or {}                         # Agent-specific configuration
        self.logger = logging.getLogger(f"{__name__}.{role.value}")  # Dedicated logger
    
    @abstractmethod
    async def process(self, context: QueryContext, **kwargs) -> QueryContext:
        """
        Process the query context and return updated context.
        
        This is the main method that each agent must implement.
        The agent reads from the context, performs its specific processing,
        and returns an updated context with new information.
        
        Args:
            context: The current query context
            **kwargs: Additional arguments specific to the agent
            
        Returns:
            Updated QueryContext with the agent's processing results
        """
        pass
    
    def log_activity(self, message: str, level: str = "info"):
        """
        Log agent activity with role prefix.
        
        Args:
            message: The message to log
            level: Logging level (info, warning, error, debug)
        """
        getattr(self.logger, level)(f"[{self.role.value}] {message}")

class QueryAnalyzerAgent(BaseAgent):
    """
    Agent responsible for analyzing and classifying queries.
    
    This is the first agent in the processing pipeline. It examines the user's query
    and determines:
    1. What type of query it is (semantic, numerical, structured, etc.)
    2. Which data sources should be searched
    3. The reasoning behind the classification
    4. A confidence score in the classification
    
    The classification uses regex patterns to identify query types, which can be
    enhanced with more sophisticated NLP techniques in the future.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the query analyzer with classification patterns.
        
        Args:
            config: Optional configuration for the analyzer
        """
        super().__init__(AgentRole.QUERY_ANALYZER, config)
        
        # Define regex patterns for each query type
        # These patterns help classify queries based on keywords and phrases
        self.classification_patterns = {
            QueryType.NUMERICAL_ANALYSIS: [
                r'\b(sum|average|mean|median|max|min|count|total)\b',  # Statistical operations
                r'\b(calculate|compute|analyze|statistics)\b',         # Computation keywords
                r'\b(spreadsheet|excel|csv|table|data)\b'             # Data source indicators
            ],
            QueryType.STRUCTURED_QUERY: [
                r'\b(find|search|locate|where)\b',                     # Search operations
                r'\b(filter|sort|group|order)\b',                      # Data manipulation
                r'\b(specific|exact|precise)\b'                        # Precision indicators
            ],
            QueryType.FULL_DOCUMENT: [
                r'\b(summarize|overview|entire|whole)\b',              # Document-level operations
                r'\b(document|file|complete)\b',                       # Document references
                r'\b(understand|comprehend|grasp)\b'                   # Understanding keywords
            ],
            QueryType.WEB_SEARCH: [
                r'\b(current|recent|latest|news)\b',                   # Time-sensitive keywords
                r'\b(real-time|live|up-to-date)\b',                    # Real-time indicators
                r'\b(internet|web|online)\b'                           # Web-specific terms
            ],
            QueryType.TOOL_CALLING: [
                r'\b(calculate|convert|translate|generate)\b',          # Tool operation keywords
                r'\b(tool|function|operation)\b',                      # Tool references
                r'\b(perform|execute|run)\b'                           # Execution keywords
            ]
        }
    
    async def process(self, context: QueryContext, **kwargs) -> QueryContext:
        """
        Analyze query and determine type and data sources.
        
        This is the main processing method for the QueryAnalyzerAgent.
        It performs the following steps:
        1. Classifies the query type using regex patterns
        2. Determines which data sources should be searched
        3. Generates reasoning for the classification
        4. Calculates confidence in the classification
        5. Updates the context with all findings
        
        Args:
            context: The query context to analyze
            **kwargs: Additional arguments (not used in this agent)
            
        Returns:
            Updated QueryContext with classification results
        """
        start_time = time.time()  # Track processing time
        
        self.log_activity(f"Analyzing query: {context.query[:100]}...")
        
        # Step 1: Determine query type using regex pattern matching
        query_type = self._classify_query(context.query)
        
        # Step 2: Determine required data sources based on query type
        data_sources = self._determine_data_sources(context.query, query_type)
        
        # Step 3: Generate human-readable reasoning for the classification
        reasoning = self._generate_reasoning(context.query, query_type, data_sources)
        
        # Step 4: Calculate confidence score in the classification
        confidence = self._calculate_confidence(context.query, query_type, data_sources)
        
        processing_time = time.time() - start_time  # Calculate total processing time
        
        # Step 5: Update the context with all analysis results
        context.query_type = query_type              # Set the classified query type
        context.data_sources = data_sources          # Set the required data sources
        context.reasoning = reasoning                # Set the reasoning explanation
        context.confidence = confidence              # Set the confidence score
        context.processing_time = processing_time    # Add this agent's processing time
        context.agent_chain.append(self.role)        # Track that this agent processed the query
        
        self.log_activity(f"Query classified as {query_type.value} with confidence {confidence:.2f}")
        
        return context
    
    def _classify_query(self, query: str) -> QueryType:
        """
        Classify the query type based on regex patterns.
        
        This method examines the query string and matches it against predefined
        regex patterns for each query type. The first matching pattern determines
        the query type. If no patterns match, it defaults to SEMANTIC_SEARCH.
        
        Args:
            query: The user's query string
            
        Returns:
            QueryType: The classified type of the query
            
        Note:
            This is a simple rule-based classification. In production, this could
            be enhanced with machine learning models for better accuracy.
        """
        query_lower = query.lower()  # Convert to lowercase for case-insensitive matching
        
        # Check for specific patterns in order of specificity
        # More specific patterns should be checked first
        for query_type, patterns in self.classification_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):  # Use regex to find pattern matches
                    return query_type  # Return the first matching query type
        
        # Default to semantic search if no specific patterns match
        # This handles general questions and conversational queries
        return QueryType.SEMANTIC_SEARCH
    
    def _determine_data_sources(self, query: str, query_type: QueryType) -> List[DataSourceType]:
        """
        Determine required data sources based on query type.
        
        This method maps query types to the appropriate data sources that should
        be searched. The vector database is always included as a fallback, and
        additional sources are added based on the query type.
        
        Args:
            query: The user's query string (used for future enhancements)
            query_type: The classified type of the query
            
        Returns:
            List[DataSourceType]: List of data sources to search
            
        Note:
            This mapping can be enhanced to be more dynamic based on the specific
            query content, available data sources, and user preferences.
        """
        sources = [DataSourceType.VECTOR_DB]  # Always include vector DB as base source
        
        # Add additional sources based on query type
        if query_type == QueryType.NUMERICAL_ANALYSIS:
            # Numerical queries need structured data sources
            sources.extend([DataSourceType.SPREADSHEET, DataSourceType.SQL_DB])
        elif query_type == QueryType.FULL_DOCUMENT:
            # Document-level queries need full document context
            sources.append(DataSourceType.FULL_DOCUMENT)
        elif query_type == QueryType.WEB_SEARCH:
            # Web queries need real-time internet access
            sources.append(DataSourceType.WEB_SEARCH)
        elif query_type == QueryType.TOOL_CALLING:
            # Tool queries need access to tool results
            sources.append(DataSourceType.TOOL_RESULT)
        
        return sources
    
    def _generate_reasoning(self, query: str, query_type: QueryType, data_sources: List[DataSourceType]) -> str:
        """
        Generate reasoning for the classification.
        
        This method creates a human-readable explanation of why the query was
        classified in a particular way and which data sources were selected.
        This reasoning is stored in the context and can be used for debugging
        or transparency purposes.
        
        Args:
            query: The user's query string
            query_type: The classified query type
            data_sources: The selected data sources
            
        Returns:
            str: Human-readable reasoning for the classification
        """
        reasoning_parts = [
            f"Query type: {query_type.value}",                    # What type of query this is
            f"Data sources: {[ds.value for ds in data_sources]}", # Which sources will be searched
            f"Query intent: {self._extract_intent(query)}"        # What the user likely wants
        ]
        return "; ".join(reasoning_parts)  # Join with semicolons for readability
    
    def _extract_intent(self, query: str) -> str:
        """
        Extract the intent from the query.
        
        This method analyzes the query to determine what the user is trying to achieve.
        It uses simple keyword matching to categorize the intent, which can be
        enhanced with more sophisticated NLP techniques in the future.
        
        Args:
            query: The user's query string
            
        Returns:
            str: The extracted intent category
            
        Note:
            This is a simplified intent extraction. In production, this could use
            intent classification models or more sophisticated NLP techniques.
        """
        # Simple intent extraction - can be enhanced with NLP
        query_lower = query.lower()  # Convert to lowercase for case-insensitive matching
        
        # Check for explanation intent first (more specific)
        if any(word in query_lower for word in ['explain', 'describe', 'summarize']):
            return "explanation"  # User wants an explanation or description
        elif any(word in query_lower for word in ['calculate', 'compute', 'analyze']):
            return "computation"  # User wants a calculation or analysis
        elif any(word in query_lower for word in ['find', 'search', 'locate']):
            return "search"  # User wants to find specific information
        elif any(word in query_lower for word in ['what', 'why', 'when', 'where']):
            return "information_seeking"  # User is asking for specific information
        elif 'how' in query_lower:
            # More specific check for "how" - only if it's a genuine question
            if any(word in query_lower for word in ['how are', 'how is', 'how do you']):
                return "general_inquiry"  # General conversational inquiry
            else:
                return "information_seeking"  # Asking how to do something
        else:
            return "general_inquiry"  # Default for other types of queries
    
    def _calculate_confidence(self, query: str, query_type: QueryType, data_sources: List[DataSourceType]) -> float:
        """
        Calculate confidence in the classification.
        
        This method computes a confidence score (0.0 to 1.0) for how certain
        the system is about the query classification. The confidence is based on:
        1. How many patterns matched the query
        2. How many data sources were selected
        3. Base confidence for the classification method
        
        Args:
            query: The user's query string
            query_type: The classified query type
            data_sources: The selected data sources
            
        Returns:
            float: Confidence score between 0.0 and 1.0
            
        Note:
            This is a simple heuristic-based confidence calculation. In production,
            this could be enhanced with machine learning models trained on
            classification accuracy.
        """
        # Simple confidence calculation - can be enhanced with ML
        base_confidence = 0.7  # Start with reasonable base confidence
        
        # Boost confidence for clear pattern matches
        query_lower = query.lower()
        patterns = self.classification_patterns.get(query_type, [])
        pattern_matches = sum(1 for pattern in patterns if re.search(pattern, query_lower))
        
        if pattern_matches > 0:
            base_confidence += 0.2  # Boost for having matching patterns
        
        # Boost for multiple data sources (indicates more complex query)
        if len(data_sources) > 1:
            base_confidence += 0.1  # Boost for multi-source queries
        
        return min(base_confidence, 1.0)  # Ensure confidence doesn't exceed 1.0

class SearchAgent(BaseAgent):
    """
    Agent responsible for searching and retrieving relevant information.
    
    This agent is the second in the processing pipeline. It takes the classified
    query and searches the appropriate data sources to find relevant information.
    The agent can search multiple sources in parallel and combines the results.
    
    Currently implemented sources:
    - Vector Database: Semantic search using embeddings
    - Full Documents: Complete document context (stubbed)
    - Spreadsheets: Tabular data analysis (stubbed)
    - Web Search: Real-time internet information (stubbed)
    
    The agent formats all results into a consistent structure for downstream processing.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the search agent with search components.
        
        Args:
            config: Optional configuration for the search agent
        """
        super().__init__(AgentRole.SEARCH_AGENT, config)
        self.vector_store = VectorStore()        # Vector database for semantic search
        self.advanced_search = AdvancedSearch()  # Advanced search capabilities
    
    async def process(self, context: QueryContext, **kwargs) -> QueryContext:
        """
        Search for relevant information based on query type.
        
        This method searches all the data sources specified in the context
        and combines the results. Each data source is searched using the
        appropriate method, and all results are formatted consistently.
        
        Args:
            context: The query context containing the query and data sources
            **kwargs: Additional arguments (not used in this agent)
            
        Returns:
            Updated QueryContext with search results
        """
        start_time = time.time()  # Track processing time
        
        self.log_activity(f"Searching for information: {context.query[:100]}...")
        
        search_results = []  # Collect results from all sources
        
        # Search each data source specified in the context
        for data_source in context.data_sources:
            if data_source == DataSourceType.VECTOR_DB:
                # Search vector database for semantic similarity
                results = await self._search_vector_db(context.query)
                search_results.extend(results)
            elif data_source == DataSourceType.FULL_DOCUMENT:
                # Search complete document context (not chunked)
                results = await self._search_full_documents(context.query)
                search_results.extend(results)
            elif data_source == DataSourceType.SPREADSHEET:
                # Search spreadsheet/tabular data
                results = await self._search_spreadsheets(context.query)
                search_results.extend(results)
            elif data_source == DataSourceType.WEB_SEARCH:
                # Search web for real-time information
                results = await self._search_web(context.query)
                search_results.extend(results)
        
        # Update context with search results and timing
        context.metadata['search_results'] = search_results  # Store results for downstream agents
        context.processing_time += time.time() - start_time   # Add this agent's processing time
        context.agent_chain.append(self.role)                # Track that this agent processed the query
        
        self.log_activity(f"Found {len(search_results)} search results")
        
        return context
    
    async def _search_vector_db(self, query: str) -> List[Dict[str, Any]]:
        """
        Search vector database for semantically similar content.
        
        This method uses the VectorStore to perform semantic search using
        embeddings. It retrieves the top results and expands the context
        around each result for better understanding.
        
        Args:
            query: The search query string
            
        Returns:
            List[Dict[str, Any]]: Formatted search results
            
        Note:
            This is the primary search method currently implemented.
            Other search methods are stubbed for future implementation.
        """
        try:
            # Use vector store with expanded context for better results
            # n_results=5: Get top 5 most similar results
            # expand=2: Expand context by 2 chunks around each result
            results = self.vector_store.query_with_expanded_context(
                query, n_results=5, expand=2
            )
            return self._format_search_results(results, "vector_db")
        except Exception as e:
            self.log_activity(f"Vector DB search error: {str(e)}", "error")
            return []  # Return empty results on error
    
    async def _search_full_documents(self, query: str) -> List[Dict[str, Any]]:
        """
        Search full document context (not chunked).
        
        This method would search complete documents rather than chunks,
        which is useful for understanding document-level context and
        generating comprehensive summaries.
        
        Args:
            query: The search query string
            
        Returns:
            List[Dict[str, Any]]: Formatted search results
            
        Note:
            This method is currently stubbed and returns empty results.
            Implementation would use the document context manager.
        """
        try:
            # TODO: Implement full document search using document context manager
            # This would search complete documents rather than chunks
            # For now, return empty results
            return []
        except Exception as e:
            self.log_activity(f"Full document search error: {str(e)}", "error")
            return []
    
    async def _search_spreadsheets(self, query: str) -> List[Dict[str, Any]]:
        """
        Search spreadsheet and tabular data.
        
        This method would search Excel files, CSV files, and other
        tabular data sources for numerical analysis and structured queries.
        
        Args:
            query: The search query string
            
        Returns:
            List[Dict[str, Any]]: Formatted search results
            
        Note:
            This method is currently stubbed and returns empty results.
            Implementation would use the numerical processor.
        """
        try:
            # TODO: Implement spreadsheet search using numerical processor
            # This would search Excel, CSV, and other tabular data
            # For now, return empty results
            return []
        except Exception as e:
            self.log_activity(f"Spreadsheet search error: {str(e)}", "error")
            return []
    
    async def _search_web(self, query: str) -> List[Dict[str, Any]]:
        """
        Search web for real-time information.
        
        This method would search the internet for current information,
        news, and real-time data that might not be in the local knowledge base.
        
        Args:
            query: The search query string
            
        Returns:
            List[Dict[str, Any]]: Formatted search results
            
        Note:
            This method is currently stubbed and returns empty results.
            Implementation would use web search integration.
        """
        try:
            # TODO: Implement web search using web search integration
            # This would search the internet for real-time information
            # For now, return empty results
            return []
        except Exception as e:
            self.log_activity(f"Web search error: {str(e)}", "error")
            return []
    
    def _format_search_results(self, results: Dict[str, Any], source_type: str) -> List[Dict[str, Any]]:
        """
        Format search results consistently across all data sources.
        
        This method takes raw search results from different sources and
        formats them into a consistent structure that downstream agents
        can process uniformly.
        
        Args:
            results: Raw search results from the data source
            source_type: Type of data source (e.g., "vector_db", "web_search")
            
        Returns:
            List[Dict[str, Any]]: Consistently formatted search results
            
        Note:
            The formatting assumes results contain 'documents', 'metadatas',
            and 'sources' keys. Different data sources may need different
            formatting logic.
        """
        formatted_results = []
        
        # Extract the actual data from the results structure
        # Handle nested structure: results['documents'][0] contains the actual docs
        docs = results.get('documents', [[]])[0]      # Document content
        metas = results.get('metadatas', [[]])[0]     # Document metadata
        sources = results.get('sources', [])          # Source information
        
        # Format each result consistently
        for i in range(min(len(docs), len(metas))):
            formatted_results.append({
                'content': docs[i],                                    # The actual content
                'metadata': metas[i],                                  # Associated metadata
                'source': sources[i] if i < len(sources) else {},      # Source information
                'source_type': source_type,                           # Type of data source
                'confidence': sources[i].get('confidence', 0.5) if i < len(sources) else 0.5  # Confidence score
            })
        
        return formatted_results

class ReasoningAgent(BaseAgent):
    """
    Agent responsible for reasoning and analysis of search results.
    
    This agent is the third in the processing pipeline. It analyzes the search
    results from the SearchAgent and performs several tasks:
    1. Evaluates the relevance and quality of search results
    2. Calculates confidence adjustments based on result analysis
    3. Generates enhanced reasoning about the results
    4. Updates the context with analysis findings
    
    The agent uses various heuristics to assess result quality and relevance,
    which helps downstream agents make better decisions about answer generation.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the reasoning agent with analysis components.
        
        Args:
            config: Optional configuration for the reasoning agent
        """
        super().__init__(AgentRole.REASONING_AGENT, config)
        self.llm_handler = LLMHandler()  # For potential LLM-based reasoning
    
    async def process(self, context: QueryContext, **kwargs) -> QueryContext:
        """
        Perform reasoning and analysis on search results.
        
        This method analyzes the search results to assess their quality,
        relevance, and usefulness for answering the query. It then adjusts
        the confidence score and generates enhanced reasoning.
        
        Args:
            context: The query context containing search results
            **kwargs: Additional arguments (not used in this agent)
            
        Returns:
            Updated QueryContext with analysis results
        """
        start_time = time.time()  # Track processing time
        
        self.log_activity("Performing reasoning and analysis...")
        
        # Get search results from the context
        search_results = context.metadata.get('search_results', [])
        
        # Handle case where no results were found
        if not search_results:
            context.reasoning += "; No relevant information found"
            context.confidence *= 0.5  # Reduce confidence when no results found
            return context
        
        # Step 1: Analyze the search results for quality and relevance
        analysis = await self._analyze_results(context.query, search_results)
        
        # Step 2: Generate enhanced reasoning based on the analysis
        enhanced_reasoning = await self._generate_reasoning(context.query, search_results, analysis)
        
        # Step 3: Calculate confidence adjustment based on analysis
        confidence_adjustment = self._calculate_confidence_adjustment(analysis)
        
        # Step 4: Update confidence score
        # Ensure we have a reasonable base confidence if starting from 0
        if context.confidence == 0.0:
            context.confidence = 0.5  # Start with reasonable base confidence
        
        # Apply confidence adjustment (ensure it doesn't exceed 1.0)
        context.confidence = min(context.confidence + confidence_adjustment, 1.0)
        
        # Step 5: Update context with analysis results
        context.reasoning = enhanced_reasoning                    # Update reasoning
        context.metadata['analysis'] = analysis                  # Store analysis results
        context.processing_time += time.time() - start_time      # Add processing time
        context.agent_chain.append(self.role)                   # Track agent processing
        
        self.log_activity(f"Reasoning completed with confidence adjustment: {confidence_adjustment:.2f}")
        
        return context
    
    async def _analyze_results(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze search results for relevance and quality.
        
        This method evaluates each search result and computes various metrics
        to assess the overall quality and relevance of the search results.
        
        Args:
            query: The original user query
            search_results: List of search results to analyze
            
        Returns:
            Dict[str, Any]: Analysis results with various quality metrics
            
        Note:
            This uses simple heuristics for analysis. In production, this could
            be enhanced with more sophisticated NLP techniques or ML models.
        """
        analysis = {
            'total_results': len(search_results),           # Total number of results
            'high_confidence_results': 0,                   # Results with confidence > 0.7
            'relevant_results': 0,                          # Results deemed relevant to query
            'source_diversity': set(),                      # Unique source types
            'content_quality': 0.0,                         # Average content quality score
            'relevance_score': 0.0                          # Overall relevance score
        }
        
        # Analyze each search result
        for result in search_results:
            # Count high confidence results (confidence > 0.7)
            if result.get('confidence', 0) > 0.7:
                analysis['high_confidence_results'] += 1
            
            # Count relevant results using simple keyword matching
            if self._is_relevant(query, result.get('content', '')):
                analysis['relevant_results'] += 1
            
            # Track source diversity (unique source types)
            analysis['source_diversity'].add(result.get('source_type', 'unknown'))
            
            # Calculate content quality using simple length heuristic
            # Longer content is assumed to be more informative
            content = result.get('content', '')
            analysis['content_quality'] += len(content) / 1000  # Normalize by length
        
        # Calculate average content quality across all results
        if analysis['total_results'] > 0:
            analysis['content_quality'] /= analysis['total_results']
        
        # Calculate overall relevance score (proportion of relevant results)
        if analysis['total_results'] > 0:
            analysis['relevance_score'] = analysis['relevant_results'] / analysis['total_results']
        
        return analysis
    
    def _is_relevant(self, query: str, content: str) -> bool:
        """
        Simple relevance check based on keyword overlap.
        
        This method determines if a piece of content is relevant to the query
        by checking for overlapping words between the query and content.
        
        Args:
            query: The user's query string
            content: The content to check for relevance
            
        Returns:
            bool: True if content is deemed relevant, False otherwise
            
        Note:
            This is a simple keyword-based relevance check. In production,
            this could be enhanced with semantic similarity, embeddings,
            or more sophisticated NLP techniques.
        """
        # Convert both query and content to lowercase and split into words
        query_words = set(query.lower().split())      # Set of query words
        content_words = set(content.lower().split())  # Set of content words
        
        # Calculate word overlap between query and content
        overlap = len(query_words.intersection(content_words))
        
        # Consider content relevant if there's any word overlap
        return overlap > 0
    
    async def _generate_reasoning(self, query: str, search_results: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """
        Generate enhanced reasoning based on analysis.
        
        This method creates a comprehensive explanation of the search results
        analysis, including statistics about result quality, relevance, and
        source diversity.
        
        Args:
            query: The original user query
            search_results: List of search results analyzed
            analysis: Analysis results from _analyze_results
            
        Returns:
            str: Enhanced reasoning explanation
        """
        reasoning_parts = [
            f"Found {analysis['total_results']} search results",                    # Total results found
            f"High confidence results: {analysis['high_confidence_results']}",      # High-quality results
            f"Relevant results: {analysis['relevant_results']}",                    # Relevant to query
            f"Source diversity: {len(analysis['source_diversity'])} sources",       # Number of source types
            f"Content quality: {analysis['content_quality']:.2f}",                  # Average content quality
            f"Relevance score: {analysis['relevance_score']:.2f}"                   # Overall relevance
        ]
        
        return "; ".join(reasoning_parts)  # Join with semicolons for readability
    
    def _calculate_confidence_adjustment(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate confidence adjustment based on analysis.
        
        This method computes how much to adjust the confidence score based
        on the quality and relevance of the search results. Positive adjustments
        boost confidence, while negative adjustments reduce it.
        
        Args:
            analysis: Analysis results from _analyze_results
            
        Returns:
            float: Confidence adjustment value (can be positive or negative)
            
        Note:
            The adjustment values are heuristic-based. In production, these
            could be learned from user feedback or optimized through A/B testing.
        """
        adjustment = 0.0  # Start with no adjustment
        
        # Boost confidence for high relevance (relevance score > 0.7)
        if analysis['relevance_score'] > 0.7:
            adjustment += 0.1  # Significant boost for high relevance
        
        # Boost for high confidence results (any results with confidence > 0.7)
        if analysis['high_confidence_results'] > 0:
            adjustment += 0.05  # Moderate boost for high-quality results
        
        # Boost for source diversity (multiple source types)
        if len(analysis['source_diversity']) > 1:
            adjustment += 0.05  # Moderate boost for diverse sources
        
        # Penalize for low content quality (but not too harshly)
        if analysis['content_quality'] < 0.1:
            adjustment -= 0.05  # Small penalty for low-quality content
        
        return adjustment

class SynthesisAgent(BaseAgent):
    """
    Agent responsible for synthesizing the final response.
    
    This agent is the final one in the processing pipeline. It takes all the
    information gathered by previous agents and generates the final answer to
    the user's query. The agent:
    1. Prepares context for the language model
    2. Generates the answer using the LLM
    3. Prepares source citations
    4. Creates the final AgenticResponse
    
    This agent transforms the processed context into a user-friendly response
    with proper citations and metadata.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the synthesis agent with LLM handler.
        
        Args:
            config: Optional configuration for the synthesis agent
        """
        super().__init__(AgentRole.SYNTHESIS_AGENT, config)
        self.llm_handler = LLMHandler()  # For generating the final answer
    
    async def process(self, context: QueryContext, **kwargs) -> AgenticResponse:
        """
        Synthesize the final response.
        
        This method takes the processed context and generates the final answer
        to the user's query. It prepares the context for the language model,
        generates the answer, and creates a complete response with sources.
        
        Args:
            context: The fully processed query context
            **kwargs: Additional arguments (not used in this agent)
            
        Returns:
            AgenticResponse: The final response with answer, sources, and metadata
        """
        start_time = time.time()  # Track processing time
        
        self.log_activity("Synthesizing final response...")
        
        # Extract search results and analysis from context
        search_results = context.metadata.get('search_results', [])
        analysis = context.metadata.get('analysis', {})
        
        # Step 1: Prepare context for the language model
        llm_context = self._prepare_llm_context(context.query, search_results, analysis)
        
        # Step 2: Generate the answer using the LLM
        answer = await self._generate_answer(context.query, llm_context)
        
        # Step 3: Prepare source citations for the response
        sources = self._prepare_sources(search_results)
        
        # Step 4: Create the final response with all metadata
        response = AgenticResponse(
            answer=answer,                                                    # The generated answer
            sources=sources,                                                  # Source citations
            reasoning=context.reasoning,                                      # Processing reasoning
            query_type=context.query_type,                                    # Type of query processed
            confidence=context.confidence,                                    # Final confidence score
            processing_time=context.processing_time + (time.time() - start_time),  # Total processing time
            metadata=context.metadata,                                        # All processing metadata
            agent_chain=context.agent_chain + [self.role]                    # Complete agent chain
        )
        
        self.log_activity("Response synthesis completed")
        
        return response
    
    def _prepare_llm_context(self, query: str, search_results: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """
        Prepare context for the language model.
        
        This method creates a structured context that the LLM can use to
        generate an accurate and relevant answer. It includes the query,
        analysis summary, and the most relevant content from search results.
        
        Args:
            query: The user's original query
            search_results: List of search results to include in context
            analysis: Analysis results from the reasoning agent
            
        Returns:
            str: Formatted context for the LLM
            
        Note:
            The context is structured to provide the LLM with all necessary
            information while keeping it concise and focused.
        """
        context_parts = [
            f"Query: {query}",                                                    # The original query
            f"Analysis: {analysis.get('total_results', 0)} results found",        # Number of results
            f"Relevance score: {analysis.get('relevance_score', 0):.2f}"          # Overall relevance
        ]
        
        # Add relevant content from search results
        relevant_content = []
        for result in search_results:
            # Only include results with reasonable confidence (> 0.5)
            if result.get('confidence', 0) > 0.5:
                content = result.get('content', '')
                if content:
                    # Limit content length to avoid overwhelming the LLM
                    relevant_content.append(content[:500])
        
        # Add relevant content to context if available
        if relevant_content:
            context_parts.append("Relevant information:")
            context_parts.extend(relevant_content)
        
        # Join all parts with double newlines for clear separation
        return "\n\n".join(context_parts)
    
    async def _generate_answer(self, query: str, context: str) -> str:
        """
        Generate answer using the language model.
        
        This method uses the LLM handler to generate the final answer to the
        user's query. It streams the response word by word and handles any
        errors that might occur during generation.
        
        Args:
            query: The user's original query
            context: The prepared context for the LLM
            
        Returns:
            str: The generated answer
            
        Note:
            The method uses streaming generation for better user experience.
            If generation fails, it returns an error message.
        """
        try:
            answer = ""  # Initialize empty answer
            # Stream the response word by word from the LLM
            for word in self.llm_handler.call_llm(query, context):
                answer += word  # Build the answer incrementally
            return answer
        except Exception as e:
            # Log the error and return a user-friendly error message
            self.log_activity(f"LLM generation error: {str(e)}", "error")
            return f"Error generating response: {str(e)}"
    
    def _prepare_sources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare sources for the response.
        
        This method filters and formats the search results to create a list
        of sources that can be cited in the final response. It only includes
        sources with reasonable confidence levels.
        
        Args:
            search_results: List of all search results
            
        Returns:
            List[Dict[str, Any]]: Formatted sources for citation
            
        Note:
            Sources with confidence below 0.3 are excluded to ensure
            only reliable information is cited.
        """
        sources = []  # List to hold formatted sources
        
        # Filter and format each search result
        for result in search_results:
            # Only include sources with reasonable confidence (> 0.3)
            if result.get('confidence', 0) > 0.3:
                sources.append({
                    'content': result.get('content', ''),                    # The actual content
                    'metadata': result.get('metadata', {}),                  # Associated metadata
                    'source': result.get('source', {}),                      # Source information
                    'confidence': result.get('confidence', 0.5),             # Confidence score
                    'source_type': result.get('source_type', 'unknown')      # Type of source
                })
        
        return sources

class AgenticRAG:
    """
    Main agentic RAG system orchestrator.
    
    This is the main class that orchestrates the entire agentic RAG pipeline.
    It manages the flow of queries through the agent chain and tracks performance
    metrics across all queries.
    
    The system follows a pipeline architecture where each agent has a specific
    role and can modify the QueryContext as it flows through the system.
    
    AGENT CHAIN:
    QueryAnalyzerAgent → SearchAgent → ReasoningAgent → SynthesisAgent
    
    Each agent processes the context and passes it to the next agent, building
    up a comprehensive understanding of the query and generating a final response.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the agentic RAG system with all agents.
        
        Args:
            config: Optional configuration dictionary for the system and agents
        """
        self.config = config or {}  # System configuration
        self.logger = logging.getLogger(__name__)  # System logger
        
        # Initialize all agents in the processing pipeline
        # Each agent can be configured independently
        self.query_analyzer = QueryAnalyzerAgent(self.config.get('query_analyzer', {}))
        self.search_agent = SearchAgent(self.config.get('search_agent', {}))
        self.reasoning_agent = ReasoningAgent(self.config.get('reasoning_agent', {}))
        self.synthesis_agent = SynthesisAgent(self.config.get('synthesis_agent', {}))
        
        # Performance tracking metrics
        # These are updated after each query to monitor system performance
        self.performance_metrics = {
            'total_queries': 0,                    # Total number of queries processed
            'average_processing_time': 0.0,        # Average time per query
            'success_rate': 0.0,                   # Percentage of successful queries
            'query_type_distribution': {},         # Distribution of query types
            'confidence_distribution': []          # Distribution of confidence scores
        }
    
    async def process_query(self, query: str, user_context: Dict[str, Any] = None) -> AgenticResponse:
        """
        Process a query through the agentic RAG system.
        
        This is the main entry point for processing user queries. It orchestrates
        the entire agent chain and handles errors gracefully.
        
        PROCESSING FLOW:
        1. Initialize QueryContext with the query and user context
        2. Pass context through the agent chain: analyze → search → reason → synthesize
        3. Update performance metrics
        4. Return the final AgenticResponse
        
        Args:
            query: The user's query string
            user_context: Optional additional context from the user
            
        Returns:
            AgenticResponse: Complete response with answer, sources, and metadata
            
        Note:
            The method includes comprehensive error handling to ensure the system
            always returns a response, even if processing fails.
        """
        start_time = time.time()  # Track total processing time
        
        self.logger.info(f"Processing agentic query: {query[:100]}...")
        
        try:
            # Step 1: Initialize query context with default values
            # These will be updated by the QueryAnalyzerAgent
            context = QueryContext(
                query=query,                                                    # The user's query
                query_type=QueryType.SEMANTIC_SEARCH,                          # Default type
                data_sources=[DataSourceType.VECTOR_DB],                       # Default sources
                reasoning="",                                                  # Will be populated by agents
                confidence=0.0,                                                # Will be calculated by agents
                metadata=user_context or {}                                    # User-provided context
            )
            
            # Step 2: Execute the agent chain in sequence
            # Each agent processes the context and passes it to the next
            context = await self.query_analyzer.process(context)    # Analyze and classify
            context = await self.search_agent.process(context)      # Search data sources
            context = await self.reasoning_agent.process(context)   # Analyze results
            response = await self.synthesis_agent.process(context)  # Generate final answer
            
            # Step 3: Update performance metrics with this query's results
            self._update_performance_metrics(response)
            
            self.logger.info(f"Agentic query completed in {response.processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            # Step 4: Handle any errors that occur during processing
            self.logger.error(f"Agentic query failed: {str(e)}")
            
            # Return a graceful error response
            return AgenticResponse(
                answer=f"Sorry, I encountered an error processing your query: {str(e)}",
                sources=[],                                                    # No sources on error
                reasoning=f"Error occurred during processing: {str(e)}",
                query_type=QueryType.SEMANTIC_SEARCH,                          # Default type
                confidence=0.0,                                                # Zero confidence on error
                processing_time=time.time() - start_time,                      # Time spent before error
                metadata={'error': str(e)},                                    # Error information
                agent_chain=[]                                                 # No agents completed
            )
    
    def _update_performance_metrics(self, response: AgenticResponse):
        """
        Update performance metrics with the results of a processed query.
        
        This method updates various performance tracking metrics after each
        query is processed. It maintains running averages and distributions
        to monitor system performance over time.
        
        Args:
            response: The AgenticResponse from processing a query
            
        Note:
            All metrics are updated using incremental averaging to avoid
            storing all historical data in memory.
        """
        # Increment total query count
        self.performance_metrics['total_queries'] += 1
        
        # Update average processing time using incremental averaging
        # Formula: new_avg = (old_avg * (n-1) + new_value) / n
        current_avg = self.performance_metrics['average_processing_time']
        total_queries = self.performance_metrics['total_queries']
        self.performance_metrics['average_processing_time'] = (
            (current_avg * (total_queries - 1) + response.processing_time) / total_queries
        )
        
        # Update query type distribution (count of each query type)
        query_type = response.query_type.value
        self.performance_metrics['query_type_distribution'][query_type] = (
            self.performance_metrics['query_type_distribution'].get(query_type, 0) + 1
        )
        
        # Update confidence distribution (store all confidence scores)
        self.performance_metrics['confidence_distribution'].append(response.confidence)
        
        # Update success rate (queries with confidence > 0.5 are considered successful)
        if response.confidence > 0.5:
            # Increment success count
            self.performance_metrics['success_rate'] = (
                (self.performance_metrics['success_rate'] * (total_queries - 1) + 1) / total_queries
            )
        else:
            # No change to success count
            self.performance_metrics['success_rate'] = (
                (self.performance_metrics['success_rate'] * (total_queries - 1)) / total_queries
            )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.
        
        Returns a copy of the current performance metrics for monitoring
        and analysis purposes.
        
        Returns:
            Dict[str, Any]: Copy of current performance metrics
            
        Note:
            Returns a copy to prevent external modification of internal metrics.
        """
        return self.performance_metrics.copy()
    
    def reset_metrics(self):
        """
        Reset performance metrics to initial state.
        
        This method clears all accumulated performance data and resets
        the metrics to their initial values. Useful for starting fresh
        or clearing old data.
        
        Note:
            This action cannot be undone. All historical performance data
            will be lost.
        """
        self.performance_metrics = {
            'total_queries': 0,                    # Reset query count
            'average_processing_time': 0.0,        # Reset average time
            'success_rate': 0.0,                   # Reset success rate
            'query_type_distribution': {},         # Clear type distribution
            'confidence_distribution': []          # Clear confidence history
        }
