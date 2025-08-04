# Agentic RAG System Documentation

## Overview

The Agentic RAG system transforms your traditional RAG chatbot into an intelligent AI agent that addresses the fundamental limitations of traditional RAG systems:

- **Context Loss from Chunking**
- **Poor Performance with Numerical/Tabular Data**
- **Inefficient Query Processing**
- **Limited Tool Selection**

## Key Features

### 🧠 **Intelligent Query Analysis**
The system automatically analyzes queries to determine the best processing strategy:

- **Semantic Search**: For general knowledge questions
- **Numerical Analysis**: For spreadsheet and calculation queries
- **Full Document**: For comprehensive document analysis
- **Structured Query**: For database and SQL operations
- **Hybrid**: For complex queries requiring multiple approaches

### 📊 **Numerical Data Processing**
Advanced handling of spreadsheets and numerical data:

- **Pandas Integration**: Direct DataFrame operations
- **SQL Database**: Automatic table creation for complex queries
- **Mathematical Operations**: Sum, average, min, max, etc.
- **Cross-Reference Analysis**: Compare data across sources

### 📄 **Full Document Context**
Prevents context loss by maintaining complete document context:

- **Document Storage**: Full documents cached for context preservation
- **Smart Summarization**: LLM-generated summaries for quick reference
- **Context Retrieval**: Intelligent selection of relevant full documents
- **Metadata Tracking**: Rich document metadata for better understanding

### 🔧 **Intelligent Tool Selection**
Automatically chooses the best tools for each query:

- **Vector Search**: For semantic similarity
- **SQL Queries**: For structured data analysis
- **Full Document Retrieval**: For comprehensive context
- **Hybrid Processing**: Combines multiple approaches

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Query Input   │───▶│ Query Analyzer  │───▶│ Agentic RAG     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Full Document  │◀───│ Context Manager │◀───│ Response        │
│    Context      │    └─────────────────┘    │ Generator       │
└─────────────────┘                           └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐           │
│  Numerical      │◀───│ Numerical       │◀──────────┘
│  Data Sources   │    │ Processor       │
└─────────────────┘    └─────────────────┘
```

## Usage Examples

### Basic Query Processing

```python
from rag_core.agentic_rag import AgenticRAG

# Initialize agentic RAG
agentic_rag = AgenticRAG()

# Process query
response = await agentic_rag.process_query("What is the total revenue?")

print(f"Answer: {response.answer}")
print(f"Query Type: {response.query_type.value}")
print(f"Confidence: {response.confidence}")
print(f"Processing Time: {response.processing_time}s")
```

### Numerical Data Analysis

```python
# Upload spreadsheet for analysis
spreadsheet_path = "sales_data.csv"
df = agentic_rag.numerical_processor.process_spreadsheet(spreadsheet_path)

# Query numerical data
response = await agentic_rag.process_query("Which week had the highest sales?")
print(response.answer)
```

### Full Document Context

```python
# Store full document context
document_content = "Full document text..."
agentic_rag.context_manager.store_full_document(
    "annual_report.pdf",
    document_content,
    {"type": "annual_report", "year": 2024}
)

# Query with full context
response = await agentic_rag.process_query("Give me a summary of the annual report")
print(response.answer)
```

## API Endpoints

### Agentic Query Processing

```bash
# Process query with agentic RAG
curl -X POST http://localhost:8000/agentic/query \
  -F "question=What is the total revenue?" \
  -F "user_context={}"

# Stream response
curl -X POST http://localhost:8000/agentic/query/stream \
  -F "question=What is the total revenue?"
```

### Spreadsheet Upload

```bash
# Upload spreadsheet for numerical analysis
curl -X POST http://localhost:8000/agentic/upload/spreadsheet \
  -F "file=@sales_data.csv" \
  -F "description=Monthly sales data"
```

### Query Analysis

```bash
# Analyze query intent without processing
curl -X POST http://localhost:8000/agentic/analyze \
  -F "query=What is the total revenue?"
```

### Performance Metrics

```bash
# Get performance metrics
curl http://localhost:8000/agentic/performance
```

## Query Types and Examples

### 1. Numerical Analysis Queries

**Examples:**
- "What is the total sales across all weeks?"
- "Which week had the highest sales?"
- "What is the average sales per week?"
- "Calculate the sum of all revenue"

**Processing:**
- Uses pandas for DataFrame operations
- Performs mathematical calculations
- Returns precise numerical results

### 2. Full Document Queries

**Examples:**
- "Give me a summary of the annual report"
- "What are the key points from the document?"
- "Provide an overview of the entire document"

**Processing:**
- Retrieves full document context
- Uses LLM for comprehensive analysis
- Preserves document structure and relationships

### 3. Semantic Search Queries

**Examples:**
- "What are the key achievements mentioned?"
- "Find information about revenue growth"
- "What challenges were discussed?"

**Processing:**
- Uses vector search for similarity
- Retrieves relevant chunks
- Combines information from multiple sources

### 4. Hybrid Queries

**Examples:**
- "Compare sales performance across regions"
- "What is the revenue performance and key achievements?"
- "Analyze both numerical data and document content"

**Processing:**
- Combines multiple query strategies
- Integrates numerical and textual analysis
- Provides comprehensive responses

## Configuration

### Default Configuration

```python
config = {
    "enable_full_document_context": True,
    "enable_numerical_analysis": True,
    "enable_hybrid_search": True,
    "max_context_length": 10000,
    "confidence_threshold": 0.7,
    "cache_results": True,
    "parallel_processing": True
}
```

### Custom Configuration

```python
from rag_core.agentic_rag import AgenticRAG

# Custom configuration
config = {
    "enable_full_document_context": True,
    "enable_numerical_analysis": True,
    "max_context_length": 15000,  # Increased context length
    "confidence_threshold": 0.8,   # Higher confidence threshold
    "cache_results": True,
    "parallel_processing": True
}

agentic_rag = AgenticRAG(config)
```

## Performance Improvements

### Traditional RAG vs Agentic RAG

| Aspect | Traditional RAG | Agentic RAG |
|--------|----------------|-------------|
| **Context Loss** | ❌ High (chunking) | ✅ Minimal (full context) |
| **Numerical Data** | ❌ Poor (vectorized) | ✅ Excellent (direct processing) |
| **Query Intelligence** | ❌ None (one-shot) | ✅ High (intelligent analysis) |
| **Tool Selection** | ❌ Limited (vector only) | ✅ Intelligent (multi-tool) |
| **Accuracy** | ⚠️ Variable | ✅ Consistent |

### Performance Metrics

```python
# Get performance metrics
metrics = agentic_rag.get_performance_metrics()

print(f"Total Queries: {metrics['total_queries']}")
print(f"Average Processing Time: {metrics['avg_processing_time']:.2f}s")
print(f"Average Confidence: {metrics['avg_confidence']:.3f}")
print(f"Query Type Distribution: {metrics['query_type_distribution']}")
```

## Testing

### Run Agentic RAG Tests

```bash
# Run comprehensive test suite
python rag_core/tests/test_agentic_rag.py

# Test specific components
python -c "
from rag_core.agentic_rag import AgenticRAG
import asyncio

async def test():
    rag = AgenticRAG()
    response = await rag.process_query('What is the total revenue?')
    print(f'Query Type: {response.query_type.value}')
    print(f'Answer: {response.answer}')

asyncio.run(test())
"
```

### Test Coverage

- ✅ Context Loss Prevention
- ✅ Numerical Data Analysis
- ✅ Query Intelligence
- ✅ Hybrid Processing
- ✅ Performance Metrics
- ✅ API Integration

## Migration from Traditional RAG

### 1. Import Changes

```python
# Old
from rag_core.search import SearchEngine
results = search_engine.search(query)

# New
from rag_core.agentic_rag import AgenticRAG
response = await agentic_rag.process_query(query)
```

### 2. Query Processing

```python
# Old: Simple vector search
results = vectorstore.search(query)

# New: Intelligent processing
response = await agentic_rag.process_query(query)
print(f"Query Type: {response.query_type.value}")
print(f"Answer: {response.answer}")
```

### 3. Numerical Data

```python
# Old: No numerical support
# Had to manually process spreadsheets

# New: Direct numerical analysis
df = agentic_rag.numerical_processor.process_spreadsheet("data.csv")
response = await agentic_rag.process_query("What is the total sales?")
```

## Troubleshooting

### Common Issues

1. **Query Type Detection Issues**
   ```python
   # Check query analysis
   query_context = agentic_rag.query_analyzer.analyze_query(query, sources)
   print(f"Detected Type: {query_context.query_type.value}")
   ```

2. **Numerical Data Not Found**
   ```python
   # Check available sources
   sources = agentic_rag._get_available_sources()
   print(f"Available sources: {sources}")
   ```

3. **Performance Issues**
   ```python
   # Check performance metrics
   metrics = agentic_rag.get_performance_metrics()
   print(f"Average processing time: {metrics['avg_processing_time']}")
   ```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from rag_core.agentic_rag import AgenticRAG
agentic_rag = AgenticRAG()
```

## Future Enhancements

### Planned Features

1. **Advanced SQL Integration**
   - Direct SQL query processing
   - Database schema understanding
   - Complex join operations

2. **Multi-Modal Processing**
   - Image analysis integration
   - Audio transcription
   - Video content processing

3. **Advanced Reasoning**
   - Chain-of-thought reasoning
   - Multi-step problem solving
   - Hypothesis generation

4. **Real-time Learning**
   - Query pattern learning
   - Performance optimization
   - Adaptive strategies

## Contributing

### Adding New Query Types

1. Add to `QueryType` enum
2. Implement handler in `AgenticRAG`
3. Update query analyzer
4. Add tests

### Adding New Data Sources

1. Implement data source interface
2. Add to `DataSourceType` enum
3. Update source detection
4. Add processing logic

## License

This agentic RAG system is part of the RAG Chatbot project and follows the same license terms. 