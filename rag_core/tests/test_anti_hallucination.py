"""
Test Enhanced Anti-Hallucination System

Tests for the enhanced anti-hallucination functionality with comprehensive
validation, fact checking, and contradiction detection.
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import Dict, Any, List

# Import the modules to test
from rag_core.anti_hallucination import (
    AntiHallucinationValidator, ContextValidator, ValidationResult,
    HallucinationDetection, HallucinationType, ConfidenceLevel
)

class TestAntiHallucinationValidator:
    """Test the AntiHallucinationValidator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            "min_confidence": 0.6,
            "min_relevance": 0.3,
            "fact_checking_enabled": True,
            "contradiction_detection_enabled": True,
            "temporal_validation_enabled": True,
            "numerical_validation_enabled": True
        }
        self.validator = AntiHallucinationValidator(self.config)
    
    def test_initialization(self):
        """Test AntiHallucinationValidator initialization"""
        assert self.validator is not None
        assert self.validator.min_confidence == 0.6
        assert self.validator.min_relevance == 0.3
        assert self.validator.fact_checking_enabled == True
        assert self.validator.contradiction_detection_enabled == True
    
    def test_validate_chunks_basic(self):
        """Test basic chunk validation"""
        query = "What is machine learning?"
        chunks = [
            {
                "content": "Machine learning is a subset of artificial intelligence.",
                "source": {"confidence": 0.8},
                "metadata": {"filename": "test.pdf"}
            },
            {
                "content": "Machine learning algorithms can learn from data.",
                "source": {"confidence": 0.9},
                "metadata": {"filename": "test.pdf"}
            }
        ]
        
        validated_chunks = self.validator.validate_chunks(query, chunks)
        
        assert len(validated_chunks) == 2
        assert "validation" in validated_chunks[0]
        assert validated_chunks[0]["validation"]["quality_passed"] == True
    
    def test_validate_chunks_low_confidence(self):
        """Test chunk validation with low confidence"""
        query = "What is machine learning?"
        chunks = [
            {
                "content": "Machine learning is a subset of artificial intelligence.",
                "source": {"confidence": 0.3},  # Below threshold
                "metadata": {"filename": "test.pdf"}
            }
        ]
        
        validated_chunks = self.validator.validate_chunks(query, chunks)
        
        assert len(validated_chunks) == 0  # Should be filtered out
    
    def test_validate_response_factual_error(self):
        """Test response validation with factual error"""
        query = "What is machine learning?"
        response = "Machine learning was invented in 2020 by John Smith."
        sources = [
            {
                "content": "Machine learning has been around since the 1950s.",
                "filename": "history.pdf"
            }
        ]
        
        validation_result = self.validator.validate_response(query, response, sources)
        
        assert validation_result.is_valid == False
        assert len(validation_result.hallucination_detections) > 0
        assert any(d.hallucination_type == HallucinationType.FACTUAL_ERROR 
                  for d in validation_result.hallucination_detections)
    
    def test_validate_response_contradiction(self):
        """Test response validation with contradiction"""
        query = "What is the population of New York?"
        response = "New York has 8 million people. However, New York has 20 million people."
        sources = [
            {
                "content": "New York City has approximately 8.4 million residents.",
                "filename": "demographics.pdf"
            }
        ]
        
        validation_result = self.validator.validate_response(query, response, sources)
        
        assert validation_result.is_valid == False
        assert len(validation_result.hallucination_detections) > 0
        assert any(d.hallucination_type == HallucinationType.CONTRADICTION 
                  for d in validation_result.hallucination_detections)
    
    def test_validate_response_temporal_error(self):
        """Test response validation with temporal error"""
        query = "When was the iPhone released?"
        response = "The iPhone was released in 2010."
        sources = [
            {
                "content": "The iPhone was first released in 2007.",
                "filename": "apple_history.pdf"
            }
        ]
        
        validation_result = self.validator.validate_response(query, response, sources)
        
        assert validation_result.is_valid == False
        assert len(validation_result.hallucination_detections) > 0
        assert any(d.hallucination_type == HallucinationType.TEMPORAL_ERROR 
                  for d in validation_result.hallucination_detections)
    
    def test_validate_response_numerical_error(self):
        """Test response validation with numerical error"""
        query = "What is the GDP of the United States?"
        response = "The GDP of the United States is $50 trillion."
        sources = [
            {
                "content": "The GDP of the United States is approximately $21 trillion.",
                "filename": "economics.pdf"
            }
        ]
        
        validation_result = self.validator.validate_response(query, response, sources)
        
        assert validation_result.is_valid == False
        assert len(validation_result.hallucination_detections) > 0
        assert any(d.hallucination_type == HallucinationType.NUMERICAL_ERROR 
                  for d in validation_result.hallucination_detections)
    
    def test_validate_response_valid(self):
        """Test response validation with valid response"""
        query = "What is machine learning?"
        response = "Machine learning is a subset of artificial intelligence that enables computers to learn from data."
        sources = [
            {
                "content": "Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
                "filename": "ai_basics.pdf"
            }
        ]
        
        validation_result = self.validator.validate_response(query, response, sources)
        
        assert validation_result.is_valid == True
        assert validation_result.confidence_level == ConfidenceLevel.HIGH
        assert validation_result.quality_score >= 0.9
    
    def test_extract_facts(self):
        """Test fact extraction from text"""
        text = "Machine learning is a subset of AI. It was developed in the 1950s. The algorithm shows promising results."
        
        facts = self.validator._extract_facts(text)
        
        assert len(facts) > 0
        assert any("machine learning" in fact.lower() for fact in facts)
        assert any("developed" in fact.lower() for fact in facts)
    
    def test_find_internal_contradictions(self):
        """Test internal contradiction detection"""
        text = "The sky is blue. However, the sky is red."
        
        contradictions = self.validator._find_internal_contradictions(text)
        
        assert len(contradictions) > 0
        assert "however" in contradictions[0].lower()
    
    def test_extract_temporal_info(self):
        """Test temporal information extraction"""
        text = "The event happened in 2020. It was before the pandemic. The results were published in 2021."
        
        temporal_info = self.validator._extract_temporal_info(text)
        
        assert len(temporal_info) > 0
        assert "2020" in temporal_info
        assert "2021" in temporal_info
        assert "before" in temporal_info
    
    def test_extract_numerical_info(self):
        """Test numerical information extraction"""
        text = "The population is 8.4 million. The growth rate is 2.5%. The cost is $1.2 billion."
        
        numerical_info = self.validator._extract_numerical_info(text)
        
        assert len(numerical_info) > 0
        assert "8.4" in numerical_info
        assert "2.5%" in numerical_info
        assert "$1.2" in numerical_info
    
    def test_calculate_quality_score(self):
        """Test quality score calculation"""
        response = "Test response"
        sources = [{"content": "Test source"}]
        detections = [
            HallucinationDetection(severity="high"),
            HallucinationDetection(severity="medium")
        ]
        
        quality_score = self.validator._calculate_quality_score(response, sources, detections)
        
        assert 0.0 <= quality_score <= 1.0
        assert quality_score < 1.0  # Should be penalized by detections
    
    def test_determine_confidence_level(self):
        """Test confidence level determination"""
        # Test high confidence
        confidence = self.validator._determine_confidence_level(0.95)
        assert confidence == ConfidenceLevel.HIGH
        
        # Test medium confidence
        confidence = self.validator._determine_confidence_level(0.75)
        assert confidence == ConfidenceLevel.MEDIUM
        
        # Test low confidence
        confidence = self.validator._determine_confidence_level(0.55)
        assert confidence == ConfidenceLevel.LOW
        
        # Test rejected
        confidence = self.validator._determine_confidence_level(0.3)
        assert confidence == ConfidenceLevel.REJECTED

class TestContextValidator:
    """Test the ContextValidator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = ContextValidator()
    
    def test_initialization(self):
        """Test ContextValidator initialization"""
        assert self.validator is not None
        assert self.validator.validator is not None
    
    def test_create_safe_context(self):
        """Test safe context creation"""
        query = "What is machine learning?"
        chunks = [
            {
                "content": "Machine learning is a subset of artificial intelligence.",
                "metadata": {"filename": "test.pdf"},
                "source": {"confidence": 0.8}  # Add confidence to pass validation
            }
        ]
    
        context, metadata = self.validator.create_safe_context(query, chunks)
    
        assert "DOCUMENT CONTEXT" in context
        assert "RELEVANT INFORMATION" in context
        assert "Machine learning" in context
        assert metadata["sources_used"] == 1
        assert metadata["validation_passed"] == True
    
    def test_create_safe_context_no_valid_chunks(self):
        """Test safe context creation with no valid chunks"""
        query = "What is machine learning?"
        chunks = []  # Empty chunks
        
        context, metadata = self.validator.create_safe_context(query, chunks)
        
        assert "NO RELEVANT CONTEXT FOUND" in context
        assert metadata["sources_used"] == 0

def test_anti_hallucination_imports():
    """Test that all anti-hallucination modules can be imported"""
    try:
        from rag_core.anti_hallucination import (
            AntiHallucinationValidator, ContextValidator, ValidationResult,
            HallucinationDetection, HallucinationType, ConfidenceLevel
        )
        assert True  # If we get here, imports worked
    except ImportError as e:
        pytest.fail(f"Failed to import anti-hallucination modules: {e}")

def test_hallucination_type_enum():
    """Test HallucinationType enum values"""
    from rag_core.anti_hallucination import HallucinationType
    
    assert HallucinationType.FACTUAL_ERROR.value == "factual_error"
    assert HallucinationType.SOURCE_MISATTRIBUTION.value == "source_misattribution"
    assert HallucinationType.CONTRADICTION.value == "contradiction"
    assert HallucinationType.SPECULATION.value == "speculation"
    assert HallucinationType.OUT_OF_SCOPE.value == "out_of_scope"
    assert HallucinationType.TEMPORAL_ERROR.value == "temporal_error"
    assert HallucinationType.NUMERICAL_ERROR.value == "numerical_error"

def test_confidence_level_enum():
    """Test ConfidenceLevel enum values"""
    from rag_core.anti_hallucination import ConfidenceLevel
    
    assert ConfidenceLevel.HIGH.value == "high"
    assert ConfidenceLevel.MEDIUM.value == "medium"
    assert ConfidenceLevel.LOW.value == "low"
    assert ConfidenceLevel.REJECTED.value == "rejected"

def test_anti_hallucination_configuration():
    """Test anti-hallucination configuration"""
    from rag_core.anti_hallucination import AntiHallucinationValidator
    
    # Test default configuration
    validator = AntiHallucinationValidator()
    config = validator.config
    
    # Verify required configuration sections
    assert 'min_confidence' in config
    assert 'min_relevance' in config
    assert 'fact_checking_enabled' in config
    assert 'contradiction_detection_enabled' in config
    assert 'temporal_validation_enabled' in config
    assert 'numerical_validation_enabled' in config
    assert 'fact_patterns' in config
    
    # Verify configuration values
    assert config['min_confidence'] == 0.7
    assert config['min_relevance'] == 0.4
    assert config['fact_checking_enabled'] == True
    assert config['contradiction_detection_enabled'] == True

if __name__ == "__main__":
    # Run basic tests
    test_anti_hallucination_imports()
    test_hallucination_type_enum()
    test_confidence_level_enum()
    test_anti_hallucination_configuration()
    print("Anti-hallucination tests completed successfully!")
