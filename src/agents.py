from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_community.chat_models import ChatZhipuAI
from langchain_community.embeddings import ZhipuAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .structure_outputs import *
from .prompts import *

class Agents():
    def __init__(self):
        # 使用智谱AI的模型
        llm = ChatZhipuAI(model="glm-4-flash", temperature=0.1)
        
        # QA assistant chat
        embeddings = ZhipuAIEmbeddings(model="embedding-3")
        vectorstore = Chroma(persist_directory="db", embedding_function=embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        # Categorize email chain
        email_category_prompt = PromptTemplate(
            template=CATEGORIZE_EMAIL_PROMPT, 
            input_variables=["email"]
        )
        self.categorize_email = (
            email_category_prompt | 
            llm.with_structured_output(CategorizeEmailOutput)
        )

        # Used to design queries for RAG retrieval
        generate_query_prompt = PromptTemplate(
            template=GENERATE_RAG_QUERIES_PROMPT, 
            input_variables=["email"]
        )
    
        self.design_rag_queries = (
            generate_query_prompt | 
            llm.with_structured_output(RAGQueriesOutput)
        )
        
        # Generate answer to queries using RAG
        qa_prompt = ChatPromptTemplate.from_template(GENERATE_RAG_ANSWER_PROMPT)
        self.generate_rag_answer = (
            {"context": retriever, "question": RunnablePassthrough()} #! “字典式输入结构”+“自动解包” 的机制，将输入的数据流向不同处理器。
            | qa_prompt #! 上面的字典会自动传入 qa_prompt 中，填充 {context} 和 {question} 占位符
            | llm #! 
            | StrOutputParser()
        )

        # Used to write a draft email based on category and related informations
        writer_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", EMAIL_WRITER_PROMPT),
                MessagesPlaceholder("history"),
                ("human", "{email_information}")
            ]
        )
        self.email_writer = ( #! 传入的email_information 会自动填充 {email_information} 占位符
            writer_prompt | 
            llm.with_structured_output(WriterOutput) #! 自动返回 WriterOutput 格式的输出
        )

        # Verify the generated email
        proofreader_prompt = PromptTemplate(
            template=EMAIL_PROOFREADER_PROMPT, 
            input_variables=["initial_email", "generated_email"]
        )
        self.email_proofreader = (
            proofreader_prompt | 
            llm.with_structured_output(ProofReaderOutput) 
        )