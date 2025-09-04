from langchain_community.chat_models import ChatZhipuAI
from .base_agent import BaseAgent, ModelConfig
from typing import Any

class ZhipuAIAgent(BaseAgent):
    def _initialize_client(self):
        return ChatZhipuAI(
            model=self.config.model_name,
            temperature=self.config.temperature,
            api_key=self.config.api_key,
            **self.config.extra_params
        )
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.invoke(prompt)
            return response.content
        except Exception as e:
            raise Exception(f"ZhipuAI generation failed: {e}")
    
    def generate_structured_response(self, prompt: str, output_schema: Any, **kwargs) -> Any:
        try:
            # Use structured output if available
            if hasattr(self.client, 'with_structured_output'):
                structured_client = self.client.with_structured_output(output_schema)
                return structured_client.invoke(prompt)
            else:
                # Fallback to regular generation and parse
                response_text = self.generate_response(prompt, **kwargs)
                return self._parse_structured_output(response_text, output_schema)
        except Exception as e:
            raise Exception(f"ZhipuAI structured generation failed: {e}")