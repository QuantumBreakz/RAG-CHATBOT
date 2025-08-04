# Multi-OCR Pipeline with Text Validation System

## Overview

The Multi-OCR Pipeline is an enhanced document processing system that uses multiple OCR engines with consensus-based validation to minimize hallucinations and improve text extraction accuracy. This system is designed for production environments where high accuracy and reliability are critical.

## Key Features

### 🎯 **Consensus-Based Validation**
- **Multi-Engine Processing**: Uses multiple OCR engines simultaneously
- **Text Overlap Detection**: Compares outputs from different engines
- **Confidence Scoring**: Assigns confidence levels based on engine agreement
- **Quality Validation**: Validates text for semantic coherence and format preservation

### 🔧 **Advanced Preprocessing**
- **Image Enhancement**: Deskew, denoise, and contrast enhancement
- **Multi-format Support**: PDF, DOCX, CSV, Excel, and more
- **Language Detection**: Automatic language detection and processing
- **Batch Processing**: Efficient handling of large document collections

### 📊 **Quality Assessment**
- **Real-time Metrics**: Processing time, confidence scores, agreement rates
- **Quality Flags**: Automatic detection of potential issues
- **Performance Reports**: Comprehensive reporting and analytics
- **Error Analysis**: Detailed error tracking and resolution

## Architecture

```
Document Input
    ↓
Preprocessing (Deskew, Denoise, Enhance)
    ↓
Parallel OCR Processing
    ├── Tesseract Engine
    ├── PaddleOCR Engine (optional)
    └── EasyOCR Engine (optional)
    ↓
Text Alignment & Comparison
    ↓
Consensus Building
    ↓
Quality Validation
    ↓
Final Output with Confidence Scores
```

## Installation

### Prerequisites

1. **Tesseract OCR** (Required)
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-eng
   
   # macOS
   brew install tesseract
   
   # Windows
   # Download from https://github.com/UB-Mannheim/tesseract/wiki
   ```

2. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Optional OCR Engines**
   ```bash
   # PaddleOCR (for enhanced accuracy)
   pip install paddleocr
   
   # EasyOCR (for multilingual support)
   pip install easyocr
   ```

### System Requirements

- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 2GB+ for models and temporary files
- **CPU**: Multi-core processor recommended
- **GPU**: Optional, for faster processing with CUDA support

## Quick Start

### Basic Usage

```python
from rag_core.multi_ocr import MultiOCREngine, extract_text_from_pdf_enhanced

# Initialize multi-OCR engine
multi_ocr = MultiOCREngine()

# Process a PDF file
results = multi_ocr.process_pdf("document.pdf")

# Print results
for i, result in enumerate(results):
    print(f"Page {i+1}:")
    print(f"  Confidence: {result.confidence.value}")
    print(f"  Agreement Score: {result.agreement_score:.3f}")
    print(f"  Text: {result.text[:100]}...")
```

### Enhanced PDF Extraction

```python
# Use enhanced extraction with multi-OCR support
text = extract_text_from_pdf_enhanced("document.pdf", use_multi_ocr=True)
print(f"Extracted text length: {len(text)} characters")
```

### Quality Assessment

```python
from rag_core.ocr_quality import OCRQualityAssessor

# Initialize quality assessor
assessor = OCRQualityAssessor("quality_reports")

# Process document and assess quality
multi_ocr = MultiOCREngine()
results = multi_ocr.process_pdf("document.pdf")

# Assess quality for each page
for i, consensus_result in enumerate(results):
    report = assessor.assess_document_quality(
        filename="document.pdf",
        file_size=1024,
        engine_results=engine_results,  # From individual engines
        consensus_result=consensus_result,
        document_type="legal"
    )
    
    print(f"Page {i+1} Quality:")
    print(f"  Confidence: {report.confidence_level.value}")
    print(f"  Quality Flags: {report.quality_flags}")

# Generate comprehensive report
metrics = assessor.calculate_batch_metrics(assessor.document_reports)
report_path = assessor.generate_quality_report(metrics)
print(f"Quality report generated: {report_path}")
```

## Configuration

### Default Configuration

```python
from rag_core.ocr_config import get_config

# Get default configuration
config = get_config("default")

# Initialize with custom configuration
multi_ocr = MultiOCREngine(config)
```

### Configuration Presets

#### High Accuracy Configuration
```python
config = get_config("high_accuracy")
# Higher confidence thresholds, better preprocessing
```

#### Fast Processing Configuration
```python
config = get_config("fast")
# Lower DPI, faster processing, acceptable accuracy
```

#### Document-Specific Configurations
```python
# Legal documents
config = get_config("legal")

# Medical documents
config = get_config("medical")

# Technical documents
config = get_config("technical")
```

### Custom Configuration

```python
from rag_core.ocr_config import merge_configs

# Start with default config
base_config = get_config("default")

# Custom overrides
custom_config = {
    "consensus": {
        "high_confidence_threshold": 0.95,  # Higher threshold
        "medium_confidence_threshold": 0.80
    },
    "preprocessing": {
        "dpi": 400,  # Higher DPI
        "enhance_contrast": True
    }
}

# Merge configurations
final_config = merge_configs(base_config, custom_config)
multi_ocr = MultiOCREngine(final_config)
```

## Quality Metrics

### Confidence Levels

- **HIGH**: 2+ engines agree with >90% similarity
- **MEDIUM**: 2+ engines agree with 70-90% similarity
- **LOW**: Single engine or <70% similarity
- **REJECTED**: Contradictory or nonsensical text

### Quality Flags

- `engine_failures`: Number of failed OCR engines
- `low_confidence`: Low confidence in extracted text
- `low_agreement`: Low agreement between engines
- `slow_processing`: Processing time exceeds threshold
- `text_too_short`: Extracted text is too short
- `formatting_issues`: Problems with text formatting
- `mixed_language_content`: Mixed language detection

### Performance Metrics

- **Processing Time**: Time per page/document
- **Success Rate**: Percentage of successful extractions
- **Average Confidence**: Overall confidence score
- **Agreement Rate**: Inter-engine agreement percentage
- **Text per Second**: Processing throughput

## Integration with Document Processing

The multi-OCR system is fully integrated with the existing document processing pipeline:

```python
from rag_core.document import DocumentProcessor

# Process document with enhanced OCR
processor = DocumentProcessor()
docs = processor._process_pdf(file_content, "document.pdf")

# Check OCR-specific metadata
for doc in docs:
    if 'ocr_confidence' in doc.metadata:
        print(f"OCR Confidence: {doc.metadata['ocr_confidence']}")
    if 'ocr_engines' in doc.metadata:
        print(f"Engines Used: {doc.metadata['ocr_engines']}")
    if 'quality_flags' in doc.metadata:
        print(f"Quality Flags: {doc.metadata['quality_flags']}")
```

## Error Handling

### Common Issues and Solutions

#### 1. Tesseract Not Found
```bash
# Install Tesseract
sudo apt-get install tesseract-ocr

# Verify installation
tesseract --version
```

#### 2. Low Confidence Results
```python
# Use high-accuracy configuration
config = get_config("high_accuracy")
multi_ocr = MultiOCREngine(config)

# Increase DPI for better quality
config["preprocessing"]["dpi"] = 400
```

#### 3. Slow Processing
```python
# Use fast configuration
config = get_config("fast")
multi_ocr = MultiOCREngine(config)

# Disable preprocessing steps
config["preprocessing"]["deskew"] = False
config["preprocessing"]["enhance_contrast"] = False
```

#### 4. Memory Issues
```python
# Reduce batch size
config["preprocessing"]["dpi"] = 200  # Lower DPI
config["consensus"]["min_agreement_engines"] = 1  # Single engine acceptable
```

## Performance Optimization

### Speed vs Accuracy Trade-offs

| Configuration | Speed | Accuracy | Use Case |
|---------------|-------|----------|----------|
| `fast` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Large document batches |
| `default` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | General purpose |
| `high_accuracy` | ⭐⭐ | ⭐⭐⭐⭐⭐ | Critical documents |

### Memory Optimization

```python
# For large documents
config = {
    "preprocessing": {
        "dpi": 200,  # Lower DPI
        "deskew": False,  # Skip deskew
        "enhance_contrast": False  # Skip enhancement
    },
    "consensus": {
        "min_agreement_engines": 1  # Single engine acceptable
    }
}
```

### Batch Processing

```python
# Process multiple documents efficiently
documents = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
results = []

for doc in documents:
    result = multi_ocr.process_pdf(doc)
    results.extend(result)
    
    # Optional: Add delay between documents
    time.sleep(0.5)
```

## Testing

### Run Test Suite

```bash
python test_multi_ocr.py
```

### Individual Tests

```python
# Test basic functionality
from test_multi_ocr import test_multi_ocr_basic
test_multi_ocr_basic()

# Test quality assessment
from test_multi_ocr import test_quality_assessment
test_quality_assessment()

# Test performance
from test_multi_ocr import test_performance_benchmark
test_performance_benchmark()
```

## Reporting and Analytics

### Quality Reports

```python
# Generate comprehensive quality report
assessor = OCRQualityAssessor()
report_path = assessor.generate_quality_report(metrics)
print(f"Report generated: {report_path}")
```

### Export Document Reports

```python
# Export detailed document-level reports
export_path = assessor.export_document_reports()
print(f"Reports exported: {export_path}")
```

### Summary Statistics

```python
# Get summary statistics
summary = assessor.get_summary_statistics()
print(f"Success Rate: {summary['success_rate']*100:.1f}%")
print(f"Average Confidence: {summary['average_confidence']:.3f}")
print(f"Average Processing Time: {summary['average_processing_time']:.2f}s")
```

## API Reference

### MultiOCREngine

#### Methods

- `process_pdf(pdf_path, max_pages=None)`: Process PDF file
- `process_image(image, languages=None)`: Process single image
- `is_scanned_pdf(pdf_path, max_pages=3)`: Detect scanned PDF
- `preprocess_image(image)`: Preprocess image for OCR

#### Configuration

- `engines`: OCR engine configuration
- `consensus`: Consensus building parameters
- `preprocessing`: Image preprocessing options
- `validation`: Text validation criteria

### OCRQualityAssessor

#### Methods

- `assess_document_quality(...)`: Assess single document
- `calculate_batch_metrics(reports)`: Calculate batch statistics
- `generate_quality_report(metrics)`: Generate quality report
- `export_document_reports()`: Export detailed reports
- `get_summary_statistics()`: Get summary statistics

## Troubleshooting

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for OCR operations
logger = logging.getLogger('rag_core.multi_ocr')
logger.setLevel(logging.DEBUG)
```

### Common Error Messages

1. **"No OCR engines available"**
   - Install Tesseract OCR
   - Check engine configuration

2. **"Low confidence results"**
   - Use higher DPI settings
   - Enable image preprocessing
   - Check document quality

3. **"Slow processing"**
   - Use fast configuration
   - Reduce DPI settings
   - Disable preprocessing steps

4. **"Memory errors"**
   - Reduce batch size
   - Lower DPI settings
   - Process documents individually

## Contributing

### Adding New OCR Engines

1. **Implement Engine Interface**
   ```python
   def _extract_text_new_engine(self, image, lang):
       # Implement engine-specific extraction
       pass
   ```

2. **Update Configuration**
   ```python
   "new_engine": {
       "enabled": True,
       "priority": 2,
       "languages": ["eng"],
       "config": "engine_specific_config"
   }
   ```

3. **Add to Engine Selection**
   ```python
   elif engine_name == "new_engine":
       result = self._extract_text_new_engine(processed_image, lang)
       results.append(result)
   ```

### Performance Improvements

- Implement parallel processing for multiple engines
- Add GPU acceleration for image preprocessing
- Optimize text similarity calculations
- Implement caching for repeated operations

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the test suite for examples
3. Check the quality reports for detailed diagnostics
4. Enable debug logging for detailed error information

---

**Note**: This multi-OCR system is designed to work with the existing RAG chatbot infrastructure and provides significant improvements in text extraction accuracy and reliability for scanned documents. 