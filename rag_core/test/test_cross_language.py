"""
Test suite for Cross-Language Query Support System
Tests language detection, translation, and multi-language processing capabilities
"""

import pytest
import json
from typing import List, Dict, Any

from rag_core.language_processor import (
    LanguageProcessor, LanguageCode, TranslationProvider,
    LanguageDetectionResult, TranslationResult, MultiLanguageQuery
)
from rag_core.llm import LLMHandler


class TestLanguageProcessor:
    """Test the language processor system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = LanguageProcessor()
    
    def test_initialization(self):
        """Test LanguageProcessor initialization"""
        assert self.processor is not None
        assert hasattr(self.processor, 'config')
        assert hasattr(self.processor, 'language_patterns')
        assert hasattr(self.processor, 'translation_cache')
    
    def test_detect_language_english(self):
        """Test language detection for English"""
        text = "This is an English text with some common words like the, and, or, but."
        
        result = self.processor.detect_language(text)
        
        assert isinstance(result, LanguageDetectionResult)
        assert result.detected_language == LanguageCode.ENGLISH
        assert result.language_name == "English"
        assert result.script == "Latin"
        assert 0 <= result.confidence <= 1
    
    def test_detect_language_spanish(self):
        """Test language detection for Spanish"""
        text = "Hola, esto es un texto en español con palabras como el, la, los, las, de, del."
        
        result = self.processor.detect_language(text)
        
        assert isinstance(result, LanguageDetectionResult)
        assert result.detected_language == LanguageCode.SPANISH
        assert result.language_name == "Spanish"
        assert result.script == "Latin"
        assert 0 <= result.confidence <= 1
    
    def test_detect_language_french(self):
        """Test language detection for French"""
        text = "Bonjour, ceci est un texte en français avec des mots comme le, la, les, de, du, des."
        
        result = self.processor.detect_language(text)
        
        assert isinstance(result, LanguageDetectionResult)
        assert result.detected_language == LanguageCode.FRENCH
        assert result.language_name == "French"
        assert result.script == "Latin"
        assert 0 <= result.confidence <= 1
    
    def test_detect_language_german(self):
        """Test language detection for German"""
        text = "Hallo, das ist ein deutscher Text mit Wörtern wie der, die, das, ein, eine."
        
        result = self.processor.detect_language(text)
        
        assert isinstance(result, LanguageDetectionResult)
        assert result.detected_language == LanguageCode.GERMAN
        assert result.language_name == "German"
        assert result.script == "Latin"
        assert 0 <= result.confidence <= 1
    
    def test_detect_language_russian(self):
        """Test language detection for Russian"""
        text = "Привет, это русский текст с словами как и, в, на, с, по, для."
        
        result = self.processor.detect_language(text)
        
        assert isinstance(result, LanguageDetectionResult)
        assert result.detected_language == LanguageCode.RUSSIAN
        assert result.language_name == "Russian"
        assert result.script == "Cyrillic"
        assert 0 <= result.confidence <= 1
    
    def test_detect_language_chinese(self):
        """Test language detection for Chinese"""
        text = "你好，这是中文文本，包含的、是、在、有、和等词汇。"
        
        result = self.processor.detect_language(text)
        
        assert isinstance(result, LanguageDetectionResult)
        assert result.detected_language == LanguageCode.CHINESE_SIMPLIFIED
        assert result.language_name == "Chinese (Simplified)"
        assert result.script == "Han"
        assert 0 <= result.confidence <= 1
    
    def test_detect_language_japanese(self):
        """Test language detection for Japanese"""
        text = "こんにちは、これは日本語のテキストです。は、が、を、に、へ、で、となどの助詞があります。"
        
        result = self.processor.detect_language(text)
        
        assert isinstance(result, LanguageDetectionResult)
        assert result.detected_language == LanguageCode.JAPANESE
        assert result.language_name == "Japanese"
        assert result.script == "Mixed"
        assert 0 <= result.confidence <= 1
    
    def test_detect_language_korean(self):
        """Test language detection for Korean"""
        text = "안녕하세요, 이것은 한국어 텍스트입니다. 은, 는, 이, 가, 을, 를 등의 조사가 있습니다."
        
        result = self.processor.detect_language(text)
        
        assert isinstance(result, LanguageDetectionResult)
        assert result.detected_language == LanguageCode.KOREAN
        assert result.language_name == "Korean"
        assert result.script == "Hangul"
        assert 0 <= result.confidence <= 1
    
    def test_detect_language_arabic(self):
        """Test language detection for Arabic"""
        text = "مرحبا، هذا نص باللغة العربية مع كلمات مثل في، من، إلى، على، عن، مع."
        
        result = self.processor.detect_language(text)
        
        assert isinstance(result, LanguageDetectionResult)
        assert result.detected_language == LanguageCode.ARABIC
        assert result.language_name == "Arabic"
        assert result.script == "Arabic"
        assert 0 <= result.confidence <= 1
    
    def test_detect_language_empty_text(self):
        """Test language detection with empty text"""
        result = self.processor.detect_language("")
        
        assert isinstance(result, LanguageDetectionResult)
        assert result.detected_language == LanguageCode.UNKNOWN
        assert result.confidence == 0.0
        assert result.language_name == "Unknown"
    
    def test_detect_language_unknown(self):
        """Test language detection with unknown language"""
        text = "1234567890 !@#$%^&*()"
        
        result = self.processor.detect_language(text)
        
        assert isinstance(result, LanguageDetectionResult)
        assert result.detected_language == LanguageCode.UNKNOWN
        assert result.confidence == 0.0
    
    def test_translate_text_spanish_to_english(self):
        """Test translation from Spanish to English"""
        text = "Hola, gracias por tu ayuda."
        
        result = self.processor.translate_text(
            text=text,
            target_language=LanguageCode.ENGLISH,
            source_language=LanguageCode.SPANISH
        )
        
        assert isinstance(result, TranslationResult)
        assert result.original_text == text
        assert result.source_language == LanguageCode.SPANISH
        assert result.target_language == LanguageCode.ENGLISH
        assert result.provider == self.processor.config["translation_provider"]
        assert 0 <= result.confidence <= 1
    
    def test_translate_text_french_to_english(self):
        """Test translation from French to English"""
        text = "Bonjour, merci pour votre aide."
        
        result = self.processor.translate_text(
            text=text,
            target_language=LanguageCode.ENGLISH,
            source_language=LanguageCode.FRENCH
        )
        
        assert isinstance(result, TranslationResult)
        assert result.original_text == text
        assert result.source_language == LanguageCode.FRENCH
        assert result.target_language == LanguageCode.ENGLISH
        assert 0 <= result.confidence <= 1
    
    def test_translate_text_german_to_english(self):
        """Test translation from German to English"""
        text = "Hallo, danke für Ihre Hilfe."
        
        result = self.processor.translate_text(
            text=text,
            target_language=LanguageCode.ENGLISH,
            source_language=LanguageCode.GERMAN
        )
        
        assert isinstance(result, TranslationResult)
        assert result.original_text == text
        assert result.source_language == LanguageCode.GERMAN
        assert result.target_language == LanguageCode.ENGLISH
        assert 0 <= result.confidence <= 1
    
    def test_translate_text_same_language(self):
        """Test translation when source and target are the same"""
        text = "Hello, thank you for your help."
        
        result = self.processor.translate_text(
            text=text,
            target_language=LanguageCode.ENGLISH,
            source_language=LanguageCode.ENGLISH
        )
        
        assert isinstance(result, TranslationResult)
        assert result.original_text == text
        assert result.translated_text == text
        assert result.confidence == 1.0
    
    def test_translate_text_auto_detect(self):
        """Test translation with automatic language detection"""
        text = "Hola, gracias por tu ayuda."
        
        result = self.processor.translate_text(
            text=text,
            target_language=LanguageCode.ENGLISH
        )
        
        assert isinstance(result, TranslationResult)
        assert result.original_text == text
        assert result.target_language == LanguageCode.ENGLISH
        assert 0 <= result.confidence <= 1
    
    def test_translate_text_empty(self):
        """Test translation with empty text"""
        result = self.processor.translate_text(
            text="",
            target_language=LanguageCode.ENGLISH
        )
        
        assert isinstance(result, TranslationResult)
        assert result.original_text == ""
        assert result.translated_text == ""
        assert result.confidence == 0.0
    
    def test_process_multi_language_query(self):
        """Test processing multi-language query"""
        query = "Hola, ¿cómo estás?"
        target_languages = [LanguageCode.ENGLISH, LanguageCode.FRENCH]
        
        result = self.processor.process_multi_language_query(query, target_languages)
        
        assert isinstance(result, MultiLanguageQuery)
        assert result.original_query == query
        assert result.detected_language == LanguageCode.SPANISH
        assert 0 <= result.confidence <= 1
        assert result.processing_time > 0
        assert len(result.translated_queries) > 0
        assert LanguageCode.ENGLISH in result.translated_queries
        assert LanguageCode.FRENCH in result.translated_queries
    
    def test_process_multi_language_query_english(self):
        """Test processing multi-language query with English input"""
        query = "Hello, how are you?"
        target_languages = [LanguageCode.SPANISH, LanguageCode.FRENCH]
        
        result = self.processor.process_multi_language_query(query, target_languages)
        
        assert isinstance(result, MultiLanguageQuery)
        assert result.original_query == query
        assert result.detected_language == LanguageCode.ENGLISH
        assert len(result.translated_queries) > 0
        assert LanguageCode.SPANISH in result.translated_queries
        assert LanguageCode.FRENCH in result.translated_queries
    
    def test_get_supported_languages(self):
        """Test getting supported languages"""
        languages = self.processor.get_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) > 0
        
        # Check language structure
        for lang in languages:
            assert "code" in lang
            assert "name" in lang
            assert "script" in lang
            assert "supported" in lang
            assert lang["supported"] is True
    
    def test_translation_cache(self):
        """Test translation cache functionality"""
        text = "Hola, gracias."
        
        # First translation
        result1 = self.processor.translate_text(
            text=text,
            target_language=LanguageCode.ENGLISH,
            source_language=LanguageCode.SPANISH
        )
        
        # Second translation (should use cache)
        result2 = self.processor.translate_text(
            text=text,
            target_language=LanguageCode.ENGLISH,
            source_language=LanguageCode.SPANISH
        )
        
        assert result1.translated_text == result2.translated_text
        assert result1.confidence == result2.confidence
    
    def test_clear_translation_cache(self):
        """Test clearing translation cache"""
        # Add some translations to cache
        self.processor.translate_text(
            text="Hola",
            target_language=LanguageCode.ENGLISH,
            source_language=LanguageCode.SPANISH
        )
        
        initial_cache_size = len(self.processor.translation_cache)
        assert initial_cache_size > 0
        
        # Clear cache
        self.processor.clear_translation_cache()
        
        assert len(self.processor.translation_cache) == 0
        assert len(self.processor.cache_timestamps) == 0
    
    def test_get_cache_stats(self):
        """Test getting cache statistics"""
        # Add some translations to cache
        self.processor.translate_text(
            text="Hola",
            target_language=LanguageCode.ENGLISH,
            source_language=LanguageCode.SPANISH
        )
        
        stats = self.processor.get_cache_stats()
        
        assert isinstance(stats, dict)
        assert "cache_size" in stats
        assert "cache_entries" in stats
        assert "oldest_entry" in stats
        assert "newest_entry" in stats
        assert stats["cache_size"] > 0


class TestLLMCrossLanguage:
    """Test LLM cross-language integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.llm_handler = LLMHandler()
    
    def test_generate_response_english(self):
        """Test generating response in English"""
        prompt = "What is machine learning?"
        context = "Machine learning is a subset of artificial intelligence."
        
        response = self.llm_handler.generate_response(
            prompt=prompt,
            context=context,
            target_language=LanguageCode.ENGLISH
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_generate_response_spanish(self):
        """Test generating response in Spanish"""
        prompt = "¿Qué es el aprendizaje automático?"
        context = "El aprendizaje automático es un subconjunto de la inteligencia artificial."
        
        response = self.llm_handler.generate_response(
            prompt=prompt,
            context=context,
            target_language=LanguageCode.SPANISH
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_process_multi_language_query(self):
        """Test processing multi-language query with LLM"""
        query = "What is artificial intelligence?"
        target_languages = [LanguageCode.ENGLISH, LanguageCode.SPANISH]
        
        result = self.llm_handler.process_multi_language_query(query, target_languages)
        
        assert isinstance(result, dict)
        assert "original_query" in result
        assert "detected_language" in result
        assert "detection_confidence" in result
        assert "processing_time" in result
        assert "responses" in result
        assert "metadata" in result
        
        assert result["original_query"] == query
        assert result["detected_language"] == LanguageCode.ENGLISH.value
        assert 0 <= result["detection_confidence"] <= 1
        assert result["processing_time"] > 0
        
        responses = result["responses"]
        assert LanguageCode.ENGLISH.value in responses
        assert LanguageCode.SPANISH.value in responses
        
        for lang_code, response_data in responses.items():
            assert "query" in response_data
            assert "response" in response_data
            assert "language" in response_data
            assert "confidence" in response_data
            assert response_data["language"] == lang_code


class TestLanguageEnums:
    """Test language enums"""
    
    def test_language_code_enum(self):
        """Test LanguageCode enum"""
        assert LanguageCode.ENGLISH.value == "en"
        assert LanguageCode.SPANISH.value == "es"
        assert LanguageCode.FRENCH.value == "fr"
        assert LanguageCode.GERMAN.value == "de"
        assert LanguageCode.ITALIAN.value == "it"
        assert LanguageCode.PORTUGUESE.value == "pt"
        assert LanguageCode.RUSSIAN.value == "ru"
        assert LanguageCode.CHINESE_SIMPLIFIED.value == "zh-CN"
        assert LanguageCode.JAPANESE.value == "ja"
        assert LanguageCode.KOREAN.value == "ko"
        assert LanguageCode.ARABIC.value == "ar"
        assert LanguageCode.UNKNOWN.value == "unknown"
    
    def test_translation_provider_enum(self):
        """Test TranslationProvider enum"""
        assert TranslationProvider.GOOGLE_TRANSLATE.value == "google_translate"
        assert TranslationProvider.DEEPL.value == "deepl"
        assert TranslationProvider.AZURE_TRANSLATOR.value == "azure_translator"
        assert TranslationProvider.AWS_TRANSLATE.value == "aws_translate"
        assert TranslationProvider.LIBRE_TRANSLATE.value == "libre_translate"
        assert TranslationProvider.CUSTOM.value == "custom"


class TestLanguageDataStructures:
    """Test language data structures"""
    
    def test_language_detection_result(self):
        """Test LanguageDetectionResult dataclass"""
        result = LanguageDetectionResult(
            detected_language=LanguageCode.ENGLISH,
            confidence=0.95,
            detected_text="Hello world",
            language_name="English",
            script="Latin",
            metadata={"test": "value"}
        )
        
        assert result.detected_language == LanguageCode.ENGLISH
        assert result.confidence == 0.95
        assert result.detected_text == "Hello world"
        assert result.language_name == "English"
        assert result.script == "Latin"
        assert result.metadata["test"] == "value"
    
    def test_translation_result(self):
        """Test TranslationResult dataclass"""
        result = TranslationResult(
            original_text="Hola",
            translated_text="Hello",
            source_language=LanguageCode.SPANISH,
            target_language=LanguageCode.ENGLISH,
            confidence=0.8,
            provider=TranslationProvider.GOOGLE_TRANSLATE,
            metadata={"test": "value"}
        )
        
        assert result.original_text == "Hola"
        assert result.translated_text == "Hello"
        assert result.source_language == LanguageCode.SPANISH
        assert result.target_language == LanguageCode.ENGLISH
        assert result.confidence == 0.8
        assert result.provider == TranslationProvider.GOOGLE_TRANSLATE
        assert result.metadata["test"] == "value"
    
    def test_multi_language_query(self):
        """Test MultiLanguageQuery dataclass"""
        translated_queries = {
            LanguageCode.ENGLISH: "Hello",
            LanguageCode.SPANISH: "Hola"
        }
        
        result = MultiLanguageQuery(
            original_query="Hola",
            detected_language=LanguageCode.SPANISH,
            translated_queries=translated_queries,
            confidence=0.9,
            processing_time=0.5,
            metadata={"test": "value"}
        )
        
        assert result.original_query == "Hola"
        assert result.detected_language == LanguageCode.SPANISH
        assert result.translated_queries == translated_queries
        assert result.confidence == 0.9
        assert result.processing_time == 0.5
        assert result.metadata["test"] == "value"


def test_cross_language_imports():
    """Test that all cross-language components can be imported"""
    from rag_core.language_processor import (
        LanguageProcessor, LanguageCode, TranslationProvider,
        LanguageDetectionResult, TranslationResult, MultiLanguageQuery,
        language_processor
    )
    
    assert LanguageProcessor is not None
    assert LanguageCode is not None
    assert TranslationProvider is not None
    assert LanguageDetectionResult is not None
    assert TranslationResult is not None
    assert MultiLanguageQuery is not None
    assert language_processor is not None


def test_cross_language_integration():
    """Test integration with LLM system"""
    from rag_core.language_processor import language_processor, LanguageCode
    from rag_core.llm import LLMHandler
    
    # Test language detection
    detection_result = language_processor.detect_language("Hello world")
    assert detection_result.detected_language == LanguageCode.ENGLISH
    
    # Test translation
    translation_result = language_processor.translate_text(
        "Hola", LanguageCode.ENGLISH, LanguageCode.SPANISH
    )
    assert isinstance(translation_result, TranslationResult)
    
    # Test LLM integration
    llm_handler = LLMHandler()
    response = llm_handler.generate_response(
        "What is AI?",
        context="Artificial Intelligence is a field of computer science.",
        target_language=LanguageCode.ENGLISH
    )
    assert isinstance(response, str)
    assert len(response) > 0
