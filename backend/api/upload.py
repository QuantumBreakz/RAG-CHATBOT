from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from rag_core.document import DocumentProcessor
from rag_core.vectorstore import VectorStore
from rag_core.cache import get_file_hash
from typing import List
from datetime import datetime
import logging
import tempfile
import os

logger = logging.getLogger(__name__)
router = APIRouter()

class UploadResponse(BaseModel):
    filename: str
    file_hash: str
    status: str
    chunks: int
    uploaded_at: str
    message: str

class FileInfo(BaseModel):
    filename: str
    file_hash: str
    size: int
    chunks: int
    uploaded_at: str

@router.post("/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        # Read file content
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Generate file hash
        file_hash = get_file_hash(file_bytes)
        
        # Create a mock uploaded file object for DocumentProcessor
        class MockUploadedFile:
            def __init__(self, name, content, size):
                self.name = name
                self.content = content
                self.size = size
                self.type = "application/pdf" if name.lower().endswith('.pdf') else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
            def read(self):
                return self.content
        
        mock_file = MockUploadedFile(file.filename, file_bytes, len(file_bytes))
        
        # Process document
        all_splits = DocumentProcessor.process_document(mock_file, file_bytes, chunk_size=400, chunk_overlap=100)
        
        if not all_splits:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to process {file.filename}. The file might be corrupted, empty, or in an unsupported format."
            )
        
        # Add to vector collection
        success = VectorStore.add_to_vector_collection(all_splits, file.filename)
        
        if not success:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to add {file.filename} to vector collection. Please try again."
            )
        
        now = datetime.now().isoformat(timespec='seconds')
        
        return UploadResponse(
            filename=file.filename,
            file_hash=file_hash,
            status="ready",
            chunks=len(all_splits),
            uploaded_at=now,
            message=f"Successfully processed {file.filename} into {len(all_splits)} chunks"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error for {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/files", response_model=List[FileInfo])
async def list_uploaded_files():
    """
    List uploaded files from the vectorstore.
    """
    try:
        files = VectorStore.list_files()
        return files
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/files/{file_hash}")
async def delete_uploaded_file(file_hash: str):
    """
    Delete an uploaded file from the vectorstore by file_hash.
    """
    try:
        success = VectorStore.delete_file(file_hash=file_hash)
        if not success:
            raise HTTPException(status_code=404, detail=f"File with hash {file_hash} not found or could not be deleted")
        return {"message": f"File with hash {file_hash} deleted from vectorstore"}
    except Exception as e:
        logger.error(f"Error deleting file {file_hash}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 