"""
Utility functions for XOR RAG system including query classification, domain detection, and hybrid search.
"""

import re
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple
from rag_core.config import logger, OLLAMA_BASE_URL, OLLAMA_LLM_MODEL
from rag_core.redis_cache import redis_get, redis_set
import ollama
from tenacity import retry, stop_after_attempt, wait_exponential

class QueryClassifier:
    """Classifies queries by domain and topic for intelligent routing."""
    
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def classify_query(query: str) -> Dict[str, Any]:
        """
        Classify a query by domain and topic using LLaMA 3.2:3B.
        
        Args:
            query: User query to classify
            
        Returns:
            Dictionary with domain, topic, confidence, and keywords
        """
        # Check cache first
        cache_key = f"query_classification:{hashlib.sha256(query.encode()).hexdigest()}"
        cached = redis_get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
        
        try:
            # Classification prompt
            classification_prompt = f"""
            Classify the domain and topic of this query: "{query}"
            
            Return a JSON object with:
            - domain: The main domain (e.g., "law", "physics", "chemistry", "religion", "medicine", "finance", "engineering", "education", "government", "technology")
            - topic: Specific topic within the domain
            - confidence: Confidence score (0.0 to 1.0)
            - keywords: List of relevant keywords for search
            
            Examples:
            - "Section 304" → {{"domain": "law", "topic": "penal code", "confidence": 0.95, "keywords": ["section", "304", "penal", "code"]}}
            - "electronegativity of chlorine" → {{"domain": "chemistry", "topic": "periodic table", "confidence": 0.9, "keywords": ["electronegativity", "chlorine", "chemistry"]}}
            - "prayer times" → {{"domain": "religion", "topic": "islamic practices", "confidence": 0.85, "keywords": ["prayer", "times", "religion"]}}
            
            Response (JSON only):
            """
            
            response = ollama.chat(
                model=OLLAMA_LLM_MODEL,
                messages=[{"role": "user", "content": classification_prompt}],
                options={"base_url": OLLAMA_BASE_URL}
            )
            
            # Extract JSON from response
            response_text = response['message']['content']
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                # Cache the result
                redis_set(cache_key, json.dumps(result), expire=3600)  # 1 hour cache
                logger.info(f"Query classification: {query[:50]}... → {result.get('domain', 'unknown')}")
                return result
            else:
                # Fallback classification
                fallback = QueryClassifier._fallback_classification(query)
                redis_set(cache_key, json.dumps(fallback), expire=3600)
                return fallback
                
        except Exception as e:
            logger.error(f"Query classification failed: {str(e)}")
            fallback = QueryClassifier._fallback_classification(query)
            redis_set(cache_key, json.dumps(fallback), expire=3600)
            return fallback
    
    @staticmethod
    def _fallback_classification(query: str) -> Dict[str, Any]:
        """Fallback classification using keyword matching."""
        query_lower = query.lower()
        
        # Domain keywords
        domain_keywords = {
            "law": ["section", "penal", "code", "law", "legal", "court", "judge", "crime", "punishment"],
            "chemistry": ["electronegativity", "molecule", "atom", "chemical", "reaction", "element", "compound"],
            "physics": ["force", "energy", "velocity", "acceleration", "mass", "gravity", "motion"],
            "religion": ["prayer", "worship", "god", "religious", "faith", "spiritual", "ritual"],
            "medicine": ["disease", "symptom", "treatment", "medicine", "patient", "diagnosis", "health"],
            "finance": ["money", "investment", "bank", "financial", "economy", "currency", "profit"],
            "engineering": ["design", "construction", "technical", "engineering", "system", "structure"],
            "education": ["student", "teacher", "school", "education", "learning", "course", "study"],
            "government": ["policy", "government", "official", "administration", "public", "service"],
            "technology": ["software", "computer", "technology", "digital", "programming", "system"]
        }
        
        # Find best matching domain
        best_domain = "general"
        best_score = 0
        
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > best_score:
                best_score = score
                best_domain = domain
        
        return {
            "domain": best_domain,
            "topic": "general",
            "confidence": min(0.7, best_score / 3),
            "keywords": [word for word in query_lower.split() if len(word) > 2]
        }

class DocumentClassifier:
    """Classifies documents by domain for intelligent storage and retrieval."""
    
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def classify_document(text_sample: str, filename: str) -> Dict[str, Any]:
        """
        Classify a document by domain using LLaMA 3.2:3B.
        
        Args:
            text_sample: Sample text from the document
            filename: Document filename
            
        Returns:
            Dictionary with domain, title, and metadata
        """
        # Check cache first
        cache_key = f"doc_classification:{hashlib.sha256((text_sample[:500] + filename).encode()).hexdigest()}"
        cached = redis_get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
        
        try:
            # Classification prompt
            classification_prompt = f"""
            Classify this document sample and extract metadata:
            
            Filename: {filename}
            Sample text: {text_sample[:1000]}
            
            Return a JSON object with:
            - domain: The main domain (e.g., "law", "physics", "chemistry", "religion", "medicine", "finance", "engineering", "education", "government", "technology")
            - title: Document title (extract from text or use filename)
            - confidence: Confidence score (0.0 to 1.0)
            - type: Document type (e.g., "textbook", "manual", "code", "guide", "reference")
            
            Examples:
            - Law document → {{"domain": "law", "title": "Pakistan Penal Code", "confidence": 0.95, "type": "code"}}
            - Chemistry textbook → {{"domain": "chemistry", "title": "Chemistry Grade 10", "confidence": 0.9, "type": "textbook"}}
            
            Response (JSON only):
            """
            
            response = ollama.chat(
                model=OLLAMA_LLM_MODEL,
                messages=[{"role": "user", "content": classification_prompt}],
                options={"base_url": OLLAMA_BASE_URL}
            )
            
            # Extract JSON from response
            response_text = response['message']['content']
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                # Cache the result
                redis_set(cache_key, json.dumps(result), expire=86400)  # 24 hour cache
                logger.info(f"Document classification: {filename} → {result.get('domain', 'unknown')}")
                return result
            else:
                # Fallback classification
                fallback = DocumentClassifier._fallback_classification(text_sample, filename)
                redis_set(cache_key, json.dumps(fallback), expire=86400)
                return fallback
                
        except Exception as e:
            logger.error(f"Document classification failed: {str(e)}")
            fallback = DocumentClassifier._fallback_classification(text_sample, filename)
            redis_set(cache_key, json.dumps(fallback), expire=86400)
            return fallback
    
    @staticmethod
    def _fallback_classification(text_sample: str, filename: str) -> Dict[str, Any]:
        """Fallback classification using keyword matching."""
        text_lower = text_sample.lower()
        filename_lower = filename.lower()
        
        # Domain keywords
        domain_keywords = {
            "law": ["section", "penal", "code", "law", "legal", "court", "judge", "crime", "punishment"],
            "chemistry": ["electronegativity", "molecule", "atom", "chemical", "reaction", "element", "compound"],
            "physics": ["force", "energy", "velocity", "acceleration", "mass", "gravity", "motion"],
            "religion": ["prayer", "worship", "god", "religious", "faith", "spiritual", "ritual"],
            "medicine": ["disease", "symptom", "treatment", "medicine", "patient", "diagnosis", "health"],
            "finance": ["money", "investment", "bank", "financial", "economy", "currency", "profit"],
            "engineering": ["design", "construction", "technical", "engineering", "system", "structure"],
            "education": ["student", "teacher", "school", "education", "learning", "course", "study"],
            "government": ["policy", "government", "official", "administration", "public", "service"],
            "technology": ["software", "computer", "technology", "digital", "programming", "system"]
        }
        
        # Find best matching domain
        best_domain = "general"
        best_score = 0
        
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > best_score:
                best_score = score
                best_domain = domain
        
        # Extract title from filename or text
        title = filename.replace('.pdf', '').replace('.docx', '').replace('.txt', '')
        
        return {
            "domain": best_domain,
            "title": title,
            "confidence": min(0.7, best_score / 3),
            "type": "document"
        }

class HybridSearch:
    """Hybrid search combining dense vector search with sparse keyword search."""
    
    @staticmethod
    def combine_scores(dense_scores: List[float], sparse_scores: List[float], 
                      dense_weight: float = 0.7) -> List[float]:
        """
        Combine dense and sparse search scores.
        
        Args:
            dense_scores: Vector similarity scores
            sparse_scores: BM25 keyword scores
            dense_weight: Weight for dense scores (0.0 to 1.0)
            
        Returns:
            Combined scores
        """
        if not dense_scores or not sparse_scores:
            return dense_scores or sparse_scores
        
        # Normalize scores to 0-1 range
        def normalize_scores(scores):
            if not scores:
                return scores
            min_score = min(scores)
            max_score = max(scores)
            if max_score == min_score:
                return [0.5] * len(scores)
            return [(s - min_score) / (max_score - min_score) for s in scores]
        
        norm_dense = normalize_scores(dense_scores)
        norm_sparse = normalize_scores(sparse_scores)
        
        # Combine with weighted average
        combined = []
        for i in range(len(norm_dense)):
            combined_score = (dense_weight * norm_dense[i] + 
                           (1 - dense_weight) * norm_sparse[i])
            combined.append(combined_score)
        
        return combined

def sanitize_text(text: str) -> str:
    """Sanitize text for safe processing."""
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_page_numbers(text: str) -> List[int]:
    """Extract page numbers from text."""
    page_patterns = [
        r'page\s+(\d+)',
        r'p\.\s*(\d+)',
        r'(\d+)\s*of\s*\d+',  # "45 of 100"
    ]
    
    page_numbers = []
    for pattern in page_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        page_numbers.extend([int(match) for match in matches])
    
    return sorted(list(set(page_numbers)))

def format_source_attribution(metadata: Dict[str, Any]) -> str:
    """Format source attribution for display."""
    title = metadata.get('title', metadata.get('filename', 'Unknown Document'))
    page = metadata.get('page_number')
    section = metadata.get('section')
    
    # Clean up title - remove file extensions and common prefixes
    title = re.sub(r'\.(pdf|docx|txt)$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'^[0-9]+\s*[-_]\s*', '', title)  # Remove leading numbers
    
    attribution = f"From: {title}"
    if page:
        attribution += f", Page {page}"
    if section:
        # Clean up section formatting
        section = re.sub(r'^[Ss]ection\s*', '', section)
        attribution += f", Section {section}"
    
    return attribution 