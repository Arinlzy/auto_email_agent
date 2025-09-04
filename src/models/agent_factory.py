from typing import Dict, Type
from .base_agent import BaseAgent, ModelConfig, ModelProvider
from .openai_agent import OpenAIAgent
from .anthropic_agent import AnthropicAgent
from .openrouter_agent import OpenRouterAgent
from .zhipuai_agent import ZhipuAIAgent

class AgentFactory:
    _agent_classes: Dict[ModelProvider, Type[BaseAgent]] = {
        ModelProvider.OPENAI: OpenAIAgent,
        ModelProvider.ANTHROPIC: AnthropicAgent,
        ModelProvider.OPENROUTER: OpenRouterAgent,
        ModelProvider.ZHIPUAI: ZhipuAIAgent,
    }
    
    @classmethod
    def create_agent(cls, config: ModelConfig) -> BaseAgent:
        agent_class = cls._agent_classes.get(config.provider)
        if not agent_class:
            raise ValueError(f"Unsupported provider: {config.provider}")
        return agent_class(config)
    
    @classmethod
    def register_agent(cls, provider: ModelProvider, agent_class: Type[BaseAgent]):
        """Register a new agent class for a provider"""
        cls._agent_classes[provider] = agent_class
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported providers"""
        return [provider.value for provider in cls._agent_classes.keys()]