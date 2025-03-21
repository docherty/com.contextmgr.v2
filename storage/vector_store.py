import os
import sqlite3
from pathlib import Path
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import SQLiteVSS
from src.config import config

class ContextVectorStore:
    """Vector store implementation using SQLite with vector extensions"""
    
    def __init__(self):
        db_path = config.PATHS["vector_store"] / "context.db"
        
        # Initialize embeddings model - using a smaller model for local embedding
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Create directory if it doesn't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize the vector store
        self.vector_store = SQLiteVSS(
            embedding=self.embeddings,
            db_file=str(db_path),
            table_name="context_vectors",
            content_column="content",
            metadata_column="metadata"
        )
    
    async def add_context(self, content, metadata=None):
        """Add content to the vector store"""
        if metadata is None:
            metadata = {}
        
        # Add documents to the vector store
        self.vector_store.add_texts(
            texts=[content],
            metadatas=[metadata]
        )
    
    async def search_context(self, query, k=5):
        """Search the vector store for relevant content"""
        results = self.vector_store.similarity_search(query, k=k)
        return results