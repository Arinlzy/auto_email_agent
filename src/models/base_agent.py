from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    OPENROUTER = "openrouter"
    ZHIPUAI = "zhipuai"
    GROQ = "groq"

@dataclass
class ModelConfig:
    provider: ModelProvider
    model_name: str
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)

class BaseAgent(ABC):
    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self):
        """Initialize the specific model client"""
        pass
    
    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a simple text response"""
        pass
    
    @abstractmethod
    def generate_structured_response(self, prompt: str, output_schema: Any, **kwargs) -> Any:
        """Generate structured output response"""
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.config.provider.value,
            "model": self.config.model_name,
            "temperature": self.config.temperature
        }
    
    def _parse_structured_output(self, response_text: str, output_schema: Any):
        """Parse JSON response and convert to structured output"""
        try:
            # If response_text is already a dict, return it directly
            if isinstance(response_text, dict):
                data = response_text
            else:
                # Try to parse as JSON
                data = json.loads(response_text)
            
            # If output_schema has a constructor, use it
            if hasattr(output_schema, '__init__'):
                return output_schema(**data)
            else:
                return data
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Failed to parse structured output: {e}")