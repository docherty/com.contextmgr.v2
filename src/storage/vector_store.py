import os
from pathlib import Path
from src.config import config

class ContextVectorStore:
    """Vector store implementation using Chroma"""
    
    def __init__(self):
        db_path = config.PATHS["vector_store"] / "chroma_db"
        
        # Create directory if it doesn't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._embeddings = None
        self._vector_store = None
        self._document_class = None
        self._db_path = str(db_path)
    
    @property
    def embeddings(self):
        """Lazy initialization of embeddings to avoid startup issues"""
        if self._embeddings is None:
            # Import inside function to avoid Streamlit watcher issues with torch
            from langchain_huggingface import HuggingFaceEmbeddings
            self._embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
        return self._embeddings
    
    def _initialize_vector_store(self):
        """Separate initialization function to avoid early imports"""
        # Import inside function to avoid Streamlit watcher issues
        from langchain_chroma import Chroma
        from langchain_core.documents import Document
        
        # Create or load Chroma database
        vector_store = Chroma(
            persist_directory=self._db_path,
            embedding_function=self.embeddings,
        )
        
        print(f"Successfully initialized Chroma vector store at {self._db_path}")
        self._document_class = Document
        return vector_store
    
    @property
    def vector_store(self):
        """Lazy initialization of vector store to avoid startup issues"""
        if self._vector_store is None:
            self._vector_store = self._initialize_vector_store()
        return self._vector_store
    
    @property
    def document_class(self):
        """Get the Document class, initializing if necessary"""
        if self._document_class is None:
            # This will initialize both the vector store and document class
            _ = self.vector_store
        return self._document_class
    
    async def add_context(self, content, metadata=None):
        """Add content to the vector store"""
        if metadata is None:
            metadata = {}
            
        # Get vector store and Document class
        vector_store = self.vector_store
        Document = self.document_class
            
        # Create a Document object
        document = Document(page_content=content, metadata=metadata)
        
        # Add documents to the vector store
        vector_store.add_documents([document])
        # Persistence is automatic when persist_directory is provided
        
    async def search_context(self, query, k=5):
        """Search the vector store for relevant content"""
        # Initialize vector store only when needed
        vector_store = self.vector_store
        results = vector_store.similarity_search(query, k=k)
        return results