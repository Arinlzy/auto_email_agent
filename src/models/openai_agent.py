import openai
from .base_agent import BaseAgent, ModelConfig
from typing import Any
import json

class OpenAIAgent(BaseAgent):
    def _initialize_client(self):
        return openai.Client(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI generation failed: {e}")
    
    def generate_structured_response(self, prompt: str, output_schema: Any, **kwargs) -> Any:
        try:
            # Add JSON format instruction to prompt
            json_prompt = f"{prompt}\n\nPlease respond with a valid JSON object."
            
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": json_prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"} if "gpt-" in self.config.model_name else None,
                **kwargs
            )
            
            response_text = response.choices[0].message.content
            return self._parse_structured_output(response_text, output_schema)
        except Exception as e:
            raise Exception(f"OpenAI structured generation failed: {e}")