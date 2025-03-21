from langchain.schema import SystemMessage, HumanMessage
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOpenRouter
from typing import Literal, Dict, Any
from src.config import config
import os

ModelRole = Literal["planner", "coder", "reviewer"]

class ModelRouter:
    """Routes requests to appropriate LLM based on required role with local-first priority"""
    
    def __init__(self):
        # Initialize model sources
        self.models = {}
        
        # Initialize local models
        self._init_local_models()
        
        # Initialize API models as fallback
        if os.getenv("OPENROUTER_API_KEY"):
            self._init_api_models()
    
    def _init_local_models(self):
        """Initialize connections to local models via Ollama"""
        try:
            # Add local models - modify these based on what you have installed
            self.models["local-llama3"] = Ollama(model="llama3")
            self.models["local-mistral"] = Ollama(model="mistral")
            self.models["local-codellama"] = Ollama(model="codellama")
            print("Local models initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize local models: {e}")
    
    def _init_api_models(self):
        """Initialize connections to API models via OpenRouter"""
        try:
            openrouter = ChatOpenRouter(
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
            self.models["gpt-4o"] = openrouter
            self.models["claude-3-opus"] = openrouter
            print("API models initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize API models: {e}")
    
    def get_model_for_role(self, role: ModelRole):
        """Get the appropriate model for a given role, prioritizing local models"""
        # Model preference order based on role
        model_preferences = {
            "planner": ["local-llama3", "local-mistral", "gpt-4o", "claude-3-opus"],
            "coder": ["local-codellama", "local-llama3", "claude-3-opus", "gpt-4o"],
            "reviewer": ["local-codellama", "local-llama3", "gpt-4o", "claude-3-opus"]
        }
        
        # Try models in preference order
        for model_name in model_preferences[role]:
            if model_name in self.models:
                return self.models[model_name], model_name
        
        raise ValueError(f"No available model found for role {role}")
    
    async def execute_prompt(self, role: ModelRole, prompt: str) -> Dict[str, Any]:
        """Execute a prompt with the appropriate model for a role"""
        model, model_name = self.get_model_for_role(role)
        
        # Handle different model interfaces
        if "local-" in model_name:  # Ollama models
            response = await model.ainvoke(prompt)
            return {"content": response, "model_used": model_name}
        else:  # API models through OpenRouter
            messages = [HumanMessage(content=prompt)]
            response = await model.ainvoke(
                messages, 
                model=model_name.replace("gpt-4o", "openai/gpt-4o").replace("claude-3-opus", "anthropic/claude-3-opus")
            )
            return {"content": response.content, "model_used": model_name}