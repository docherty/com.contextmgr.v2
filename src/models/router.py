import os
from typing import Dict, List, Optional, Any
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from src.config import config

# Handle OpenAI imports properly
OPENAI_AVAILABLE = False
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    try:
        from langchain_community.chat_models import ChatOpenAI
        OPENAI_AVAILABLE = True
    except ImportError:
        # Fall back to deprecated import path
        try:
            from langchain.chat_models import ChatOpenAI
            OPENAI_AVAILABLE = True
        except ImportError:
            pass

# Handle Ollama imports properly
OLLAMA_AVAILABLE = False
try:
    from langchain_community.chat_models import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    try:
        from langchain.chat_models import ChatOllama
        OLLAMA_AVAILABLE = True
    except ImportError:
        pass

# Optional Anthropic support
ANTHROPIC_AVAILABLE = False
try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

class ModelRouter:
    """A router to handle different LLM models based on configuration."""
    
    DEFAULT_MODEL = "gemma3:12b"
    
    def __init__(self):
        self.models: Dict[str, BaseChatModel] = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize the configured models."""
        # First try to initialize the default Ollama model
        self._initialize_default_model()
        
        # Then initialize other configured models
        for model_type, model_name in config.MODELS.items():
            if model_name.startswith("gpt"):
                # OpenAI models
                if not OPENAI_AVAILABLE:
                    raise ImportError(
                        "To use OpenAI models, please install langchain-openai: "
                        "pip install langchain-openai"
                    )
                
                # Check for API key
                api_key = os.environ.get("OPENAI_API_KEY", config.API_KEYS.get("openai"))
                if not api_key:
                    # For development, skip initializing this model but don't crash
                    print(f"Skipping {model_name} initialization: No OpenAI API key found")
                    continue
                
                self.models[model_type] = ChatOpenAI(
                    model=model_name,
                    temperature=0.1,
                    openai_api_key=api_key,
                )
            elif model_name.startswith("claude"):
                # Anthropic models
                if not ANTHROPIC_AVAILABLE:
                    raise ImportError(
                        "To use Claude models, please install langchain_anthropic: "
                        "pip install langchain-anthropic"
                    )
                
                # Check for API key
                api_key = os.environ.get("ANTHROPIC_API_KEY", config.API_KEYS.get("anthropic"))
                if not api_key:
                    # For development, skip initializing this model but don't crash
                    print(f"Skipping {model_name} initialization: No Anthropic API key found")
                    continue
                
                self.models[model_type] = ChatAnthropic(
                    model=model_name,
                    temperature=0.1,
                    anthropic_api_key=api_key,
                )
            elif model_name.startswith("local-"):
                # Local models via Ollama
                if not OLLAMA_AVAILABLE:
                    raise ImportError(
                        "To use local models, please install langchain-community: "
                        "pip install langchain-community"
                    )
                
                actual_model = model_name.replace("local-", "")
                self.models[model_type] = ChatOllama(
                    model=actual_model,
                    temperature=0.1,
                )

    def _initialize_default_model(self):
        """Initialize the default Ollama model."""
        if not OLLAMA_AVAILABLE:
            print(f"Cannot initialize default Ollama model: langchain-community not available")
            return
        
        try:
            default_model = ChatOllama(
                model=self.DEFAULT_MODEL,
                temperature=0.1,
            )
            self.models["default"] = default_model
            print(f"Successfully initialized default model: {self.DEFAULT_MODEL}")
        except Exception as e:
            print(f"Failed to initialize default model {self.DEFAULT_MODEL}: {str(e)}")
    
    def get_model(self, model_type: str) -> BaseChatModel:
        """Get the model instance for the specified type.
        Falls back to default Ollama model if the requested model is unavailable.
        """
        if model_type in self.models:
            return self.models[model_type]
        elif "default" in self.models:
            print(f"Model type {model_type} not configured, falling back to default model")
            return self.models["default"]
        else:
            raise ValueError(f"Model type {model_type} not configured and default model unavailable")
    
    async def generate_response(self, model_type: str, prompt: str, 
                               system_message: Optional[str] = None) -> str:
        """Generate a response from the specified model type.
        Falls back to the default model if there's a problem with the specified model.
        """
        try:
            model = self.get_model(model_type)
            
            # Create a chat prompt template
            if system_message:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", system_message),
                    ("human", "{input}")
                ])
            else:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("human", "{input}")
                ])
            
            # Create a simple chain
            chain = prompt_template | model | StrOutputParser()
            
            # Run the chain
            return await chain.ainvoke({"input": prompt})
        except Exception as e:
            if model_type != "default" and "default" in self.models:
                print(f"Error using {model_type}, falling back to default model: {str(e)}")
                # Recursive call with the default model
                return await self.generate_response("default", prompt, system_message)
            else:
                raise e