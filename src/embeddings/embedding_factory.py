from typing import Any, Optional
from langchain_community.embeddings import ZhipuAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from ..models.base_agent import ModelProvider
import os
import yaml

class EmbeddingFactory:
    """Factory for creating embedding models based on provider or model name"""
    
    @staticmethod
    def _load_config():
        """Load model configuration from YAML file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'model_config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load model_config.yaml: {e}")
            return {}
    
    @staticmethod
    def _is_embedding_model(model_name: str) -> bool:
        """Check if the model is an embedding model"""
        embedding_keywords = [
            'embedding', 'embed', 'text-embedding', 
            'ada-002', 'similarity', 'search'
        ]
        model_lower = model_name.lower()
        return any(keyword in model_lower for keyword in embedding_keywords)
    
    @staticmethod
    def _detect_provider_from_openrouter_model(model_name: str) -> ModelProvider:
        """从OpenRouter模型名检测原始厂商"""
        model_lower = model_name.lower()
        
        if "/" in model_name:
            # OpenRouter格式: "openai/gpt-3.5-turbo", "anthropic/claude-3-haiku"
            provider_part = model_name.split("/")[0].lower()
            if "openai" in provider_part:
                return ModelProvider.OPENAI
            elif "anthropic" in provider_part:
                return ModelProvider.ANTHROPIC
            elif "zhipu" in provider_part or "glm" in provider_part:
                return ModelProvider.ZHIPUAI
        
        # 基于模型名检测
        if any(keyword in model_lower for keyword in ["gpt", "openai"]):
            return ModelProvider.OPENAI
        elif any(keyword in model_lower for keyword in ["claude", "anthropic"]):
            return ModelProvider.ANTHROPIC
        elif any(keyword in model_lower for keyword in ["glm", "zhipu"]):
            return ModelProvider.ZHIPUAI
        
        # 默认返回OpenAI
        return ModelProvider.OPENAI
    
    @staticmethod
    def _get_default_embedding_for_provider(provider: ModelProvider) -> str:
        """Get default embedding model for a given provider"""
        config = EmbeddingFactory._load_config()
        default_embeddings = config.get('default_embeddings', {})
        
        provider_map = {
            ModelProvider.ZHIPUAI: 'zhipuai',
            ModelProvider.OPENAI: 'openai', 
            ModelProvider.ANTHROPIC: 'anthropic',
            ModelProvider.OPENROUTER: 'openrouter'
        }
        
        provider_key = provider_map.get(provider, 'zhipuai')
        return default_embeddings.get(provider_key, 'embedding-3')
    
    @staticmethod
    def _resolve_embedding_config(provider: ModelProvider, model_name: str) -> tuple[str, ModelProvider]:
        """Resolve the final embedding model and provider to use
        
        Args:
            provider: The specified provider
            model_name: The specified model (embedding or LLM)
            
        Returns:
            tuple: (final_embedding_model, final_embedding_provider)
        """
        
        # 检查model_name是否是embedding模型
        if EmbeddingFactory._is_embedding_model(model_name):
            print(f"Embedding model '{model_name}' detected")
            
            # 对于OpenRouter，如果指定的是embedding模型，使用对应厂商的API
            if provider == ModelProvider.OPENROUTER:
                if "/" in model_name:
                    # OpenRouter格式，检测厂商并使用其API
                    detected_provider = EmbeddingFactory._detect_provider_from_openrouter_model(model_name)
                    clean_model = model_name.split("/")[-1] if "/" in model_name else model_name
                    print(f"OpenRouter embedding '{model_name}' -> using {detected_provider.value} API: {clean_model}")
                    return clean_model, detected_provider
                else:
                    # 直接指定embedding模型，检测其对应的厂商
                    embedding_provider = EmbeddingFactory._detect_provider_from_model(model_name)
                    print(f"OpenRouter embedding '{model_name}' -> using {embedding_provider.value} API")
                    return model_name, embedding_provider
            else:
                # 直接使用指定的embedding模型
                embedding_provider = EmbeddingFactory._detect_provider_from_model(model_name)
                return model_name, embedding_provider
        else:
            print(f"LLM model '{model_name}' detected")
            
            # model_name是LLM模型，获取对应provider的默认embedding
            if provider == ModelProvider.OPENROUTER:
                # OpenRouter不支持embedding，检测模型对应的厂商，使用该厂商的embedding API
                detected_provider = EmbeddingFactory._detect_provider_from_openrouter_model(model_name)
                embedding_model = EmbeddingFactory._get_default_embedding_for_provider(detected_provider)
                print(f"OpenRouter LLM '{model_name}' -> detected provider: {detected_provider.value}")
                print(f"Using {detected_provider.value} embedding API: {embedding_model}")
                return embedding_model, detected_provider
            elif provider == ModelProvider.ANTHROPIC:
                # Anthropic LLM模型，使用OpenAI的默认embedding
                default_embed = EmbeddingFactory._get_default_embedding_for_provider(provider)
                print(f"Anthropic LLM, using OpenAI embedding: {default_embed}")
                return default_embed, ModelProvider.OPENAI
            else:
                # 其他provider，使用对应的默认embedding
                default_embed = EmbeddingFactory._get_default_embedding_for_provider(provider)
                embedding_provider = EmbeddingFactory._detect_provider_from_model(default_embed)
                return default_embed, embedding_provider
    
    @staticmethod
    def create_embedding(provider: Optional[ModelProvider] = None, model_name: str = None, **kwargs) -> Any:
        """Create embedding model based on provider and model name
        
        Args:
            provider: The AI provider (zhipuai, openai, anthropic, openrouter)
            model_name: Either an embedding model name or LLM model name
        
        Returns:
            Embedding model instance
        """
        
        # 必须指定provider和model_name
        if not provider or not model_name:
            raise ValueError("Both provider and model_name must be specified")
        
        # 确定最终使用的embedding模型和provider
        final_embedding_model, final_embedding_provider = EmbeddingFactory._resolve_embedding_config(provider, model_name)
        
        print(f"Final embedding config: provider={final_embedding_provider.value}, model={final_embedding_model}")
        
        # 创建embedding实例
        if final_embedding_provider == ModelProvider.ZHIPUAI:
            return ZhipuAIEmbeddings(
                model=final_embedding_model,
                api_key=os.getenv("ZHIPUAI_API_KEY"),
                **kwargs
            )
        
        elif final_embedding_provider == ModelProvider.OPENAI:
            return OpenAIEmbeddings(
                model=final_embedding_model,
                api_key=os.getenv("OPENAI_API_KEY"),
                **kwargs
            )
        
        elif final_embedding_provider == ModelProvider.OPENROUTER:
            # 使用OpenRouter API
            return OpenAIEmbeddings(
                model=final_embedding_model,
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                **kwargs
            )
        
        else:
            # 默认使用智谱AI
            return ZhipuAIEmbeddings(
                model=final_embedding_model or "embedding-3",
                api_key=os.getenv("ZHIPUAI_API_KEY"),
                **kwargs
            )
    
    @staticmethod
    def _detect_provider_from_model(model_name: str) -> ModelProvider:
        """根据模型名检测提供商"""
        model_lower = model_name.lower()
        
        # OpenAI模型特征 (包括通过OpenRouter访问的OpenAI模型)
        if any(keyword in model_lower for keyword in ["gpt", "text-embedding", "ada", "davinci", "openai/"]):
            return ModelProvider.OPENAI
        
        # 智谱AI模型特征
        elif any(keyword in model_lower for keyword in ["glm", "embedding-", "zhipu"]):
            return ModelProvider.ZHIPUAI
        
        # OpenRouter特殊模型路径
        elif "/" in model_name:  # OpenRouter格式如 "openai/text-embedding-3-small"
            if "openai" in model_lower:
                return ModelProvider.OPENAI
            elif "zhipu" in model_lower or "glm" in model_lower:
                return ModelProvider.ZHIPUAI
            else:
                return ModelProvider.OPENROUTER
        
        # 默认使用智谱AI
        else:
            print(f"Warning: Cannot detect provider for model '{model_name}', using ZhipuAI as default")
            return ModelProvider.ZHIPUAI
    
    @staticmethod
    def get_provider_from_model(model_name: str) -> ModelProvider:
        """公开方法：根据模型名获取提供商"""
        return EmbeddingFactory._detect_provider_from_model(model_name)
    
    @staticmethod
    def get_db_path(provider: ModelProvider, model_name: str) -> str:
        """Generate database path based on provider and model
        
        Args:
            provider: The AI provider
            model_name: Either embedding model or LLM model name
        
        Returns:
            Database path string
        """
        # 获取实际使用的embedding配置
        actual_embedding, actual_provider = EmbeddingFactory._resolve_embedding_config(provider, model_name)
        
        # 清理模型名用于路径
        clean_model = actual_embedding.replace('-', '_').replace('/', '_').replace(':', '_')
        provider_name = actual_provider.value
        
        return f"db/db_{provider_name}_{clean_model}"
    
    @staticmethod
    def get_embedding_dimension(provider: ModelProvider = None, model_name: str = None) -> int:
        """Get embedding dimension for the model"""
        
        # 如果没有指定provider，从model_name检测
        if not provider and model_name:
            provider = EmbeddingFactory._detect_provider_from_model(model_name)
        
        dimension_map = {
            ModelProvider.ZHIPUAI: {
                "embedding-3": 1024, 
                "embedding-2": 1024,
                "glm-embedding": 1024
            },
            ModelProvider.OPENAI: {
                "text-embedding-3-small": 1536,
                "text-embedding-3-large": 3072,
                "text-embedding-ada-002": 1536,
                "gpt-embedding": 1536
            }
        }
        
        provider_dims = dimension_map.get(provider, {})
        return provider_dims.get(model_name, 1024)  # 默认1024