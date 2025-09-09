from typing import Dict, Any, List
from langchain_chroma import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from .base_service import BaseService
from ..models.agent_factory import AgentFactory
from ..embeddings.embedding_factory import EmbeddingFactory
from ..models.base_agent import ModelProvider
from ..structure_outputs import RAGQueriesOutput
from ..prompts import GENERATE_RAG_QUERIES_PROMPT, GENERATE_RAG_ANSWER_PROMPT

class RAGService(BaseService):
    """Service for RAG (Retrieval-Augmented Generation)"""
    
    def __init__(self, config_manager=None, 
                 embedding_provider: ModelProvider = ModelProvider.ZHIPUAI,
                 embedding_model: str = "embedding-3",
                 query_preference: str = "default"):
        super().__init__(config_manager)
        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model
        self.query_preference = query_preference
        
        self.embeddings = None
        self.vectorstore = None
        self.retriever = None
        self.query_agent = None
        self.rag_chain = None
        
        self.initialize()
    
    def initialize(self):
        """Initialize the RAG system"""
        # Initialize embeddings based on provider
        self.embeddings = EmbeddingFactory.create_embedding(
            self.embedding_provider, 
            self.embedding_model
        )
        
        # Initialize vector store with provider-specific path
        db_path = self._get_db_path(self.embedding_provider, self.embedding_model)
        self.vectorstore = Chroma(
            persist_directory=db_path, 
            embedding_function=self.embeddings
        )
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        
        # Initialize query generation agent
        query_config = self.config_manager.get_config("rag_query_generation", self.query_preference)
        self.query_agent = AgentFactory.create_agent(query_config)
        
        # Create RAG chain
        qa_prompt = ChatPromptTemplate.from_template(GENERATE_RAG_ANSWER_PROMPT)
        self.rag_chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | qa_prompt
            | self.query_agent.client
            | StrOutputParser()
        )
    
    def generate_queries(self, email_body: str) -> RAGQueriesOutput:
        """Generate RAG queries for an email"""
        prompt = GENERATE_RAG_QUERIES_PROMPT.format(email=email_body)
        return self.query_agent.generate_structured_response(prompt, RAGQueriesOutput)
    
    def retrieve_context(self, query: str) -> str:
        """Retrieve context for a single query"""
        return self.rag_chain.invoke(query)
    
    def retrieve_multi_context(self, queries: List[str]) -> str:
        """Retrieve context for multiple queries"""
        final_answer = ""
        for query in queries:
            rag_result = self.retrieve_context(query)
            final_answer += f"{query}\n{rag_result}\n\n"
        return final_answer
    
    def process_email_for_context(self, email_body: str) -> str:
        """Complete RAG process: generate queries + retrieve context"""
        # Generate queries
        query_result = self.generate_queries(email_body)
        
        # Retrieve context for all queries
        return self.retrieve_multi_context(query_result.queries)
    
    def switch_embedding_model(self, provider: ModelProvider, model: str = None):
        """Switch to a different embedding model"""
        self.embedding_provider = provider
        self.embedding_model = model or self._get_default_model(provider)
        self.initialize()
    
    def switch_query_agent(self, preference: str):
        """Switch to a different query generation agent"""
        self.query_preference = preference
        self.initialize()
    
    def _get_default_model(self, provider: ModelProvider) -> str:
        """Get default embedding model for provider"""
        defaults = {
            ModelProvider.ZHIPUAI: "embedding-3",
            ModelProvider.OPENAI: "text-embedding-3-small",
            ModelProvider.OPENROUTER: "text-embedding-3-small"
        }
        return defaults.get(provider, "embedding-3")
    
    def _get_db_path(self, provider: ModelProvider, model: str) -> str:
        """Generate database path based on embedding provider and model"""
        # Use the same path generation logic as EmbeddingFactory
        return EmbeddingFactory.get_db_path(provider, model)
    
    def get_service_info(self) -> Dict[str, Any]:
        base_info = super().get_service_info()
        base_info.update({
            "embedding_provider": self.embedding_provider.value,
            "embedding_model": self.embedding_model,
            "query_preference": self.query_preference,
            "query_agent_info": self.query_agent.get_model_info() if self.query_agent else None
        })
        return base_info