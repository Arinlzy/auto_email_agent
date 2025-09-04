import os
import yaml
from typing import Dict, Any
from ..models.base_agent import ModelConfig, ModelProvider

class ModelConfigManager:
    def __init__(self, config_file: str = "model_config.yaml"):
        self.config_file = config_file
        self.configs = self._load_configs()
    
    def _load_configs(self) -> Dict[str, Any]:
        """Load model configurations from YAML file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:
                # Return default configurations if file doesn't exist
                return self._get_default_configs()
        except Exception as e:
            print(f"Warning: Failed to load config file {self.config_file}: {e}")
            return self._get_default_configs()
    
    def _get_default_configs(self) -> Dict[str, Any]:
        """Get default model configurations"""
        return {
            "email_categorization": {
                "default": {
                    "provider": "zhipuai",
                    "model": "glm-4-flash",
                    "temperature": 0.1,
                    "api_key_env": "ZHIPUAI_API_KEY"
                }
            },
            "rag_query_generation": {
                "default": {
                    "provider": "zhipuai",
                    "model": "glm-4-flash",
                    "temperature": 0.1,
                    "api_key_env": "ZHIPUAI_API_KEY"
                }
            },
            "email_writing": {
                "default": {
                    "provider": "zhipuai",
                    "model": "glm-4-flash",
                    "temperature": 0.3,
                    "api_key_env": "ZHIPUAI_API_KEY"
                }
            },
            "email_proofreading": {
                "default": {
                    "provider": "zhipuai",
                    "model": "glm-4-flash",
                    "temperature": 0.1,
                    "api_key_env": "ZHIPUAI_API_KEY"
                }
            }
        }
    
    def get_config(self, task_type: str, preference: str = "default") -> ModelConfig:
        """Get model config based on task type and user preference"""
        task_configs = self.configs.get(task_type, {})
        config_data = task_configs.get(preference, task_configs.get("default"))
        
        if not config_data:
            raise ValueError(f"No configuration found for task type: {task_type}")
        
        return ModelConfig(
            provider=ModelProvider(config_data["provider"]),
            model_name=config_data["model"],
            temperature=config_data.get("temperature", 0.1),
            max_tokens=config_data.get("max_tokens"),
            api_key=os.getenv(config_data["api_key_env"]),
            base_url=config_data.get("base_url"),
            extra_params=config_data.get("extra_params", {})
        )
    
    def update_config(self, task_type: str, preference: str, config_data: Dict[str, Any]):
        """Update configuration for a specific task and preference"""
        if task_type not in self.configs:
            self.configs[task_type] = {}
        
        self.configs[task_type][preference] = config_data
    
    def save_configs(self):
        """Save current configurations to YAML file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.configs, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"Failed to save config file: {e}")
    
    def get_available_tasks(self) -> list[str]:
        """Get list of available task types"""
        return list(self.configs.keys())
    
    def get_available_preferences(self, task_type: str) -> list[str]:
        """Get list of available preferences for a task type"""
        return list(self.configs.get(task_type, {}).keys())