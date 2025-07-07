# demo-rag-chroma – ChromaDB Storage

This directory contains ChromaDB’s persistent vector storage files for the PITB RAG Chatbot.

## Files

- **index_metadata.pickle, link_lists.bin, length.bin, data_level0.bin, header.bin** – Internal ChromaDB files for vector storage and retrieval.

## Usage

- Do not edit or delete these files manually unless you want to reset the knowledge base.
- Back up this directory to preserve your vector database and all document embeddings.
- If you want to reset the knowledge base, use the app’s reset button or delete this directory. 