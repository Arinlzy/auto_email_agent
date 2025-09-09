from typing import Dict, Any, List, Optional
from .base_service import BaseService
from ..models.agent_factory import AgentFactory
from ..structure_outputs import WriterOutput, ProofReaderOutput
from ..prompts import EMAIL_WRITER_PROMPT, EMAIL_PROOFREADER_PROMPT

class EmailWritingService(BaseService):
    """Service for email writing and proofreading"""
    
    def __init__(self, config_manager=None, 
                 writer_preference: str = "default",
                 proofreader_preference: str = "default"):
        super().__init__(config_manager)
        self.writer_preference = writer_preference
        self.proofreader_preference = proofreader_preference
        
        self.writer_agent = None
        self.proofreader_agent = None
        
        self.initialize()
    
    def initialize(self):
        """Initialize writer and proofreader agents"""
        writer_config = self.config_manager.get_config("email_writing", self.writer_preference)
        self.writer_agent = AgentFactory.create_agent(writer_config)
        
        proofreader_config = self.config_manager.get_config("email_proofreading", self.proofreader_preference)
        self.proofreader_agent = AgentFactory.create_agent(proofreader_config)
    
    def write_draft(self, email_information: str, history: Optional[List[str]] = None) -> WriterOutput:
        """Write an email draft"""
        # 处理history格式 - 转换LangChain Message对象为字符串
        processed_history = []
        if history:
            for item in history:
                if hasattr(item, 'content'):  # LangChain Message对象
                    processed_history.append(item.content)
                elif isinstance(item, str):   # 字符串
                    processed_history.append(item)
                else:                        # 其他类型转为字符串
                    processed_history.append(str(item))
            
            prompt = f"{EMAIL_WRITER_PROMPT}\n\nHistory:\n{''.join(processed_history)}\n\nEmail Information:\n{email_information}"
        else:
            prompt = f"{EMAIL_WRITER_PROMPT}\n\nEmail Information:\n{email_information}"
        
        try:
            result = self.writer_agent.generate_structured_response(prompt, WriterOutput)
            print(f"\n=== EmailWritingService - AI返回结果 ===")
            print(f"Result type: {type(result)}")
            if result and hasattr(result, 'email'):
                print(f"Email content: {result.email}")
            print(f"========================================\n")
            return result
        except Exception as e:
            print(f"\n=== EmailWritingService错误 ===")
            print(f"Error: {e}")
            print(f"==============================\n")
            raise
    
    def proofread(self, initial_email: str, generated_email: str) -> ProofReaderOutput:
        """Proofread a generated email"""
        prompt = EMAIL_PROOFREADER_PROMPT.format(
            initial_email=initial_email,
            generated_email=generated_email
        )
        return self.proofreader_agent.generate_structured_response(prompt, ProofReaderOutput)
    
    def write_and_proofread(self, email_information: str, initial_email: str, 
                           history: Optional[List[str]] = None, max_iterations: int = 3) -> Dict[str, Any]:
        """Complete writing process with proofreading iterations"""
        results = {
            "drafts": [],
            "reviews": [],
            "final_draft": None,
            "approved": False,
            "iterations": 0
        }
        
        current_draft = None
        writer_history = history or []
        
        for iteration in range(max_iterations):
            # Write draft
            draft_result = self.write_draft(email_information, writer_history)
            current_draft = draft_result.email
            results["drafts"].append(current_draft)
            results["iterations"] = iteration + 1
            
            # Proofread
            review = self.proofread(initial_email, current_draft)
            results["reviews"].append(review)
            
            if review.send:
                results["final_draft"] = current_draft
                results["approved"] = True
                break
            else:
                # Add feedback to history for next iteration
                writer_history.append(f"**Draft {iteration + 1}:**\n{current_draft}")
                writer_history.append(f"**Proofreader Feedback:**\n{review.feedback}")
        
        if not results["approved"]:
            results["final_draft"] = current_draft  # Best effort
        
        return results
    
    def switch_writer_model(self, preference: str):
        """Switch to a different writer model"""
        self.writer_preference = preference
        writer_config = self.config_manager.get_config("email_writing", preference)
        self.writer_agent = AgentFactory.create_agent(writer_config)
    
    def switch_proofreader_model(self, preference: str):
        """Switch to a different proofreader model"""
        self.proofreader_preference = preference
        proofreader_config = self.config_manager.get_config("email_proofreading", preference)
        self.proofreader_agent = AgentFactory.create_agent(proofreader_config)
    
    def get_service_info(self) -> Dict[str, Any]:
        base_info = super().get_service_info()
        base_info.update({
            "writer_preference": self.writer_preference,
            "proofreader_preference": self.proofreader_preference,
            "writer_model": self.writer_agent.get_model_info() if self.writer_agent else None,
            "proofreader_model": self.proofreader_agent.get_model_info() if self.proofreader_agent else None
        })
        return base_info