import argparse
import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Import our new components
from src.embeddings.embedding_factory import EmbeddingFactory
from src.models.base_agent import ModelProvider
from src.models.agent_factory import AgentFactory
from src.config.model_configs import ModelConfigManager

# Load environment variables from a .env file
load_dotenv()

RAG_SEARCH_PROMPT_TEMPLATE = """
Using the following pieces of retrieved context, answer the question comprehensively and concisely.
Ensure your response fully addresses the question based on the given context.

**IMPORTANT:**
Just provide the answer and never mention or refer to having access to the external context or information in your answer.
If you are unable to determine the answer from the provided context, state 'I don't know.'

Question: {question}
Context: {context}
"""

def get_db_path(provider: ModelProvider, model: str) -> str:
    """Generate database path based on provider and model"""
    return EmbeddingFactory.get_db_path(provider, model)

def create_vector_index(provider: ModelProvider = ModelProvider.ZHIPUAI, 
                       model: str = "embedding-3",
                       data_path: str = "./data/agency.txt",
                       chunk_size: int = 300,
                       chunk_overlap: int = 50,
                       test_query: bool = True):
    """
    Create vector index with specified provider and model
    
    Args:
        provider: AI provider (zhipuai, openai, anthropic, openrouter)
        model: Model name (can be embedding model or LLM model)
        data_path: Path to source data file
        chunk_size: Document chunk size
        chunk_overlap: Overlap between chunks
        test_query: Whether to run test query
    """
    
    print(f"Creating vector index with provider: {provider.value}, model: {model}")
    print("=" * 60)
    
    # Check if data file exists
    if not os.path.exists(data_path):
        print(f"Error: Data file {data_path} not found!")
        return False
    
    # Load and chunk documents
    print("Loading & Chunking Docs...")
    loader = TextLoader(data_path, encoding="utf-8")
    docs = loader.load()
    
    doc_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
    )
    doc_chunks = doc_splitter.split_documents(docs)
    print(f"Split into {len(doc_chunks)} chunks")
    
    # Create embeddings
    print(f"Creating embeddings with provider: {provider.value}, model: {model}")
    try:
        embeddings = EmbeddingFactory.create_embedding(provider, model)
    except Exception as e:
        print(f"❌ Error creating embeddings: {e}")
        
        # 提供更具体的建议
        if provider == ModelProvider.OPENROUTER:
            print("\n💡 Suggestions for OpenRouter:")
            print("   - Ensure OPENROUTER_API_KEY is set in .env file") 
            print("   - Check if the model is supported by OpenRouter")
            print("   - Try: --provider openrouter --model openai/text-embedding-3-small")
        elif provider == ModelProvider.OPENAI:
            print("\n💡 Suggestions for OpenAI:")
            print("   - Check if OPENAI_API_KEY is set in .env file")
            print("   - Verify your OpenAI account has embedding API access")
            print("   - Try: --provider openai --model text-embedding-3-small")
        elif provider == ModelProvider.ZHIPUAI:
            print("\n💡 Suggestions for ZhipuAI:")
            print("   - Check if ZHIPUAI_API_KEY is set in .env file")
            print("   - Try: --provider zhipuai --model embedding-3")
        elif provider == ModelProvider.ANTHROPIC:
            print("\n💡 Suggestions for Anthropic:")
            print("   - Anthropic models will use OpenAI embedding by default")
            print("   - Ensure OPENAI_API_KEY is set in .env file")
            print("   - Try: --provider anthropic --model claude-3-haiku-20240307")
        
        return False
    
    # Create vector store with provider-specific path
    db_path = get_db_path(provider, model)
    print(f"Saving to database: {db_path}")
    
    try:
        vectorstore = Chroma.from_documents(
            doc_chunks, 
            embeddings, 
            persist_directory=db_path
        )
        print("✓ Vector index created successfully!")
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return False
    
    # Test the RAG chain if requested
    if test_query:
        print("\nTesting RAG chain...")
        try:
            test_rag_chain(vectorstore, provider)
        except Exception as e:
            print(f"Error during testing: {e}")
            return False
    
    print(f"\n✓ Index creation completed for {provider.value} - {model}")
    print(f"Database saved at: {db_path}")
    return True

def test_rag_chain(vectorstore, provider: ModelProvider):
    """Test the RAG chain with a sample query"""
    
    # Create retriever
    vectorstore_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    # Get a test agent (using same provider for consistency)
    config_manager = ModelConfigManager()
    
    # Try to use the same provider for the test agent, fallback to zhipuai
    try:
        if provider == ModelProvider.ZHIPUAI:
            test_config = config_manager.get_config("rag_query_generation", "default")
        else:
            # For other providers, still use zhipuai for the LLM part
            test_config = config_manager.get_config("rag_query_generation", "default")
    except:
        test_config = config_manager.get_config("rag_query_generation", "default")
    
    test_agent = AgentFactory.create_agent(test_config)
    
    # Create RAG chain
    prompt = ChatPromptTemplate.from_template(RAG_SEARCH_PROMPT_TEMPLATE)
    rag_chain = (
        {"context": vectorstore_retriever, "question": RunnablePassthrough()}
        | prompt
        | test_agent.client
        | StrOutputParser()
    )
    
    # Test query
    test_question = "Dear Professor, I am a junior student majoring in Computer Science and I am very interested in your research direction. I would like to apply for a research internship in your laboratory. Do you accept undergraduate student applications? What materials should I prepare?"
    
    print("Running test query...")
    result = rag_chain.invoke(test_question)
    print(f"Question: {test_question}")
    print(f"Answer: {result}")

def main():
    parser = argparse.ArgumentParser(description="Create vector index with different providers and models")
    parser.add_argument(
        "--provider", 
        choices=["zhipuai", "openai", "anthropic", "openrouter"],
        required=True,
        help="AI provider (required)"
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Model name - can be embedding model (e.g., 'embedding-3', 'text-embedding-3-small') or LLM model (e.g., 'glm-4-flash', 'gpt-3.5-turbo', 'claude-3-haiku')"
    )
    parser.add_argument(
        "--data",
        default="./data/agency.txt", 
        help="Path to data file (default: ./data/agency.txt)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=300,
        help="Document chunk size (default: 300)"
    )
    parser.add_argument(
        "--chunk-overlap", 
        type=int,
        default=50,
        help="Overlap between chunks (default: 50)"
    )
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip test query"
    )
    parser.add_argument(
        "--list-examples",
        action="store_true", 
        help="List usage examples for different providers and models"
    )
    
    args = parser.parse_args()
    
    if args.list_examples:
        print("Usage Examples for Different Providers and Models:")
        print("=" * 60)
        print("📘 ZhipuAI Examples:")
        print("  # Using embedding model directly")
        print("  python create_index.py --provider zhipuai --model embedding-3")
        print("  # Using LLM model (will use default embedding-3)")
        print("  python create_index.py --provider zhipuai --model glm-4-flash")
        print("  python create_index.py --provider zhipuai --model glm-4")
        
        print("\n🔥 OpenAI Examples:")
        print("  # Using embedding model directly")
        print("  python create_index.py --provider openai --model text-embedding-3-small")
        print("  python create_index.py --provider openai --model text-embedding-3-large")
        print("  # Using LLM model (will use default text-embedding-3-small)")
        print("  python create_index.py --provider openai --model gpt-3.5-turbo")
        print("  python create_index.py --provider openai --model gpt-4")
        
        print("\n🧠 Anthropic Examples:")
        print("  # Using LLM model (will use OpenAI text-embedding-3-small as default)")
        print("  python create_index.py --provider anthropic --model claude-3-haiku-20240307")
        print("  python create_index.py --provider anthropic --model claude-3-sonnet-20240229")
        
        print("\n🔄 OpenRouter Examples:")
        print("  # Using embedding model via OpenRouter")
        print("  python create_index.py --provider openrouter --model openai/text-embedding-3-small")
        print("  # Using LLM model (will use default openai/text-embedding-3-small)")
        print("  python create_index.py --provider openrouter --model openai/gpt-3.5-turbo")
        print("  python create_index.py --provider openrouter --model anthropic/claude-3-haiku")
        return
    
    # 处理provider和model
    model = args.model
    
    # 使用指定的provider
    provider_map = {
        "zhipuai": ModelProvider.ZHIPUAI,
        "openai": ModelProvider.OPENAI,
        "anthropic": ModelProvider.ANTHROPIC,
        "openrouter": ModelProvider.OPENROUTER
    }
    provider = provider_map[args.provider]
    
    print(f"Using provider: {provider.value}, model: {model}")
    
    # Create the index
    success = create_vector_index(
        provider=provider,
        model=model,
        data_path=args.data,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        test_query=not args.no_test
    )
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main()