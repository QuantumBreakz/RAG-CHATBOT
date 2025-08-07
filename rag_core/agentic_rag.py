"""
Agentic RAG System

This module implements an agentic AI system that addresses the limitations of traditional RAG:
- Context Loss from Chunking
- Poor Performance with Numerical/Tabular Data  
- Inefficient Query Processing
- Limited Tool Selection
"""

import os
import sys
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
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

# Import existing RAG components
from .document import DocumentProcessor, EnhancedDocument
from .vectorstore import VectorStore
from .llm import LLMHandler
from .search import AdvancedSearch
from .multi_ocr import MultiOCREngine

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Types of queries the agent can handle"""
    SEMANTIC_SEARCH = "semantic_search"
    NUMERICAL_ANALYSIS = "numerical_analysis"
    FULL_DOCUMENT = "full_document"
    STRUCTURED_QUERY = "structured_query"
    HYBRID = "hybrid"

class DataSourceType(Enum):
    """Types of data sources"""
    VECTOR_DB = "vector_db"
    SQL_DB = "sql_db"
    FULL_DOCUMENT = "full_document"
    SPREADSHEET = "spreadsheet"
    DATABASE = "database"

@dataclass
class QueryContext:
    """Context for a query including metadata and reasoning"""
    query: str
    query_type: QueryType
    data_sources: List[DataSourceType]
    reasoning: str
    confidence: float
    metadata: Dict[str, Any]

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

class DocumentContextManager:
    """Manages full document context to prevent chunking loss"""
    
    def __init__(self, storage_dir: str = "data/document_contexts"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.context_cache = {}
    
    def store_full_document(self, filename: str, content: str, metadata: Dict[str, Any]):
        """Store full document content for context preservation"""
        doc_hash = hashlib.md5(content.encode()).hexdigest()
        
        context_data = {
            "filename": filename,
            "content": content,
            "metadata": metadata,
            "doc_hash": doc_hash,
            "stored_at": datetime.now().isoformat(),
            "length": len(content)
        }
        
        # Store in cache and disk
        self.context_cache[filename] = context_data
        
        cache_file = self.storage_dir / f"{doc_hash}.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(context_data, f)
        
        logger.info(f"Stored full document context for {filename} ({len(content)} chars)")
    
    def get_full_document(self, filename: str) -> Optional[Dict[str, Any]]:
        """Retrieve full document context"""
        if filename in self.context_cache:
            return self.context_cache[filename]
        
        # Try to load from disk
        for cache_file in self.storage_dir.glob("*.pkl"):
            try:
                with open(cache_file, 'rb') as f:
                    context_data = pickle.load(f)
                    if context_data["filename"] == filename:
                        self.context_cache[filename] = context_data
                        return context_data
            except Exception as e:
                logger.warning(f"Failed to load context from {cache_file}: {e}")
        
        return None
    
    def get_document_summary(self, filename: str) -> Optional[str]:
        """Get a summary of the full document"""
        context = self.get_full_document(filename)
        if context:
            # Use LLM to generate summary
            llm = LLMHandler()
            prompt = f"Summarize this document in 2-3 sentences:\n\n{context['content'][:2000]}..."
            return llm.generate_response(prompt)
        return None

class NumericalDataProcessor:
    """Handles numerical and tabular data analysis"""
    
    def __init__(self):
        self.data_cache = {}
        self.sql_connections = {}
    
    def process_spreadsheet(self, file_path: str) -> pd.DataFrame:
        """Process spreadsheet data and store for numerical analysis"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
            
            # Store in cache
            self.data_cache[file_path] = df
            
            # Create SQL table for complex queries
            self._create_sql_table(file_path, df)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to process spreadsheet {file_path}: {e}")
            raise
    
    def _create_sql_table(self, file_path: str, df: pd.DataFrame):
        """Create SQL table for the dataframe"""
        db_path = f"data/numerical_data.db"
        conn = sqlite3.connect(db_path)
        
        table_name = Path(file_path).stem.replace(' ', '_').lower()
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        self.sql_connections[file_path] = conn
        logger.info(f"Created SQL table '{table_name}' for {file_path}")
    
    def analyze_numerical_query(self, query: str, data_sources: List[str]) -> Dict[str, Any]:
        """Analyze numerical queries using pandas and SQL"""
        results = {}
        
        for source in data_sources:
            if source in self.data_cache:
                df = self.data_cache[source]
                
                # Extract numerical operations from query
                analysis = self._extract_numerical_operations(query, df)
                results[source] = analysis
        
        return results
    
    def _extract_numerical_operations(self, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract and perform numerical operations from query"""
        query_lower = query.lower()
        results = {}
        
        # Detect numerical operations
        if 'sum' in query_lower or 'total' in query_lower:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                results[f"sum_{col}"] = df[col].sum()
        
        if 'average' in query_lower or 'mean' in query_lower:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                results[f"average_{col}"] = df[col].mean()
        
        if 'maximum' in query_lower or 'highest' in query_lower:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                max_val = df[col].max()
                max_idx = df[col].idxmax()
                results[f"max_{col}"] = {
                    "value": max_val,
                    "row": df.iloc[max_idx].to_dict()
                }
        
        if 'minimum' in query_lower or 'lowest' in query_lower:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                min_val = df[col].min()
                min_idx = df[col].idxmin()
                results[f"min_{col}"] = {
                    "value": min_val,
                    "row": df.iloc[min_idx].to_dict()
                }
        
        return results

class QueryAnalyzer:
    """Analyzes queries to determine the best processing strategy"""
    
    def __init__(self):
        self.llm = LLMHandler()
    
    def analyze_query(self, query: str, available_sources: List[str]) -> QueryContext:
        """Analyze query to determine processing strategy"""
        
        # Use LLM to analyze query type and reasoning
        analysis_prompt = f"""
        Analyze this query and determine the best processing strategy:
        
        Query: "{query}"
        Available sources: {available_sources}
        
        Determine:
        1. Query type (semantic_search, numerical_analysis, full_document, structured_query, hybrid)
        2. Required data sources
        3. Reasoning for the choice
        4. Confidence level (0-1)
        
        Respond in JSON format:
        {{
            "query_type": "type",
            "data_sources": ["source1", "source2"],
            "reasoning": "explanation",
            "confidence": 0.85
        }}
        """
        
        try:
            response = self.llm.generate_response(analysis_prompt)
            analysis = json.loads(response)
            
            return QueryContext(
                query=query,
                query_type=QueryType(analysis["query_type"]),
                data_sources=[DataSourceType(ds) for ds in analysis["data_sources"]],
                reasoning=analysis["reasoning"],
                confidence=analysis["confidence"],
                metadata={"analysis": analysis}
            )
            
        except Exception as e:
            logger.warning(f"Query analysis failed, using fallback: {e}")
            return self._fallback_analysis(query, available_sources)
    
    def _fallback_analysis(self, query: str, available_sources: List[str]) -> QueryContext:
        """Fallback analysis when LLM analysis fails"""
        query_lower = query.lower()
        
        # Simple keyword-based analysis
        if any(word in query_lower for word in ['sum', 'total', 'average', 'maximum', 'minimum', 'highest', 'lowest']):
            query_type = QueryType.NUMERICAL_ANALYSIS
            data_sources = [DataSourceType.SPREADSHEET, DataSourceType.SQL_DB]
            reasoning = "Query contains numerical operations"
        elif any(word in query_lower for word in ['summary', 'overview', 'entire', 'full']):
            query_type = QueryType.FULL_DOCUMENT
            data_sources = [DataSourceType.FULL_DOCUMENT]
            reasoning = "Query requests full document context"
        else:
            query_type = QueryType.SEMANTIC_SEARCH
            data_sources = [DataSourceType.VECTOR_DB]
            reasoning = "Default to semantic search"
        
        return QueryContext(
            query=query,
            query_type=query_type,
            data_sources=data_sources,
            reasoning=reasoning,
            confidence=0.7,
            metadata={"fallback": True}
        )

# class AgenticRAG:
#     """Main agentic RAG system that intelligently handles different query types"""
    
#     def __init__(self, config: Dict[str, Any] = None):
#         self.config = config or self._get_default_config()
        
#         # Initialize components
#         self.context_manager = DocumentContextManager()
#         self.numerical_processor = NumericalDataProcessor()
#         self.query_analyzer = QueryAnalyzer()
#         self.vectorstore = VectorStore()
#         self.llm = LLMHandler()
#         self.search_engine = AdvancedSearch()
        
#         # Performance tracking
#         self.query_history = []
#         self.performance_metrics = {}
    
#     def _get_default_config(self) -> Dict[str, Any]:
#         """Get default configuration"""
#         return {
#             "enable_full_document_context": True,
#             "enable_numerical_analysis": True,
#             "enable_hybrid_search": True,
#             "max_context_length": 10000,
#             "confidence_threshold": 0.7,
#             "cache_results": True,
#             "parallel_processing": True
#         }
    
#     async def process_query(self, query: str, user_context: Dict[str, Any] = None) -> AgenticResponse:
#         """Process query using agentic reasoning"""
#         start_time = datetime.now()
        
#         try:
#             # Step 1: Analyze query and determine strategy
#             query_context = self.query_analyzer.analyze_query(query, self._get_available_sources())
            
#             # Step 2: Execute query based on analysis
#             if query_context.query_type == QueryType.NUMERICAL_ANALYSIS:
#                 result = await self._handle_numerical_query(query, query_context)
#             elif query_context.query_type == QueryType.FULL_DOCUMENT:
#                 result = await self._handle_full_document_query(query, query_context)
#             elif query_context.query_type == QueryType.STRUCTURED_QUERY:
#                 result = await self._handle_structured_query(query, query_context)
#             elif query_context.query_type == QueryType.HYBRID:
#                 result = await self._handle_hybrid_query(query, query_context)
#             else:
#                 result = await self._handle_semantic_query(query, query_context)
            
#             # Step 3: Generate final response
#             processing_time = (datetime.now() - start_time).total_seconds()
            
#             response = AgenticResponse(
#                 answer=result["answer"],
#                 sources=result["sources"],
#                 reasoning=query_context.reasoning,
#                 query_type=query_context.query_type,
#                 confidence=query_context.confidence,
#                 processing_time=processing_time,
#                 metadata={
#                     "query_context": asdict(query_context),
#                     "result_metadata": result.get("metadata", {})
#                 }
#             )
            
#             # Step 4: Update performance tracking
#             self._update_performance_metrics(query_context, response)
            
#             return response
            
#         except Exception as e:
#             logger.error(f"Query processing failed: {e}")
#             return AgenticResponse(
#                 answer=f"Sorry, I encountered an error processing your query: {str(e)}",
#                 sources=[],
#                 reasoning="Error occurred during processing",
#                 query_type=QueryType.SEMANTIC_SEARCH,
#                 confidence=0.0,
#                 processing_time=(datetime.now() - start_time).total_seconds(),
#                 metadata={"error": str(e)}
#             )
    
#     async def _handle_numerical_query(self, query: str, context: QueryContext) -> Dict[str, Any]:
#         """Handle numerical analysis queries"""
#         logger.info(f"Processing numerical query: {query}")
        
#         # Get available spreadsheet data
#         spreadsheet_sources = [f for f in self.numerical_processor.data_cache.keys()]
        
#         if not spreadsheet_sources:
#             return {
#                 "answer": "No numerical data available for analysis.",
#                 "sources": [],
#                 "metadata": {"error": "no_numerical_data"}
#             }
        
#         # Analyze numerical data
#         analysis_results = self.numerical_processor.analyze_numerical_query(query, spreadsheet_sources)
        
#         # Generate response using LLM
#         analysis_text = json.dumps(analysis_results, indent=2)
#         prompt = f"""
#         Based on this numerical analysis, answer the user's question:
        
#         User Question: {query}
        
#         Analysis Results:
#         {analysis_text}
        
#         Provide a clear, concise answer based on the numerical analysis.
#         """
        
#         answer = self.llm.generate_response(prompt)
        
#         return {
#             "answer": answer,
#             "sources": [{"type": "numerical_analysis", "data": analysis_results}],
#             "metadata": {"analysis_results": analysis_results}
#         }
    
#     async def _handle_full_document_query(self, query: str, context: QueryContext) -> Dict[str, Any]:
#         """Handle queries requiring full document context"""
#         logger.info(f"Processing full document query: {query}")
        
#         # Get available documents
#         available_docs = self._get_available_documents()
        
#         if not available_docs:
#             return {
#                 "answer": "No documents available for full context analysis.",
#                 "sources": [],
#                 "metadata": {"error": "no_documents"}
#             }
        
#         # Get full document contexts
#         full_contexts = []
#         for doc in available_docs:
#             context = self.context_manager.get_full_document(doc)
#             if context:
#                 full_contexts.append(context)
        
#         if not full_contexts:
#             return {
#                 "answer": "No full document contexts available.",
#                 "sources": [],
#                 "metadata": {"error": "no_full_contexts"}
#             }
        
#         # Generate response using full context
#         context_text = "\n\n".join([ctx["content"][:2000] for ctx in full_contexts])
#         prompt = f"""
#         Based on the full document context, answer the user's question:
        
#         User Question: {query}
        
#         Document Context:
#         {context_text}
        
#         Provide a comprehensive answer using the full document context.
#         """
        
#         answer = self.llm.generate_response(prompt)
        
#         return {
#             "answer": answer,
#             "sources": [{"type": "full_document", "documents": [ctx["filename"] for ctx in full_contexts]}],
#             "metadata": {"full_contexts": len(full_contexts)}
#         }
    
#     async def _handle_structured_query(self, query: str, context: QueryContext) -> Dict[str, Any]:
#         """Handle structured queries (SQL, etc.)"""
#         logger.info(f"Processing structured query: {query}")
        
#         # This would implement SQL query processing
#         # For now, fall back to semantic search
#         return await self._handle_semantic_query(query, context)
    
#     async def _handle_hybrid_query(self, query: str, context: QueryContext) -> Dict[str, Any]:
#         """Handle hybrid queries using multiple strategies"""
#         logger.info(f"Processing hybrid query: {query}")
        
#         # Execute multiple query strategies in parallel
#         tasks = [
#             self._handle_semantic_query(query, context),
#             self._handle_full_document_query(query, context)
#         ]
        
#         results = await asyncio.gather(*tasks, return_exceptions=True)
        
#         # Combine results
#         combined_answer = self._combine_hybrid_results(results)
        
#         return {
#             "answer": combined_answer,
#             "sources": [r["sources"] for r in results if isinstance(r, dict)],
#             "metadata": {"hybrid_results": len(results)}
#         }
    
#     async def _handle_semantic_query(self, query: str, context: QueryContext) -> Dict[str, Any]:
#         """Handle traditional semantic search queries"""
#         logger.info(f"Processing semantic query: {query}")
        
#         # Use existing vector search
#         results = self.search_engine.search_documents(query, limit=5)
        
#         if not results:
#             return {
#                 "answer": "No relevant information found.",
#                 "sources": [],
#                 "metadata": {"error": "no_results"}
#             }
        
#         # Generate response
#         context_text = "\n\n".join([r.content for r in results])
#         prompt = f"""
#         Based on the retrieved information, answer the user's question:
        
#         User Question: {query}
        
#         Retrieved Information:
#         {context_text}
        
#         Provide a clear, accurate answer based on the retrieved information.
#         """
        
#         answer = self.llm.generate_response(prompt)
        
#         return {
#             "answer": answer,
#             "sources": [{"type": "semantic_search", "results": [{"content": r.content, "filename": r.filename, "score": r.score} for r in results]}],
#             "metadata": {"results_count": len(results)}
#         }
    
#     def _combine_hybrid_results(self, results: List[Dict[str, Any]]) -> str:
#         """Combine results from multiple query strategies"""
#         valid_results = [r for r in results if isinstance(r, dict) and "answer" in r]
        
#         if not valid_results:
#             return "Unable to generate a comprehensive answer."
        
#         # Use LLM to combine results
#         combined_text = "\n\n".join([r["answer"] for r in valid_results])
#         prompt = f"""
#         Combine these different answers into a comprehensive response:
        
#         {combined_text}
        
#         Provide a unified, coherent answer that incorporates all relevant information.
#         """
        
#         return self.llm.generate_response(prompt)
    
#     def _get_available_sources(self) -> List[str]:
#         """Get list of available data sources"""
#         sources = []
        
#         # Add vector database sources
#         try:
#             collection = self.vectorstore.get_vector_collection()
#             if collection:
#                 sources.append("vector_db")
#         except:
#             pass
        
#         # Add numerical data sources
#         if self.numerical_processor.data_cache:
#             sources.append("spreadsheet")
        
#         # Add full document sources
#         if self.context_manager.context_cache:
#             sources.append("full_document")
        
#         return sources
    
#     def _get_available_documents(self) -> List[str]:
#         """Get list of available documents"""
#         return list(self.context_manager.context_cache.keys())
    
#     def _update_performance_metrics(self, query_context: QueryContext, response: AgenticResponse):
#         """Update performance tracking metrics"""
#         self.query_history.append({
#             "timestamp": datetime.now().isoformat(),
#             "query": query_context.query,
#             "query_type": query_context.query_type.value,
#             "processing_time": response.processing_time,
#             "confidence": response.confidence
#         })
        
#         # Keep only recent history
#         if len(self.query_history) > 1000:
#             self.query_history = self.query_history[-1000:]
    
#     def get_performance_metrics(self) -> Dict[str, Any]:
#         """Get performance metrics"""
#         if not self.query_history:
#             return {}
        
#         processing_times = [q["processing_time"] for q in self.query_history]
#         confidences = [q["confidence"] for q in self.query_history]
        
#         return {
#             "total_queries": len(self.query_history),
#             "avg_processing_time": sum(processing_times) / len(processing_times),
#             "avg_confidence": sum(confidences) / len(confidences),
#             "query_type_distribution": self._get_query_type_distribution(),
#             "recent_queries": self.query_history[-10:]
#         }
    
#     def _get_query_type_distribution(self) -> Dict[str, int]:
#         """Get distribution of query types"""
#         distribution = {}
#         for query in self.query_history:
#             query_type = query["query_type"]
#             distribution[query_type] = distribution.get(query_type, 0) + 1
#         return distribution 