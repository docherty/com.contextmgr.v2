import os
import pathlib
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Model configuration
    MODELS = {
        "planner": os.getenv("PLANNER_MODEL", "gpt-4o"),
        "coder": os.getenv("CODER_MODEL", "claude-3-opus-20240229"),
        "reviewer": os.getenv("REVIEWER_MODEL", "gpt-4o"),
    }
    
    # Storage paths
    BASE_DIR = pathlib.Path.cwd()
    PATHS = {
        "plans": BASE_DIR / "data" / "plans",
        "context": BASE_DIR / "data" / "context",
        "vector_store": BASE_DIR / "data" / "vectors",
    }
    
    # Git configuration
    GIT = {
        "auto_commit": os.getenv("GIT_AUTO_COMMIT", "false").lower() == "true",
        "commit_message": os.getenv("GIT_COMMIT_MESSAGE", "Update from context manager"),
    }
    
    # LLM provider configuration
    API_KEYS = {
        "openai": None, 
        "anthropic": None,
    }

    def __init__(self):
        # Create directories if they don't exist
        for path in self.PATHS.values():
            path.mkdir(parents=True, exist_ok=True)

config = Config()