"""
Cross-Language Query Support System
Provides language detection, translation, and multi-language processing capabilities
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class LanguageCode(Enum):
    """Supported language codes"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    HINDI = "hi"
    DUTCH = "nl"
    SWEDISH = "sv"
    NORWEGIAN = "no"
    DANISH = "da"
    FINNISH = "fi"
    POLISH = "pl"
    TURKISH = "tr"
    UNKNOWN = "unknown"


class TranslationProvider(Enum):
    """Translation service providers"""
    GOOGLE_TRANSLATE = "google_translate"
    DEEPL = "deepl"
    AZURE_TRANSLATOR = "azure_translator"
    AWS_TRANSLATE = "aws_translate"
    LIBRE_TRANSLATE = "libre_translate"
    CUSTOM = "custom"


@dataclass
class LanguageDetectionResult:
    """Result of language detection"""
    detected_language: LanguageCode
    confidence: float
    detected_text: str
    language_name: str
    script: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranslationResult:
    """Result of translation operation"""
    original_text: str
    translated_text: str
    source_language: LanguageCode
    target_language: LanguageCode
    confidence: float
    provider: TranslationProvider
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiLanguageQuery:
    """Multi-language query with detection and translation"""
    original_query: str
    detected_language: LanguageCode
    translated_queries: Dict[LanguageCode, str]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class LanguageProcessor:
    """Cross-language query processing system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = self._get_default_config()
        if config:
            self.config.update(config)
        
        self.logger = logging.getLogger(__name__)
        self._initialize_language_patterns()
        self._initialize_translation_cache()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "default_language": LanguageCode.ENGLISH,
            "supported_languages": [
                LanguageCode.ENGLISH, LanguageCode.SPANISH, LanguageCode.FRENCH,
                LanguageCode.GERMAN, LanguageCode.ITALIAN, LanguageCode.PORTUGUESE,
                LanguageCode.RUSSIAN, LanguageCode.CHINESE_SIMPLIFIED,
                LanguageCode.JAPANESE, LanguageCode.KOREAN, LanguageCode.ARABIC
            ],
            "translation_provider": TranslationProvider.GOOGLE_TRANSLATE,
            "translation_cache_ttl": 3600,  # 1 hour
            "min_confidence_threshold": 0.7,
            "enable_auto_translation": True,
            "preserve_original": True,
            "max_query_length": 1000
        }
    
    def _initialize_language_patterns(self):
        """Initialize language detection patterns"""
        self.language_patterns = {
            LanguageCode.ENGLISH: {
                "patterns": [
                    r'\b(the|and|or|but|in|on|at|to|for|of|with|by)\b',
                    r'\b(is|are|was|were|be|been|being)\b',
                    r'\b(this|that|these|those)\b'
                ],
                "name": "English",
                "script": "Latin"
            },
            LanguageCode.SPANISH: {
                "patterns": [
                    r'\b(el|la|los|las|de|del|al|por|para|con|sin|sobre)\b',
                    r'\b(es|son|era|eran|ser|sido|siendo)\b',
                    r'\b(este|esta|estos|estas|ese|esa|esos|esas)\b',
                    r'[áéíóúñü]'
                ],
                "name": "Spanish",
                "script": "Latin"
            },
            LanguageCode.FRENCH: {
                "patterns": [
                    r'\b(le|la|les|de|du|des|au|aux|par|pour|avec|sans)\b',
                    r'\b(est|sont|était|étaient|être|été|étant)\b',
                    r'\b(ce|cette|ces|celui|celle|ceux|celles)\b',
                    r'[àâäéèêëïîôöùûüÿç]'
                ],
                "name": "French",
                "script": "Latin"
            },
            LanguageCode.GERMAN: {
                "patterns": [
                    r'\b(der|die|das|den|dem|des|ein|eine|eines|einer)\b',
                    r'\b(ist|sind|war|waren|sein|gewesen|seiend)\b',
                    r'\b(dieser|diese|dieses|jener|jene|jenes)\b',
                    r'[äöüß]'
                ],
                "name": "German",
                "script": "Latin"
            },
            LanguageCode.ITALIAN: {
                "patterns": [
                    r'\b(il|la|lo|i|gli|le|di|del|della|dello|delle|degli)\b',
                    r'\b(è|sono|era|erano|essere|stato|stata|stati|state)\b',
                    r'\b(questo|questa|questi|queste|quello|quella|quelli|quelle)\b',
                    r'[àèéìíîòóù]'
                ],
                "name": "Italian",
                "script": "Latin"
            },
            LanguageCode.PORTUGUESE: {
                "patterns": [
                    r'\b(o|a|os|as|de|do|da|dos|das|em|no|na|nos|nas)\b',
                    r'\b(é|são|era|eram|ser|sido|sendo)\b',
                    r'\b(este|esta|estes|estas|esse|essa|esses|essas)\b',
                    r'[áâãàçéêíóôõú]'
                ],
                "name": "Portuguese",
                "script": "Latin"
            },
            LanguageCode.RUSSIAN: {
                "patterns": [
                    r'[а-яё]',
                    r'\b(и|в|на|с|по|для|от|до|из|за|под|над)\b',
                    r'\b(это|этот|эта|эти|тот|та|те)\b'
                ],
                "name": "Russian",
                "script": "Cyrillic"
            },
            LanguageCode.CHINESE_SIMPLIFIED: {
                "patterns": [
                    r'[\u4e00-\u9fff]',
                    r'\b(的|是|在|有|和|与|或|但|而|因为|所以)\b'
                ],
                "name": "Chinese (Simplified)",
                "script": "Han"
            },
            LanguageCode.JAPANESE: {
                "patterns": [
                    r'[\u3040-\u309f]',  # Hiragana
                    r'[\u30a0-\u30ff]',  # Katakana
                    r'[\u4e00-\u9fff]',  # Kanji
                    r'\b(は|が|を|に|へ|で|と|から|まで|より|の|も|や|か)\b'
                ],
                "name": "Japanese",
                "script": "Mixed"
            },
            LanguageCode.KOREAN: {
                "patterns": [
                    r'[\uac00-\ud7af]',  # Hangul
                    r'\b(은|는|이|가|을|를|에|에서|로|으로|와|과|의|도|만)\b'
                ],
                "name": "Korean",
                "script": "Hangul"
            },
            LanguageCode.ARABIC: {
                "patterns": [
                    r'[\u0600-\u06ff]',  # Arabic
                    r'\b(في|من|إلى|على|عن|مع|هذا|هذه|هؤلاء|التي|الذي)\b'
                ],
                "name": "Arabic",
                "script": "Arabic"
            }
        }
    
    def _initialize_translation_cache(self):
        """Initialize translation cache"""
        self.translation_cache = {}
        self.cache_timestamps = {}
    
    def detect_language(self, text: str) -> LanguageDetectionResult:
        """Detect the language of the input text"""
        if not text or not text.strip():
            return LanguageDetectionResult(
                detected_language=LanguageCode.UNKNOWN,
                confidence=0.0,
                detected_text=text,
                language_name="Unknown"
            )
        
        text_lower = text.lower()
        scores = {}
        
        # Calculate scores for each supported language
        for lang_code, lang_info in self.language_patterns.items():
            if lang_code not in self.config["supported_languages"]:
                continue
            
            score = 0
            total_patterns = len(lang_info["patterns"])
            
            for pattern in lang_info["patterns"]:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                if matches > 0:
                    score += matches
            
            if total_patterns > 0:
                scores[lang_code] = score / total_patterns
        
        # Find the language with highest score
        if scores:
            best_language = max(scores, key=scores.get)
            confidence = min(1.0, scores[best_language] / 10.0)  # Normalize confidence
            
            return LanguageDetectionResult(
                detected_language=best_language,
                confidence=confidence,
                detected_text=text,
                language_name=self.language_patterns[best_language]["name"],
                script=self.language_patterns[best_language]["script"]
            )
        else:
            return LanguageDetectionResult(
                detected_language=LanguageCode.UNKNOWN,
                confidence=0.0,
                detected_text=text,
                language_name="Unknown"
            )
    
    def translate_text(self, text: str, target_language: LanguageCode,
                      source_language: LanguageCode = None) -> TranslationResult:
        """Translate text to target language"""
        if not text or not text.strip():
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_language or LanguageCode.UNKNOWN,
                target_language=target_language,
                confidence=0.0,
                provider=self.config["translation_provider"]
            )
        
        # Check cache first
        cache_key = self._generate_cache_key(text, target_language, source_language)
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        # Auto-detect source language if not provided
        if not source_language:
            detection_result = self.detect_language(text)
            source_language = detection_result.detected_language
        
        # Skip translation if source and target are the same
        if source_language == target_language:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                confidence=1.0,
                provider=self.config["translation_provider"]
            )
        
        # Perform translation based on provider
        translated_text, confidence = self._perform_translation(
            text, source_language, target_language
        )
        
        result = TranslationResult(
            original_text=text,
            translated_text=translated_text,
            source_language=source_language,
            target_language=target_language,
            confidence=confidence,
            provider=self.config["translation_provider"]
        )
        
        # Cache the result
        self.translation_cache[cache_key] = result
        self.cache_timestamps[cache_key] = self._get_current_timestamp()
        
        return result
    
    def _perform_translation(self, text: str, source_lang: LanguageCode,
                           target_lang: LanguageCode) -> Tuple[str, float]:
        """Perform actual translation using configured provider"""
        # For now, implement a simple rule-based translation
        # In production, this would integrate with actual translation APIs
        
        if self.config["translation_provider"] == TranslationProvider.GOOGLE_TRANSLATE:
            return self._google_translate_simulation(text, source_lang, target_lang)
        elif self.config["translation_provider"] == TranslationProvider.DEEPL:
            return self._deepl_translate_simulation(text, source_lang, target_lang)
        else:
            return self._fallback_translation(text, source_lang, target_lang)
    
    def _google_translate_simulation(self, text: str, source_lang: LanguageCode,
                                   target_lang: LanguageCode) -> Tuple[str, float]:
        """Simulate Google Translate (placeholder for actual API integration)"""
        # Simple translation examples for demonstration
        translations = {
            (LanguageCode.SPANISH, LanguageCode.ENGLISH): {
                "hola": "hello",
                "gracias": "thank you",
                "por favor": "please"
            },
            (LanguageCode.FRENCH, LanguageCode.ENGLISH): {
                "bonjour": "hello",
                "merci": "thank you",
                "s'il vous plaît": "please"
            },
            (LanguageCode.GERMAN, LanguageCode.ENGLISH): {
                "hallo": "hello",
                "danke": "thank you",
                "bitte": "please"
            }
        }
        
        key = (source_lang, target_lang)
        if key in translations:
            translated = text
            for src, tgt in translations[key].items():
                translated = translated.replace(src, tgt)
            return translated, 0.8
        else:
            return text, 0.5  # Fallback
    
    def _deepl_translate_simulation(self, text: str, source_lang: LanguageCode,
                                   target_lang: LanguageCode) -> Tuple[str, float]:
        """Simulate DeepL translation (placeholder for actual API integration)"""
        # Similar to Google Translate simulation but with different confidence
        return self._google_translate_simulation(text, source_lang, target_lang)
    
    def _fallback_translation(self, text: str, source_lang: LanguageCode,
                            target_lang: LanguageCode) -> Tuple[str, float]:
        """Fallback translation method"""
        return text, 0.3
    
    def _generate_cache_key(self, text: str, target_lang: LanguageCode,
                           source_lang: LanguageCode = None) -> str:
        """Generate cache key for translation"""
        key_parts = [
            hashlib.md5(text.encode()).hexdigest(),
            target_lang.value,
            source_lang.value if source_lang else "auto"
        ]
        return "_".join(key_parts)
    
    def _get_current_timestamp(self) -> float:
        """Get current timestamp"""
        import time
        return time.time()
    
    def process_multi_language_query(self, query: str, 
                                   target_languages: List[LanguageCode] = None) -> MultiLanguageQuery:
        """Process a query in multiple languages"""
        start_time = self._get_current_timestamp()
        
        # Detect language
        detection_result = self.detect_language(query)
        
        # Determine target languages
        if not target_languages:
            target_languages = [self.config["default_language"]]
        
        # Translate to target languages
        translated_queries = {}
        for target_lang in target_languages:
            if target_lang != detection_result.detected_language:
                translation_result = self.translate_text(
                    query, target_lang, detection_result.detected_language
                )
                translated_queries[target_lang] = translation_result.translated_text
            else:
                translated_queries[target_lang] = query
        
        processing_time = self._get_current_timestamp() - start_time
        
        return MultiLanguageQuery(
            original_query=query,
            detected_language=detection_result.detected_language,
            translated_queries=translated_queries,
            confidence=detection_result.confidence,
            processing_time=processing_time,
            metadata={
                "detection_confidence": detection_result.confidence,
                "script": detection_result.script,
                "language_name": detection_result.language_name
            }
        )
    
    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Get list of supported languages"""
        languages = []
        for lang_code in self.config["supported_languages"]:
            if lang_code in self.language_patterns:
                lang_info = self.language_patterns[lang_code]
                languages.append({
                    "code": lang_code.value,
                    "name": lang_info["name"],
                    "script": lang_info["script"],
                    "supported": True
                })
        
        return languages
    
    def clear_translation_cache(self):
        """Clear translation cache"""
        self.translation_cache.clear()
        self.cache_timestamps.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get translation cache statistics"""
        return {
            "cache_size": len(self.translation_cache),
            "cache_entries": list(self.translation_cache.keys()),
            "oldest_entry": min(self.cache_timestamps.values()) if self.cache_timestamps else None,
            "newest_entry": max(self.cache_timestamps.values()) if self.cache_timestamps else None
        }


# Global language processor instance
language_processor = LanguageProcessor()
