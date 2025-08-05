# Whole Document Mode Guide

## Overview

The RAG system supports two document processing modes:

1. **Default Mode** (Default): Uses semantic chunking for efficient search and retrieval
2. **Master Document Mode**: Treats entire documents as single chunks for complete context preservation

## How It Works

### Default Mode (Default)
- Documents are split into semantic chunks (800 characters by default)
- Chunks overlap by 400 characters to maintain context
- Optimized for efficient search and retrieval
- Better for large documents and quick queries

### Master Document Mode
- Entire documents are processed as single chunks
- Preserves complete context and prevents information fragmentation
- Better for comprehensive analysis and detailed responses
- Ideal for legal documents, contracts, technical specifications, etc.

## Configuration

### Environment Variable
```bash
# Default: false (uses semantic chunking)
MASTER_DOCUMENT_MODE=false

# Enable: true (uses whole document processing)
MASTER_DOCUMENT_MODE=true
```

### Frontend Toggle
The frontend includes a toggle button in the chat interface:
- **Default**: Shows "Default" button
- **Master Doc**: Shows "Master Doc" button with green gradient

## API Endpoints

### Get Current Mode
```http
GET /config/master-document-mode
```

Response:
```json
{
  "status": "success",
  "master_document_mode": false
}
```

### Toggle Mode
```http
POST /config/master-document-mode
Content-Type: application/x-www-form-urlencoded

enable=true
```

Response:
```json
{
  "status": "success",
  "master_document_mode": true,
  "message": "Master Document Mode enabled"
}
```

## Document Processing Logic

### Code Location: `rag_core/document.py`

```python
# Check if master document mode is enabled
from .config import MASTER_DOCUMENT_MODE
if MASTER_DOCUMENT_MODE:
    # Use whole document chunking to preserve all context
    chunked_documents = DocumentProcessor._whole_document_chunking(documents)
    logger.info(f"Created {len(chunked_documents)} whole document chunks from {len(documents)} documents (Master Document Mode - Full Context Preservation)")
else:
    # Use semantic chunking for better search granularity
    chunked_documents = DocumentProcessor._semantic_chunking(documents, chunk_size, chunk_overlap)
    logger.info(f"Created {len(chunked_documents)} semantic chunks from {len(documents)} documents (Default Mode - Granular Search)")
```

### Whole Document Chunking Method

```python
@staticmethod
def _whole_document_chunking(docs: List[Document]) -> List[Document]:
    """
    Create a single chunk containing the entire document content.
    This preserves all context and prevents information loss.
    """
    if not docs:
        return []
    
    # Combine all document content into a single chunk
    all_content = "\n\n".join([doc.page_content for doc in docs])
    
    # Create a single document with all content
    whole_doc = Document(
        page_content=all_content,
        metadata={
            **docs[0].metadata,
            'chunk_type': 'whole_document',
            'total_chunks': 1,
            'document_length': len(all_content),
            'processing_mode': 'master_document',
            'preserves_context': True,
            'information_completeness': 'full'
        }
    )
    
    return [whole_doc]
```

## System Prompt Adaptation

The system prompt automatically adapts based on the mode:

### Default Mode
- Concise, focused answers
- Key points and essential information
- Efficient use of available context
- Clear, direct responses

### Master Document Mode
- Comprehensive analysis requirements
- Detailed explanations with step-by-step breakdowns
- Complete context utilization
- Deep insights and cross-references
- Extensive responses (500-1000+ words when appropriate)

## Use Cases

### Default Mode (Recommended for)
- Quick queries and searches
- Large document collections
- General Q&A
- Performance-critical applications
- Real-time responses

### Master Document Mode (Recommended for)
- Legal document analysis
- Contract review and interpretation
- Technical specification analysis
- Comprehensive research
- Detailed explanations
- Cross-document analysis
- Policy and procedure review

## Testing

Run the test script to verify both modes work correctly:

```bash
python test_whole_document_mode.py
```

This will test:
1. Default mode chunking behavior
2. Master document mode whole document processing
3. Mode toggle functionality
4. Metadata verification

## Performance Considerations

### Default Mode
- Faster processing
- Lower memory usage
- Better for large document collections
- More granular search results

### Master Document Mode
- Slower processing for large documents
- Higher memory usage
- Better for comprehensive analysis
- Complete context preservation

## Best Practices

1. **Use Default Mode** for:
   - General document collections
   - Quick queries
   - Performance-critical applications

2. **Use Master Document Mode** for:
   - Important legal documents
   - Technical specifications
   - Comprehensive analysis needs
   - When complete context is critical

3. **Toggle as Needed**:
   - Switch to Master Document Mode for specific important documents
   - Return to Default Mode for general use

## Troubleshooting

### Common Issues

1. **Mode not changing**: Check environment variable and restart the application
2. **Memory issues**: Large documents in Master Document Mode may require more memory
3. **Slow responses**: Master Document Mode processes entire documents, which can be slower

### Debug Information

Check the logs for chunking information:
```
Created 1 whole document chunks from 1 documents (Master Document Mode - Full Context Preservation)
Created 5 semantic chunks from 1 documents (Default Mode - Granular Search)
``` 