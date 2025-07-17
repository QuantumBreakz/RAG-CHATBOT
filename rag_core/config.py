import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

def get_env_value(key, default=None):
    """Get environment variable value and strip any comments"""
    value = os.getenv(key, default)
    if value is not None:
        # Strip comments (anything after #)
        value = value.split('#')[0].strip()
    return value

# List of required environment variables
REQUIRED_ENV_VARS = [
    "LOG_LEVEL", "LOG_FILE", "OLLAMA_BASE_URL", "OLLAMA_EMBEDDING_MODEL", "OLLAMA_LLM_MODEL",
    "MAX_FILE_SIZE", "CHUNK_SIZE", "CHUNK_OVERLAP", "N_RESULTS", "CHROMA_DB_PATH", "CHROMA_COLLECTION_NAME",
    "CACHE_TTL", "EMBEDDINGS_CACHE_PATH"
]

# Enforce that all required environment variables are set
for var in REQUIRED_ENV_VARS:
    if get_env_value(var) is None:
        raise ValueError(f"Environment variable {var} must be set in your .env file.")

# Application configuration (all values loaded from environment)
LOG_LEVEL = get_env_value("LOG_LEVEL")
LOG_FILE = get_env_value("LOG_FILE")
OLLAMA_BASE_URL = get_env_value("OLLAMA_BASE_URL")
OLLAMA_EMBEDDING_MODEL = get_env_value("OLLAMA_EMBEDDING_MODEL")
OLLAMA_LLM_MODEL = get_env_value("OLLAMA_LLM_MODEL")
MAX_FILE_SIZE = int(get_env_value("MAX_FILE_SIZE"))
DEFAULT_CHUNK_SIZE = int(get_env_value("CHUNK_SIZE", "600"))
DEFAULT_CHUNK_OVERLAP = int(get_env_value("CHUNK_OVERLAP", "200"))
DEFAULT_N_RESULTS = int(get_env_value("N_RESULTS"))
CHROMA_DB_PATH = get_env_value("CHROMA_DB_PATH")
CHROMA_COLLECTION_NAME = get_env_value("CHROMA_COLLECTION_NAME")
CACHE_TTL = int(get_env_value("CACHE_TTL"))
EMBEDDINGS_CACHE_PATH = get_env_value("EMBEDDINGS_CACHE_PATH")

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# System prompt for the LLM (importable by other modules)
SYSTEM_PROMPT = """
You are an AI assistant developed by XOR, tasked with providing detailed answers based solely on the given context and conversation history. Your goal is to analyze the information provided and formulate a comprehensive, well-structured response to the question.

Context will be passed as "Context:"
Conversation history will be passed as "Conversation History:"
User question will be passed as "Question:"

To answer the question:
1. Thoroughly analyze the context and conversation history, identifying key information relevant to the question.
2. If the context contains conflicting or contradictory statements, always prefer the most recent, conclusive, or updated information. If a statement is later contradicted, corrected, or updated, use the latest information and clearly explain the reasoning.
3. Pay special attention to phrases such as "however", "in conclusion", "update", "but", "as of [year]", or similar, as these often indicate corrections or the most up-to-date information.
4. Organize your thoughts and plan your response to ensure a logical flow of information.
5. Formulate a detailed answer that directly addresses the question, using only the information provided in the context and conversation history.
6. Ensure your answer is comprehensive, covering all relevant aspects found in the context and history.
7. If the context and history don't contain sufficient information to fully answer the question, state this clearly in your response.
8. If the user asks about changing a parameter in a feasibility report or similar document (e.g., changing the number of cows from 10 to 15), intelligently infer the impact of this change. Recalculate all relevant costs, assets, and totals based on the new parameter, using the data in the context. Clearly explain which values change, how they are recalculated, and why. If any assumptions are needed, state them explicitly.
9. You are a mathematician and a financial analyst. You are able to perform calculations and provide detailed explanations of the calculations.
10. Do not make up information. If you don't know the answer, say so.
11. If tasked with answering mcqs based questions, return correct answers and explain in one line justification for each answer only, do not exceed 1 line justification. But do give answer, select an option if you must from the given options.
12. Do not and I repeat Do not show context to the user.


Format your response as follows:
1. Use clear, concise language, answer concisely, do not exceed max length of 500 words.
2. Organize your answer into paragraphs for readability.
3. Use bullet points or numbered lists where appropriate to break down complex information.
4. If relevant, include any headings or subheadings to structure your response.
"""