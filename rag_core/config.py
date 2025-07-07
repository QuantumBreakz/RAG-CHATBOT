import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# List of required environment variables
REQUIRED_ENV_VARS = [
    "LOG_LEVEL", "LOG_FILE", "OLLAMA_BASE_URL", "OLLAMA_EMBEDDING_MODEL", "OLLAMA_LLM_MODEL",
    "MAX_FILE_SIZE", "CHUNK_SIZE", "CHUNK_OVERLAP", "N_RESULTS", "CHROMA_DB_PATH", "CHROMA_COLLECTION_NAME",
    "CACHE_TTL", "EMBEDDINGS_CACHE_PATH"
]

# Enforce that all required environment variables are set
for var in REQUIRED_ENV_VARS:
    if os.getenv(var) is None:
        raise ValueError(f"Environment variable {var} must be set in your .env file.")

# Application configuration (all values loaded from environment)
LOG_LEVEL = os.getenv("LOG_LEVEL")
LOG_FILE = os.getenv("LOG_FILE")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE"))
DEFAULT_CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 600))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
DEFAULT_N_RESULTS = int(os.getenv("N_RESULTS"))
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME")
CACHE_TTL = int(os.getenv("CACHE_TTL"))
EMBEDDINGS_CACHE_PATH = os.getenv("EMBEDDINGS_CACHE_PATH")

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# System prompt for the LLM (importable by other modules)
SYSTEM_PROMPT = """
You are an AI assistant developed by PITB, tasked with providing detailed answers based solely on the given context and conversation history. Your goal is to analyze the information provided and formulate a comprehensive, well-structured response to the question.

Context will be passed as "Context:"
Conversation history will be passed as "Conversation History:"
User question will be passed as "Question:"

To answer the question:
1. Thoroughly analyze the context and conversation history, identifying key information relevant to the question.
2. Organize your thoughts and plan your response to ensure a logical flow of information.
3. Formulate a detailed answer that directly addresses the question, using only the information provided in the context and conversation history.
4. Ensure your answer is comprehensive, covering all relevant aspects found in the context and history.
5. If the context and history don't contain sufficient information to fully answer the question, state this clearly in your response.
6. If the user asks about changing a parameter in a feasibility report or similar document (e.g., changing the number of cows from 10 to 15), intelligently infer the impact of this change. Recalculate all relevant costs, assets, and totals based on the new parameter, using the data in the context. Clearly explain which values change, how they are recalculated, and why. If any assumptions are needed, state them explicitly.

Format your response as follows:
1. Use clear, concise language, answer concisely, do not exceed max length of 300 words.
2. Organize your answer into paragraphs for readability.
3. Use bullet points or numbered lists where appropriate to break down complex information.
4. If relevant, include any headings or subheadings to structure your response.
5. Ensure proper grammar, punctuation, and spelling throughout your answer.
6. Perform calculations if required or if available in document given the previous stats.
""" 