from typing import Dict, Any
from .base_service import BaseService
from ..models.agent_factory import AgentFactory
from ..structure_outputs import CategorizeEmailOutput
from ..prompts import CATEGORIZE_EMAIL_PROMPT

class EmailCategorizationService(BaseService):
    """Service for email categorization"""
    
    def __init__(self, config_manager=None, preference: str = "default"):
        super().__init__(config_manager)
        self.preference = preference
        self.agent = None
        self.initialize()
    
    def initialize(self):
        """Initialize the categorization agent"""
        config = self.config_manager.get_config("email_categorization", self.preference)
        self.agent = AgentFactory.create_agent(config)
    
    def categorize(self, email_body: str) -> CategorizeEmailOutput:
        """Categorize an email"""
        prompt = CATEGORIZE_EMAIL_PROMPT.format(email=email_body)
        return self.agent.generate_structured_response(prompt, CategorizeEmailOutput)
    
    def batch_categorize(self, email_bodies: list[str]) -> list[CategorizeEmailOutput]:
        """Categorize multiple emails"""
        return [self.categorize(body) for body in email_bodies]
    
    def switch_model(self, preference: str):
        """Switch to a different model preference"""
        self.preference = preference
        self.initialize()
    
    def get_service_info(self) -> Dict[str, Any]:
        base_info = super().get_service_info()
        base_info.update({
            "preference": self.preference,
            "model_info": self.agent.get_model_info() if self.agent else None
        })
        return base_info