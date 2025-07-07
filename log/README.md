# log – Persistent Storage

This directory contains all persistent data for the PITB RAG Chatbot.

## Structure

- **conversations/** – Per-chat history, context, and embeddings (one folder per chat)
- **global_embeddings/** – (Optional) global embedding cache (by file hash)
- **pitb_rag_app.log** – Application logs (errors, debug info, etc.)

## Privacy

- All data is stored locally and never sent externally.
- You can delete or back up this directory to reset or migrate your knowledge base.

## Usage

- To reset all chat and embedding history, delete the contents of `log/` (or use the app’s reset button).
- For debugging, check `pitb_rag_app.log` for errors and system events. 