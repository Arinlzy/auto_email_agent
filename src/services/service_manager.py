from typing import Dict, Any, Optional
from .base_service import BaseService
from .email_categorization_service import EmailCategorizationService
from .rag_service import RAGService
from .email_writing_service import EmailWritingService
from ..config.model_configs import ModelConfigManager
from ..models.base_agent import ModelProvider

class ServiceManager:
    """Central manager for all email processing services"""
    
    def __init__(self, config_manager: ModelConfigManager = None):
        self.config_manager = config_manager or ModelConfigManager()
        self.services: Dict[str, BaseService] = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all services with default configurations"""
        self.services = {
            'categorization': EmailCategorizationService(self.config_manager),
            'rag': RAGService(self.config_manager),
            'writing': EmailWritingService(self.config_manager)
        }
    
    def get_categorization_service(self) -> EmailCategorizationService:
        """Get email categorization service"""
        return self.services['categorization']
    
    def get_rag_service(self) -> RAGService:
        """Get RAG service"""
        return self.services['rag']
    
    def get_writing_service(self) -> EmailWritingService:
        """Get email writing service"""
        return self.services['writing']
    
    def configure_categorization(self, preference: str = "default"):
        """Configure categorization service"""
        self.services['categorization'] = EmailCategorizationService(
            self.config_manager, preference
        )
    
    def configure_rag(self, embedding_provider: ModelProvider = ModelProvider.ZHIPUAI,
                      embedding_model: str = "embedding-3",
                      query_preference: str = "default"):
        """Configure RAG service"""
        self.services['rag'] = RAGService(
            self.config_manager,
            embedding_provider,
            embedding_model,
            query_preference
        )
    
    def configure_writing(self, writer_preference: str = "default",
                         proofreader_preference: str = "default"):
        """Configure email writing service"""
        self.services['writing'] = EmailWritingService(
            self.config_manager,
            writer_preference,
            proofreader_preference
        )
    
    def get_all_services_info(self) -> Dict[str, Any]:
        """Get information about all services"""
        return {
            service_name: service.get_service_info()
            for service_name, service in self.services.items()
        }
    
    def switch_model_globally(self, task_type: str, preference: str):
        """Switch model preference for a specific task type across services"""
        if task_type == "email_categorization":
            self.configure_categorization(preference)
        elif task_type == "rag_query_generation":
            current_rag = self.get_rag_service()
            self.configure_rag(
                current_rag.embedding_provider,
                current_rag.embedding_model,
                preference
            )
        elif task_type == "email_writing":
            current_writing = self.get_writing_service()
            self.configure_writing(preference, current_writing.proofreader_preference)
        elif task_type == "email_proofreading":
            current_writing = self.get_writing_service()
            self.configure_writing(current_writing.writer_preference, preference)
    
    def health_check(self) -> Dict[str, bool]:
        """Check if all services are properly initialized"""
        health_status = {}
        for service_name, service in self.services.items():
            try:
                service.get_service_info()
                health_status[service_name] = True
            except Exception:
                health_status[service_name] = False
        return health_status