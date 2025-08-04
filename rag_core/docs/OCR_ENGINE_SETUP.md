# OCR Engine Setup Guide

This guide provides detailed instructions for setting up all OCR engines used in the multi-OCR pipeline system.

## Overview

The multi-OCR system supports three OCR engines:
1. **Tesseract** (Primary) - Fast, reliable, good for general use
2. **PaddleOCR** (Secondary) - High accuracy, good for complex documents
3. **EasyOCR** (Tertiary) - Multilingual support, good for diverse content

## Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 2GB+ for models and temporary files
- **CPU**: Multi-core processor recommended
- **GPU**: Optional, for faster processing with CUDA support

### Operating System Support

| Engine | Windows | macOS | Linux |
|--------|---------|-------|-------|
| Tesseract | ✅ | ✅ | ✅ |
| PaddleOCR | ✅ | ✅ | ✅ |
| EasyOCR | ✅ | ✅ | ✅ |

## Installation Guide

### 1. Tesseract OCR (Required)

#### Windows
```bash
# Download from https://github.com/UB-Mannheim/tesseract/wiki
# Install with default settings
# Add to PATH: C:\Program Files\Tesseract-OCR

# Verify installation
tesseract --version
```

#### macOS
```bash
# Using Homebrew
brew install tesseract tesseract-lang

# Verify installation
tesseract --version
```

#### Linux (Ubuntu/Debian)
```bash
# Install Tesseract and English language pack
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Verify installation
tesseract --version
```

#### Linux (CentOS/RHEL)
```bash
# Install Tesseract
sudo yum install tesseract tesseract-langpack-eng

# Verify installation
tesseract --version
```

### 2. Python Dependencies

Install all required Python packages:

```bash
# Install base requirements
pip install -r requirements.txt

# Or install individually
pip install opencv-python==4.9.0.80
pip install nltk==3.8.1
pip install paddleocr==2.7.0.3
pip install easyocr==1.7.0
```

### 3. PaddleOCR Setup

PaddleOCR requires additional setup for optimal performance:

#### Install PaddleOCR
```bash
# Install PaddleOCR
pip install paddleocr==2.7.0.3

# Verify installation
python -c "from paddleocr import PaddleOCR; print('PaddleOCR installed successfully')"
```

#### GPU Support (Optional)
```bash
# Install CUDA version if you have NVIDIA GPU
pip install paddlepaddle-gpu

# For CPU-only
pip install paddlepaddle
```

#### Download Models (Automatic)
PaddleOCR will automatically download required models on first use:
- Text detection model
- Text recognition model
- Angle classification model

### 4. EasyOCR Setup

EasyOCR is simpler to set up but requires more disk space:

#### Install EasyOCR
```bash
# Install EasyOCR
pip install easyocr==1.7.0

# Verify installation
python -c "import easyocr; print('EasyOCR installed successfully')"
```

#### Download Models (Automatic)
EasyOCR will automatically download models on first use:
- English language model (~1GB)
- Additional language models as needed

## Automated Setup

Use the provided setup script for automated installation and testing:

```bash
# Install all OCR engines
python setup_ocr_engines.py install

# Test all OCR engines
python setup_ocr_engines.py test

# Interactive setup
python setup_ocr_engines.py
```

## Configuration

### Default Configuration

The system is configured to use all three engines by default:

```python
from rag_core.ocr_config import get_config

# Get default configuration
config = get_config("default")

# Initialize multi-OCR engine
from rag_core.multi_ocr import MultiOCREngine
multi_ocr = MultiOCREngine(config)
```

### Engine-Specific Configuration

#### Tesseract Configuration
```python
config = {
    "engines": {
        "tesseract": {
            "enabled": True,
            "priority": 1,
            "languages": ["eng"],
            "config": "--oem 3 --psm 6"  # OCR Engine Mode 3, Page Segmentation Mode 6
        }
    }
}
```

#### PaddleOCR Configuration
```python
config = {
    "engines": {
        "paddleocr": {
            "enabled": True,
            "priority": 2,
            "languages": ["en"],
            "config": {
                "use_angle_cls": True,
                "lang": "en",
                "use_gpu": False,  # Set to True for GPU
                "show_log": False
            }
        }
    }
}
```

#### EasyOCR Configuration
```python
config = {
    "engines": {
        "easyocr": {
            "enabled": True,
            "priority": 3,
            "languages": ["en"],
            "config": {
                "lang_list": ['en'],
                "gpu": False,  # Set to True for GPU
                "recog_network": 'standard',
                "detector_network": 'craft'
            }
        }
    }
}
```

## Testing

### Individual Engine Testing

Test each engine separately:

```python
from test_multi_ocr import test_ocr_engines_individual
test_ocr_engines_individual()
```

### Multi-Engine Consensus Testing

Test the consensus system:

```python
from test_multi_ocr import test_multi_engine_consensus
test_multi_engine_consensus()
```

### Performance Comparison

Compare engine performance:

```python
from test_multi_ocr import test_engine_comparison
test_engine_comparison()
```

### Complete Test Suite

Run all tests:

```bash
python test_multi_ocr.py
```

## Troubleshooting

### Common Issues

#### 1. Tesseract Not Found
```bash
# Windows: Add to PATH
set PATH=%PATH%;C:\Program Files\Tesseract-OCR

# Linux/macOS: Install language packs
sudo apt-get install tesseract-ocr-eng  # Ubuntu
brew install tesseract-lang             # macOS
```

#### 2. PaddleOCR Installation Issues
```bash
# Clear pip cache
pip cache purge

# Install with specific version
pip install paddleocr==2.7.0.3 --no-cache-dir

# Check CUDA compatibility
nvidia-smi  # If you have NVIDIA GPU
```

#### 3. EasyOCR Memory Issues
```bash
# Reduce memory usage
export CUDA_VISIBLE_DEVICES=""  # Disable GPU
export OMP_NUM_THREADS=1        # Limit CPU threads
```

#### 4. Model Download Issues
```bash
# Manual model download for PaddleOCR
python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='en')"

# Manual model download for EasyOCR
python -c "import easyocr; easyocr.Reader(['en'])"
```

### Performance Optimization

#### GPU Acceleration
```python
# Enable GPU for PaddleOCR
config = {
    "engines": {
        "paddleocr": {
            "enabled": True,
            "config": {
                "use_gpu": True,  # Enable GPU
                "gpu_mem": 500    # GPU memory in MB
            }
        }
    }
}

# Enable GPU for EasyOCR
config = {
    "engines": {
        "easyocr": {
            "enabled": True,
            "config": {
                "gpu": True  # Enable GPU
            }
        }
    }
}
```

#### Memory Optimization
```python
# Reduce memory usage
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

## Usage Examples

### Basic Usage
```python
from rag_core.multi_ocr import MultiOCREngine

# Initialize with default configuration
multi_ocr = MultiOCREngine()

# Process PDF
results = multi_ocr.process_pdf("document.pdf")

# Print results
for i, result in enumerate(results):
    print(f"Page {i+1}: {result.confidence.value} confidence")
    print(f"Text: {result.text[:100]}...")
```

### Custom Configuration
```python
from rag_core.ocr_config import get_config, merge_configs

# Get high-accuracy configuration
config = get_config("high_accuracy")

# Custom overrides
custom_config = {
    "preprocessing": {
        "dpi": 400  # Higher DPI for better quality
    }
}

# Merge configurations
final_config = merge_configs(config, custom_config)
multi_ocr = MultiOCREngine(final_config)
```

### Quality Assessment
```python
from rag_core.ocr_quality import OCRQualityAssessor

# Initialize quality assessor
assessor = OCRQualityAssessor("quality_reports")

# Process and assess
results = multi_ocr.process_pdf("document.pdf")
for result in results:
    report = assessor.assess_document_quality(
        filename="document.pdf",
        file_size=1024,
        engine_results=engine_results,
        consensus_result=result,
        document_type="legal"
    )
    print(f"Quality: {report.confidence_level.value}")
```

## Performance Benchmarks

### Expected Performance

| Engine | Speed | Accuracy | Memory Usage | Use Case |
|--------|-------|----------|--------------|----------|
| Tesseract | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | General purpose |
| PaddleOCR | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | High accuracy |
| EasyOCR | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | Multilingual |

### Memory Requirements

| Engine | CPU Memory | GPU Memory | Disk Space |
|--------|------------|------------|------------|
| Tesseract | 100MB | N/A | 50MB |
| PaddleOCR | 500MB | 1GB | 200MB |
| EasyOCR | 1GB | 2GB | 1GB |

## Support

### Getting Help

1. **Check Installation**: Run `python setup_ocr_engines.py test`
2. **Review Logs**: Check console output for error messages
3. **Verify Dependencies**: Ensure all packages are installed correctly
4. **Test Individual Engines**: Use the individual engine tests

### Common Error Messages

- **"No OCR engines available"**: Install at least Tesseract
- **"PaddleOCR not available"**: Run `pip install paddleocr`
- **"EasyOCR not available"**: Run `pip install easyocr`
- **"Low confidence results"**: Check document quality and preprocessing settings
- **"Memory errors"**: Reduce DPI or disable preprocessing steps

### Performance Tips

1. **Use GPU** when available for PaddleOCR and EasyOCR
2. **Adjust DPI** based on document quality (200-400)
3. **Enable preprocessing** for better accuracy
4. **Use consensus** for critical documents
5. **Monitor memory** usage for large documents

---

**Note**: The multi-OCR system is designed to work with the existing RAG chatbot infrastructure. All engines are optional except Tesseract, which is required as the primary engine. 