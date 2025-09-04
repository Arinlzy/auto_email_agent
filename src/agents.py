from .services.service_manager import ServiceManager
from .config.model_configs import ModelConfigManager
from .models.base_agent import ModelProvider

class Agents:
    """Legacy adapter for the new service-based architecture"""
    
    def __init__(self, config_manager: ModelConfigManager = None):
        self.service_manager = ServiceManager(config_manager)
    
    # Legacy compatibility methods for existing code
    def categorize_email(self):
        """Legacy method for email categorization"""
        service = self.service_manager.get_categorization_service()
        
        class LegacyWrapper:
            def __init__(self, categorization_service):
                self.service = categorization_service
            
            def invoke(self, inputs):
                email_text = inputs.get('email', '')
                return self.service.categorize(email_text)
        
        return LegacyWrapper(service)
    
    def design_rag_queries(self):
        """Legacy method for RAG query generation"""
        service = self.service_manager.get_rag_service()
        
        class LegacyWrapper:
            def __init__(self, rag_service):
                self.service = rag_service
            
            def invoke(self, inputs):
                email_text = inputs.get('email', '')
                return self.service.generate_queries(email_text)
        
        return LegacyWrapper(service)
    
    def generate_rag_answer(self):
        """Legacy method for RAG answer generation"""
        service = self.service_manager.get_rag_service()
        
        class LegacyWrapper:
            def __init__(self, rag_service):
                self.service = rag_service
            
            def invoke(self, query):
                return self.service.retrieve_context(query)
        
        return LegacyWrapper(service)
    
    def email_writer(self):
        """Legacy method for email writing"""
        service = self.service_manager.get_writing_service()
        
        class LegacyWrapper:
            def __init__(self, writing_service):
                self.service = writing_service
            
            def invoke(self, inputs):
                email_information = inputs.get('email_information', '')
                history = inputs.get('history', [])
                return self.service.write_draft(email_information, history)
        
        return LegacyWrapper(service)
    
    def email_proofreader(self):
        """Legacy method for email proofreading"""
        service = self.service_manager.get_writing_service()
        
        class LegacyWrapper:
            def __init__(self, writing_service):
                self.service = writing_service
            
            def invoke(self, inputs):
                initial_email = inputs.get('initial_email', '')
                generated_email = inputs.get('generated_email', '')
                return self.service.proofread(initial_email, generated_email)
        
        return LegacyWrapper(service)
    
    # New direct service access methods (recommended for new code)
    def get_categorization_service(self):
        """Get categorization service for direct access"""
        return self.service_manager.get_categorization_service()
    
    def get_rag_service(self):
        """Get RAG service for direct access"""
        return self.service_manager.get_rag_service()
    
    def get_writing_service(self):
        """Get writing service for direct access"""
        return self.service_manager.get_writing_service()
    
    def get_service_manager(self):
        """Get service manager for full control"""
        return self.service_manager
    
    # Configuration methods
    def configure_embedding_model(self, provider: ModelProvider, model: str = None):
        """Configure embedding model for RAG"""
        self.service_manager.configure_rag(
            embedding_provider=provider,
            embedding_model=model
        )
    
    def configure_task_model(self, task_type: str, preference: str):
        """Configure model for specific task"""
        self.service_manager.switch_model_globally(task_type, preference)
    
    def get_system_info(self):
        """Get information about all services"""
        return self.service_manager.get_all_services_info()
    
    def health_check(self):
        """Check system health"""
        return self.service_manager.health_check()