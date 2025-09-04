import anthropic
from .base_agent import BaseAgent, ModelConfig
from typing import Any

class AnthropicAgent(BaseAgent):
    def _initialize_client(self):
        return anthropic.Client(api_key=self.config.api_key)
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=self.config.max_tokens or 1024,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic generation failed: {e}")
    
    def generate_structured_response(self, prompt: str, output_schema: Any, **kwargs) -> Any:
        try:
            # Add JSON format instruction to prompt
            json_prompt = f"{prompt}\n\nPlease respond with a valid JSON object that matches the required schema."
            
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=self.config.max_tokens or 1024,
                messages=[{"role": "user", "content": json_prompt}],
                temperature=self.config.temperature,
                **kwargs
            )
            
            response_text = response.content[0].text
            return self._parse_structured_output(response_text, output_schema)
        except Exception as e:
            raise Exception(f"Anthropic structured generation failed: {e}")