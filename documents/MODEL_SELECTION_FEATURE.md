# Intelligent Model Selection Feature

## Overview

The XOR RAG Chatbot now includes an intelligent model selection feature that automatically detects when attached files would benefit from OpenAI's advanced capabilities, particularly for images, mathematical expressions, and technical blueprints. **This feature works for chat attachments only, not knowledge base uploads.**

## Features

### 🎯 Automatic Content Detection

The system automatically detects:
- **Images**: PNG, JPG, JPEG, GIF, BMP, TIFF, WebP, SVG files
- **Mathematical Content**: Expressions like "25X54", equations, formulas, calculations
- **Blueprints/Technical Drawings**: Engineering diagrams, schematics, architectural plans

### 🎨 Model Selection Modal

When special content is detected in chat attachments, users see a beautiful modal with:
- **Blurred background** for focus
- **Clear explanations** of what was detected
- **Two model options**:
  - **Local Model**: Basic text extraction and processing
  - **OpenAI Model**: Advanced image analysis, mathematical reasoning, and technical understanding

### 🔧 Session-Level Model Selection

- **Chat Session Scope**: Once a model is selected, it's used for the entire chat session
- **Toast Notification**: Shows which model is being used for the current chat
- **No Knowledge Base Integration**: Attachments are processed in the cloud, not stored locally
- **Automatic Reset**: Model selection resets when starting a new conversation

## How It Works

### 1. Chat Attachment Detection
```typescript
// When user attaches file to chat
const handleInlineFileAttach = async (e) => {
  const file = e.target.files[0];
  const detectionResult = await detectContentType(file);
  
  if (shouldShowModelSelection(detectionResult)) {
    setShowModelSelection(true); // Show modal
  } else {
    setAttachedFile(file); // Use local model
  }
};
```

### 2. User Selection
```typescript
// User chooses model in modal
const handleModelSelection = async (selectedModel: 'local' | 'openai') => {
  setSessionModel(selectedModel); // Set for entire chat session
  setAttachedFile(pendingFile);
  setShowModelToast(true); // Show toast notification
};
```

### 3. Chat Processing
```typescript
// All subsequent messages use the selected model
if (sessionModel === 'openai') {
  formData.append('online_model', 'openai');
}
if (attachedFile) {
  formData.append('file', attachedFile);
}
```

## Key Differences from Knowledge Base Uploads

| Feature | Knowledge Base Upload | Chat Attachment |
|---------|----------------------|-----------------|
| **Model Selection** | ❌ No modal | ✅ Modal appears |
| **Storage** | ✅ Stored locally | ❌ Processed in cloud |
| **Scope** | Global for all chats | Session-specific |
| **Purpose** | Long-term knowledge | Temporary analysis |

## Detection Patterns

### Mathematical Expressions
- `25X54` pattern (multiplication)
- Basic arithmetic: `100 + 200 = 300`
- Equations: `x = 5`, `y = 2x + 3`
- Functions: `sqrt(16)`, `log(x)`, `sin(θ)`
- Mathematical symbols: `∫`, `∑`, `√`, `∞`, `±`, `≤`, `≥`
- Greek letters: `α`, `β`, `γ`, `δ`, `ε`, `θ`, `λ`, `μ`, `π`, `σ`, `φ`, `ω`

### Blueprint/Technical Keywords
- `blueprint`, `drawing`, `schematic`, `diagram`
- `engineering`, `architectural`, `floorplan`
- `circuit`, `wiring`, `mechanical`
- `dimension`, `scale`, `measurement`
- `assembly`, `component`, `part`, `section`
- `isometric`, `orthographic`, `projection`

### Image Files
- Direct image files: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.webp`, `.svg`
- PDFs containing images (detected via PyMuPDF)

## API Changes

### Query Endpoint (Updated)
```python
@app.post("/query")
async def query_rag(
    question: str = Form(...),
    # ... other parameters ...
    online_model: str = Form(None),  # "openai" for OpenAI model
    file: UploadFile = File(None)    # Attached file for analysis
):
```

### Response Format
```json
{
  "answer": "Generated response",
  "sources": [],
  "context_metadata": {},
  "model_used": "openai"  // or "local"
}
```

## Frontend Components

### ModelSelectionModal
```typescript
<ModelSelectionModal
  isOpen={showModelSelection}
  onClose={() => setShowModelSelection(false)}
  onModelSelect={handleModelSelection}
  detectedType={detectedContentType}
  fileName={pendingFile?.name}
  isLoading={modelSelectionLoading}
/>
```

### ModelToast
```typescript
<ModelToast
  isVisible={showModelToast}
  model={sessionModel}
  onClose={() => setShowModelToast(false)}
/>
```

## User Experience Flow

1. **User attaches file** to chat (📎 button)
2. **System detects content** type automatically
3. **Modal appears** if special content detected
4. **User selects model** (Local or OpenAI)
5. **Toast notification** shows selected model
6. **All subsequent messages** use selected model
7. **Model resets** when starting new conversation

## Configuration

### Environment Variables
No additional environment variables required. The feature uses existing OpenAI configuration.

### Settings
The feature respects existing model settings in the UI:
- OpenAI API key (if configured)
- Model preferences
- Temperature and token settings

## Benefits

### For Users
- **Better Results**: Automatic selection of the best model for content type
- **Transparency**: Clear explanation of what was detected and why
- **Control**: Option to override automatic selection
- **Session Consistency**: Same model used throughout chat session
- **No Storage**: Files processed in cloud, not stored locally

### For System
- **Optimized Performance**: Use the right tool for the job
- **Cost Efficiency**: Only use OpenAI when beneficial
- **Privacy**: No local storage of sensitive files
- **Scalability**: Cloud processing for complex content
- **Reliability**: Robust error handling and validation

## Future Enhancements

- **Machine Learning**: Train models to improve detection accuracy
- **More Content Types**: Support for charts, graphs, tables
- **Batch Processing**: Handle multiple files with different content types
- **User Preferences**: Remember user's model preferences per content type
- **Advanced Analytics**: Track which model performs better for different content types
- **File Type Support**: Support for more file formats (Excel, PowerPoint, etc.)

## Troubleshooting

### Modal Not Appearing
- Check browser console for JavaScript errors
- Verify file type is supported
- Ensure content detection patterns match your file
- **Note**: Modal only appears for chat attachments, not knowledge base uploads

### OpenAI Not Available
- Check OpenAI API key configuration
- Verify internet connectivity
- System will automatically fallback to local model

### Detection Accuracy
- Adjust confidence thresholds in `contentDetection.ts`
- Add custom patterns for your specific use cases
- Review detection logs for false positives/negatives

### Session Model Issues
- Model selection resets when starting new conversation
- Model selection resets when switching conversations
- Check toast notification for current model status
