"""
Configuration for Multi-OCR Pipeline

This module provides configuration presets for different OCR scenarios and requirements.
"""

from typing import Dict, Any, List

# Default configuration for production use
DEFAULT_CONFIG = {
    "engines": {
        "tesseract": {
            "enabled": True,
            "priority": 1,
            "languages": ["eng"],
            "config": "--oem 3 --psm 6"
        },
        "paddleocr": {
            "enabled": True,  # Enable PaddleOCR for better consensus
            "priority": 2,
            "languages": ["en"]
        },
        "easyocr": {
            "enabled": True,  # Enable EasyOCR for better consensus
            "priority": 3,
            "languages": ["en"]
        }
    },
    "consensus": {
        "high_confidence_threshold": 0.90,
        "medium_confidence_threshold": 0.70,
        "min_agreement_engines": 2,
        "fuzzy_match_threshold": 0.85
    },
    "preprocessing": {
        "deskew": True,
        "denoise": True,
        "enhance_contrast": True,
        "dpi": 300
    },
    "validation": {
        "check_semantic_coherence": True,
        "check_language_consistency": True,
        "check_format_preservation": True,
        "min_text_length": 10
    }
}

# High-accuracy configuration for critical documents
HIGH_ACCURACY_CONFIG = {
    "engines": {
        "tesseract": {
            "enabled": True,
            "priority": 1,
            "languages": ["eng"],
            "config": "--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;:()[]{}'\"-+=/\\|@#$%^&*~`"
        },
        "paddleocr": {
            "enabled": False,
            "priority": 2,
            "languages": ["en"]
        },
        "easyocr": {
            "enabled": False,
            "priority": 3,
            "languages": ["en"]
        }
    },
    "consensus": {
        "high_confidence_threshold": 0.95,  # Higher threshold
        "medium_confidence_threshold": 0.80,  # Higher threshold
        "min_agreement_engines": 2,
        "fuzzy_match_threshold": 0.90
    },
    "preprocessing": {
        "deskew": True,
        "denoise": True,
        "enhance_contrast": True,
        "dpi": 400  # Higher DPI
    },
    "validation": {
        "check_semantic_coherence": True,
        "check_language_consistency": True,
        "check_format_preservation": True,
        "min_text_length": 20  # Higher minimum length
    }
}

# Fast processing configuration for large documents
FAST_CONFIG = {
    "engines": {
        "tesseract": {
            "enabled": True,
            "priority": 1,
            "languages": ["eng"],
            "config": "--oem 1 --psm 6"  # Faster engine mode
        },
        "paddleocr": {
            "enabled": False,
            "priority": 2,
            "languages": ["en"]
        },
        "easyocr": {
            "enabled": False,
            "priority": 3,
            "languages": ["en"]
        }
    },
    "consensus": {
        "high_confidence_threshold": 0.85,  # Lower threshold
        "medium_confidence_threshold": 0.60,  # Lower threshold
        "min_agreement_engines": 1,  # Single engine acceptable
        "fuzzy_match_threshold": 0.80
    },
    "preprocessing": {
        "deskew": False,  # Skip deskew for speed
        "denoise": True,
        "enhance_contrast": False,  # Skip contrast enhancement
        "dpi": 200  # Lower DPI
    },
    "validation": {
        "check_semantic_coherence": False,  # Skip validation for speed
        "check_language_consistency": False,
        "check_format_preservation": False,
        "min_text_length": 5  # Lower minimum length
    }
}

# Multilingual configuration
MULTILINGUAL_CONFIG = {
    "engines": {
        "tesseract": {
            "enabled": True,
            "priority": 1,
            "languages": ["eng", "fra", "deu", "spa", "ita", "por", "rus", "chi_sim", "jpn", "kor"],
            "config": "--oem 3 --psm 6"
        },
        "paddleocr": {
            "enabled": False,
            "priority": 2,
            "languages": ["en", "ch", "french", "german", "korean", "japan"]
        },
        "easyocr": {
            "enabled": False,
            "priority": 3,
            "languages": ["en", "ch_sim", "ch_tra", "ja", "ko", "th", "ar", "hi"]
        }
    },
    "consensus": {
        "high_confidence_threshold": 0.85,
        "medium_confidence_threshold": 0.65,
        "min_agreement_engines": 2,
        "fuzzy_match_threshold": 0.80
    },
    "preprocessing": {
        "deskew": True,
        "denoise": True,
        "enhance_contrast": True,
        "dpi": 300
    },
    "validation": {
        "check_semantic_coherence": False,  # Disable for multilingual
        "check_language_consistency": True,
        "check_format_preservation": True,
        "min_text_length": 10
    }
}

# Configuration for specific document types
DOCUMENT_TYPE_CONFIGS = {
    "legal": {
        "engines": {
            "tesseract": {
                "enabled": True,
                "priority": 1,
                "languages": ["eng"],
                "config": "--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;:()[]{}'\"-+=/\\|@#$%^&*~`§¶"
            }
        },
        "consensus": {
            "high_confidence_threshold": 0.95,
            "medium_confidence_threshold": 0.80,
            "min_agreement_engines": 2,
            "fuzzy_match_threshold": 0.90
        },
        "preprocessing": {
            "deskew": True,
            "denoise": True,
            "enhance_contrast": True,
            "dpi": 400
        },
        "validation": {
            "check_semantic_coherence": True,
            "check_language_consistency": True,
            "check_format_preservation": True,
            "min_text_length": 15
        }
    },
    "medical": {
        "engines": {
            "tesseract": {
                "enabled": True,
                "priority": 1,
                "languages": ["eng"],
                "config": "--oem 3 --psm 6"
            }
        },
        "consensus": {
            "high_confidence_threshold": 0.90,
            "medium_confidence_threshold": 0.75,
            "min_agreement_engines": 2,
            "fuzzy_match_threshold": 0.85
        },
        "preprocessing": {
            "deskew": True,
            "denoise": True,
            "enhance_contrast": True,
            "dpi": 350
        },
        "validation": {
            "check_semantic_coherence": True,
            "check_language_consistency": True,
            "check_format_preservation": True,
            "min_text_length": 10
        }
    },
    "technical": {
        "engines": {
            "tesseract": {
                "enabled": True,
                "priority": 1,
                "languages": ["eng"],
                "config": "--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;:()[]{}'\"-+=/\\|@#$%^&*~`αβγδεθλμπσφψωΔΛΠΣΦΨΩ"
            }
        },
        "consensus": {
            "high_confidence_threshold": 0.90,
            "medium_confidence_threshold": 0.70,
            "min_agreement_engines": 2,
            "fuzzy_match_threshold": 0.85
        },
        "preprocessing": {
            "deskew": True,
            "denoise": True,
            "enhance_contrast": True,
            "dpi": 300
        },
        "validation": {
            "check_semantic_coherence": False,  # Technical documents may have unusual formatting
            "check_language_consistency": True,
            "check_format_preservation": True,
            "min_text_length": 5
        }
    }
}

# Fast performance configuration for speed-optimized processing
FAST_PERFORMANCE_CONFIG = {
    "engines": {
        "tesseract": {
            "enabled": True,
            "priority": 1,
            "languages": ["eng"],
            "config": "--oem 1 --psm 6"  # Fastest engine mode
        },
        "paddleocr": {
            "enabled": False,  # Disabled for speed
            "priority": 2,
            "languages": ["en"]
        },
        "easyocr": {
            "enabled": False,  # Disabled for speed
            "priority": 3,
            "languages": ["en"]
        }
    },
    "consensus": {
        "high_confidence_threshold": 0.80,  # Lower threshold
        "medium_confidence_threshold": 0.60,  # Lower threshold
        "min_agreement_engines": 1,  # Single engine acceptable
        "fuzzy_match_threshold": 0.75
    },
    "preprocessing": {
        "deskew": False,  # Disabled for speed
        "denoise": False,  # Disabled for speed
        "enhance_contrast": False,  # Disabled for speed
        "dpi": 150  # Very low DPI for speed
    },
    "validation": {
        "check_semantic_coherence": False,  # Disabled for speed
        "check_language_consistency": False,  # Disabled for speed
        "check_format_preservation": False,  # Disabled for speed
        "min_text_length": 3  # Very low minimum length
    },
    "performance": {
        "enable_caching": True,
        "cache_size": 2000,  # Larger cache
        "parallel_processing": False,  # Disabled for single engine
        "max_workers": 1,
        "timeout_seconds": 15,  # Shorter timeout
        "enable_offline_mode": True
    }
}

# Offline-only configuration
OFFLINE_CONFIG = {
    "engines": {
        "tesseract": {
            "enabled": True,
            "priority": 1,
            "languages": ["eng"],
            "config": "--oem 1 --psm 6"
        },
        "paddleocr": {
            "enabled": True,
            "priority": 2,
            "languages": ["en"]
        },
        "easyocr": {
            "enabled": True,
            "priority": 3,
            "languages": ["en"]
        }
    },
    "consensus": {
        "high_confidence_threshold": 0.85,
        "medium_confidence_threshold": 0.65,
        "min_agreement_engines": 2,
        "fuzzy_match_threshold": 0.80
    },
    "preprocessing": {
        "deskew": False,
        "denoise": True,
        "enhance_contrast": False,
        "dpi": 200
    },
    "validation": {
        "check_semantic_coherence": False,
        "check_language_consistency": True,
        "check_format_preservation": False,
        "min_text_length": 5
    },
    "performance": {
        "enable_caching": True,
        "cache_size": 1000,
        "parallel_processing": True,
        "max_workers": 4,
        "timeout_seconds": 30,
        "enable_offline_mode": True
    }
}

def get_config(config_name: str = "default") -> Dict[str, Any]:
    """
    Get configuration by name.
    
    Args:
        config_name: Name of the configuration preset
        
    Returns:
        Configuration dictionary
    """
    configs = {
        "default": DEFAULT_CONFIG,
        "high_accuracy": HIGH_ACCURACY_CONFIG,
        "fast": FAST_CONFIG,
        "fast_performance": FAST_PERFORMANCE_CONFIG,
        "offline": OFFLINE_CONFIG,
        "multilingual": MULTILINGUAL_CONFIG,
        **DOCUMENT_TYPE_CONFIGS
    }
    
    if config_name not in configs:
        raise ValueError(f"Unknown configuration '{config_name}'. Available: {list(configs.keys())}")
    
    return configs[config_name]

def get_config_for_document_type(document_type: str) -> Dict[str, Any]:
    """
    Get configuration optimized for specific document type.
    
    Args:
        document_type: Type of document (legal, medical, technical, etc.)
        
    Returns:
        Configuration dictionary
    """
    if document_type in DOCUMENT_TYPE_CONFIGS:
        return DOCUMENT_TYPE_CONFIGS[document_type]
    else:
        # Return default config for unknown document types
        return DEFAULT_CONFIG

def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configurations, with override_config taking precedence.
    
    Args:
        base_config: Base configuration
        override_config: Override configuration
        
    Returns:
        Merged configuration
    """
    import copy
    merged = copy.deepcopy(base_config)
    
    def merge_dict(target: Dict, source: Dict):
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                merge_dict(target[key], value)
            else:
                target[key] = value
    
    merge_dict(merged, override_config)
    return merged 