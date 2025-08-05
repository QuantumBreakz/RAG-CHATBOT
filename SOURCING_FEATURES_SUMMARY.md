# Sourcing and Document Upload Features Implementation

## Overview

This document summarizes the implementation of two major features:

1. **Enhanced Sourcing with Chunk Display**: Shows detailed source information including chunks in responses
2. **Document Type Selection**: Allows users to choose between regular document processing and master document processing

## Backend Changes

### 1. Enhanced Upload Endpoint (`backend/api.py`)

**Modified `/upload` endpoint:**
- Added `document_type` parameter (default: "default", options: "default" or "master_document")
- Enhanced metadata storage for document types
- Returns document type in response

**Key changes:**
```python
@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(DEFAULT_CHUNK_SIZE),
    chunk_overlap: int = Form(DEFAULT_CHUNK_OVERLAP),
    document_type: str = Form("default")  # NEW: Document type selection
):
    # ... existing validation ...
    
    # Add document type metadata to all chunks
    for doc in docs:
        doc.metadata['document_type'] = document_type
        if document_type == "master_document":
            doc.metadata['is_master'] = True
            doc.metadata['master_document'] = file.filename
    
    # ... rest of processing ...
    
    return {
        "num_chunks": len(docs), 
        "status": "uploaded and embedded",
        "file_type": docs[0].metadata.get('file_type', 'unknown'),
        "document_type": document_type  # NEW: Return document type
    }
```

### 2. Enhanced Query Endpoint (`backend/api.py`)

**Modified `/query` endpoint:**
- Returns detailed source information including chunks
- Enhanced source metadata with confidence scores and document types

**Key changes:**
```python
# Prepare detailed source information with chunks
detailed_sources = []
for chunk, meta, source in filtered_chunks:
    detailed_sources.append({
        "content": chunk,
        "metadata": meta,
        "source": source,
        "filename": meta.get('filename', 'unknown'),
        "page": meta.get('page', None),
        "section": meta.get('section', None),
        "document_type": meta.get('document_type', 'default'),
        "is_master": meta.get('is_master', False),
        "chunk_id": meta.get('chunk_id', None),
        "confidence": source.get('confidence', 0.5) if source else 0.5
    })

return {
    "answer": answer,
    "context": context_str,
    "sources": sources,
    "detailed_sources": detailed_sources,  # NEW: Detailed source info
    "context_metadata": context_metadata
}
```

## Frontend Changes

### 1. Streamlit UI (`rag_core/ui.py`)

**Enhanced upload functionality:**
- Added document type selection dropdown
- Updated upload function to pass document type
- Enhanced source display in chat messages

**Key changes:**
```python
# Document type selection
document_type = st.selectbox(
    "Select document type:",
    options=[
        ("default", "Default - Process as regular document chunks"),
        ("master_document", "Master Document - Process as complete document for comprehensive analysis")
    ],
    format_func=lambda x: x[1],
    key="document_type_selector"
)

# Enhanced source display
if msg.get("detailed_sources"):
    with st.expander("📚 Sources & Chunks", expanded=False):
        sources = msg.get("detailed_sources", [])
        for idx, source in enumerate(sources):
            with st.container():
                st.markdown(f"**Source {idx + 1}:** {source.get('filename', 'Unknown')}")
                if source.get('page'):
                    st.caption(f"Page: {source['page']}")
                if source.get('document_type') == 'master_document':
                    st.caption("📋 Master Document")
                st.markdown(f"**Confidence:** {source.get('confidence', 0.5):.2f}")
                st.markdown(f"**Content:**")
                st.markdown(f"```\n{source.get('content', '')[:300]}{'...' if len(source.get('content', '')) > 300 else ''}\n```")
                st.divider()
```

### 2. React Frontend (`frontend/src/pages/ChatInterface.tsx`)

**Enhanced upload UI:**
- Added document type selection dropdown in sidebar
- Updated upload function to use selected document type
- Enhanced success messages to show document type

**Key changes:**
```typescript
// Document Type Selection
<div className="mb-4">
  <label className="text-xs text-muted-foreground mb-2 block">Document Type:</label>
  <select 
    className="w-full text-xs p-2 border border-border rounded bg-surface text-foreground"
    onChange={(e) => {
      const selectedType = e.target.value;
      localStorage.setItem('xor-rag-document-type', selectedType);
    }}
    defaultValue={localStorage.getItem('xor-rag-document-type') || 'default'}
  >
    <option value="default">Default - Regular chunks</option>
    <option value="master_document">Master Document - Complete analysis</option>
  </select>
</div>

// Enhanced upload function
const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, documentType: string = 'default') => {
  // ... existing code ...
  
  // Get the selected document type from localStorage
  const selectedDocType = localStorage.getItem('xor-rag-document-type') || 'default';
  formData.append('document_type', selectedDocType);
  
  // ... rest of function ...
  
  if (data.status?.includes('uploaded and embedded')) {
    const docType = data.document_type === 'master_document' ? 'Master Document' : 'Regular Document';
    showBanner(`${docType} embeddings created for "${file.name}" (${data.num_chunks} chunks).`, 'success');
  }
}
```

### 3. Enhanced Source Display (`frontend/src/components/SourceDisplay.tsx`)

**Enhanced source display:**
- Shows chunk content preview
- Displays confidence scores
- Indicates master document status
- Shows additional metadata

**Key changes:**
```typescript
interface Source {
  title: string;
  page?: number;
  section?: string;
  domain: string;
  attribution: string;
  content?: string;           // NEW: Chunk content
  filename?: string;          // NEW: Source filename
  document_type?: string;     // NEW: Document type
  is_master?: boolean;        // NEW: Master document flag
  confidence?: number;        // NEW: Confidence score
}

// Enhanced display
{source.content && (
  <div className="mt-2">
    <div className="text-xs font-medium text-muted-foreground mb-1">Chunk Content:</div>
    <div className="text-xs bg-muted/30 p-2 rounded border-l-2 border-primary">
      {source.content.length > 200 
        ? `${source.content.substring(0, 200)}...` 
        : source.content}
    </div>
  </div>
)}

{/* Show additional metadata */}
<div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
  {source.confidence && (
    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
      Confidence: {(source.confidence * 100).toFixed(0)}%
    </span>
  )}
  {source.is_master && (
    <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded">
      Master Document
    </span>
  )}
</div>
```

## Testing

A test script (`test_sourcing_features.py`) has been created to verify the functionality:

```bash
python test_sourcing_features.py
```

The test script verifies:
- Health check of the API
- Document upload with different document types
- Query functionality with source information
- Document listing with metadata

## Usage

### Document Upload with Type Selection

1. **Streamlit UI:**
   - Select document type from dropdown (Default/Master Document)
   - Upload files as usual
   - See enhanced success messages with document type

2. **React Frontend:**
   - Select document type from sidebar dropdown
   - Upload files using the upload button
   - See enhanced success messages

### Viewing Sources and Chunks

1. **Streamlit UI:**
   - Ask questions in the chat
   - Click "📚 Sources & Chunks" expander in AI responses
   - View detailed source information including chunks

2. **React Frontend:**
   - Ask questions in the chat
   - Sources are displayed below AI responses
   - Click on sources to see detailed information

## Benefits

1. **Enhanced Transparency:** Users can see exactly which chunks were used to generate responses
2. **Better Document Management:** Master documents can be processed differently for comprehensive analysis
3. **Improved Debugging:** Developers can see confidence scores and source metadata
4. **User Control:** Users can choose how their documents are processed

## Future Enhancements

1. **Source Filtering:** Allow users to filter sources by confidence or document type
2. **Source Highlighting:** Highlight specific parts of chunks that were most relevant
3. **Source Export:** Allow users to export source information
4. **Advanced Document Types:** Add more document type options (e.g., "reference", "tutorial", etc.) 