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
            # 获取schema的字段信息
            if hasattr(output_schema, 'model_fields'):
                fields_info = []
                for field_name, field_info in output_schema.model_fields.items():
                    description = getattr(field_info, 'description', f'The {field_name} field')
                    fields_info.append(f'"{field_name}": {description}')
                fields_desc = ', '.join(fields_info)
            else:
                fields_desc = "required fields as defined in the schema"
            
            # 改进的prompt，明确要求实际内容而不是schema
            json_prompt = f"""{prompt}

CRITICAL INSTRUCTION: Generate actual content, not a schema or template!

For email writing tasks, provide the actual email text.
For categorization tasks, provide the actual category.
For query generation, provide actual search queries.

Required JSON format: {{{fields_desc}}}

BAD example (schema): {{"properties": {{"email": {{"type": "string"}}}}}}
GOOD example (content): {{"email": "Dear Emma,\\n\\nThank you for the invitation to speak at ICML 2025...\\n\\nBest regards"}}

Return ONLY the JSON with real content:"""
            
            # 直接使用常规生成并解析
            response_text = self.generate_response(json_prompt, **kwargs)
            print(f"ZhipuAI raw response: {response_text}")  # 调试
            
            # 尝试清理响应文本（去除markdown格式）
            clean_response = response_text.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]  # 去除 ```json
            if clean_response.startswith('```'):
                clean_response = clean_response[3:]   # 去除 ```
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]  # 去除结尾的 ```
            clean_response = clean_response.strip()
            
            return self._parse_structured_output(clean_response, output_schema)
        except Exception as e:
            raise Exception(f"ZhipuAI structured generation failed: {e}")