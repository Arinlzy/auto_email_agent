from typing import final
from colorama import Fore, Style
from .agents import Agents
from .tools.email import create_email_tools
from .state import GraphState, Email


class Nodes:
    def __init__(self):
        self.agents = Agents()
        self.email_tools = create_email_tools(config_file='email_config.yaml')

    def load_new_emails(self, state: GraphState) -> GraphState:
        """Loads new emails and updates the state."""
        print(Fore.YELLOW + "Loading new emails...\n" + Style.RESET_ALL)
        recent_emails = self.email_tools.fetch_unanswered_emails()
        emails = [Email(**email) for email in recent_emails]
        
        # 打印每封邮件的内容
        for email in emails:
            print(Fore.CYAN + "\n=== 新邮件 ===" + Style.RESET_ALL)
            print(Fore.CYAN + f"发件人: {email.sender}" + Style.RESET_ALL)
            print(Fore.CYAN + f"主题: {email.subject}" + Style.RESET_ALL)
            print(Fore.CYAN + "内容:" + Style.RESET_ALL)
            print(email.body)
            print(Fore.CYAN + "===========\n" + Style.RESET_ALL)
            
        return {"emails": emails} 
        #! LangGraph 的 状态机模型（stateful workflow），每个节点（node）是函数，
        #! 传入一个状态（state），输出更新后的状态（部分字段），LangGraph 自动 合并。
        
        #! LangGraph 会 自动将刚才更新后的 state 传给下一个节点函数：

    def check_new_emails(self, state: GraphState) -> str:
        """Checks if there are new emails to process."""
        if len(state['emails']) == 0:
            print(Fore.RED + "No new emails" + Style.RESET_ALL)
            return "empty"
        else:
            print(Fore.GREEN + "New emails to process" + Style.RESET_ALL)
            return "process"
        
    def is_email_inbox_empty(self, state: GraphState) -> GraphState:
        return state

    def categorize_email(self, state: GraphState) -> GraphState:
        """Categorizes the current email using the categorize_email agent."""
        print(Fore.YELLOW + "Checking email category...\n" + Style.RESET_ALL)
        
        # Get the last email
        current_email = state["emails"][-1]
        print(Fore.CYAN + "\n=== 正在处理的邮件 ===" + Style.RESET_ALL)
        print(Fore.CYAN + f"发件人: {current_email.sender}" + Style.RESET_ALL)
        print(Fore.CYAN + f"主题: {current_email.subject}" + Style.RESET_ALL)
        print(Fore.CYAN + "内容:" + Style.RESET_ALL)
        print(current_email.body)
        print(Fore.CYAN + "===========\n" + Style.RESET_ALL)
        
        result = self.agents.categorize_email().invoke({"email": current_email.body})
        print(Fore.MAGENTA + f"Email category: {result.category.value}" + Style.RESET_ALL)
        
        return {
            "email_category": result.category.value,
            "current_email": current_email
        }

    def route_email_based_on_category(self, state: GraphState) -> str:
        """Routes the email based on its category."""
        print(Fore.YELLOW + "Routing email based on category...\n" + Style.RESET_ALL)
        category = state["email_category"]
        if category == "other":
            return "unrelated"
        else:
            return "academic"

    def construct_rag_queries(self, state: GraphState) -> GraphState:
        """Constructs RAG queries based on the email content."""
        print(Fore.YELLOW + "Designing RAG query...\n" + Style.RESET_ALL)
        email_content = state["current_email"].body
        query_result = self.agents.design_rag_queries().invoke({"email": email_content})
        print(Fore.MAGENTA + f"RAG queries: {query_result.queries}" + Style.RESET_ALL) #* test
        return {"rag_queries": query_result.queries}

    def retrieve_from_rag(self, state: GraphState) -> GraphState:
        """Retrieves information from internal knowledge based on RAG questions."""
        print(Fore.YELLOW + "Retrieving information from internal knowledge...\n" + Style.RESET_ALL)
        
        print(Fore.CYAN + f"\n=== RAG检索 {len(state['rag_queries'])} 个查询 ===" + Style.RESET_ALL)
        
        final_answer = ""
        for i, query in enumerate(state["rag_queries"]):
            rag_result = self.agents.generate_rag_answer().invoke(query)
            final_answer += query + "\n" + rag_result + "\n\n"
            print(f"Query {i+1} processed")
        
        print(f"检索内容长度: {len(final_answer)} 字符")
        print(Fore.CYAN + "==================\n" + Style.RESET_ALL)
        
        return {"retrieved_documents": final_answer}

    def write_draft_email(self, state: GraphState) -> GraphState:
        """Writes a draft email based on the current email and retrieved information."""
        print(Fore.YELLOW + "Writing draft email...\n" + Style.RESET_ALL)
        
        # Format input to the writer agent
        inputs = (
            f'# **EMAIL CATEGORY:** {state["email_category"]}\n\n'
            f'# **EMAIL CONTENT:**\n{state["current_email"].body}\n\n'
            f'# **INFORMATION:**\n{state["retrieved_documents"]}' # Empty for feedback or complaint
        )
        
        # Get messages history for current email
        writer_messages = state.get('writer_messages', [])
        
        # 调试: 打印关键信息
        print(Fore.CYAN + f"\n=== Email Writer输入摘要 ===" + Style.RESET_ALL)
        print(f"Category: {state['email_category']}")
        print(f"History items: {len(writer_messages)}")
        print(Fore.CYAN + "========================\n" + Style.RESET_ALL)
        
        # Write email
        try:
            draft_result = self.agents.email_writer().invoke({
                "email_information": inputs,
                "history": writer_messages
            })
            
            # 调试: 打印writer返回结果类型
            print(Fore.CYAN + f"Email Writer结果类型: {type(draft_result)}" + Style.RESET_ALL)
            
            if draft_result is None:
                print(Fore.RED + "Error: Email writer returned None" + Style.RESET_ALL)
                return {
                    "generated_email": "Error: Failed to generate email", 
                    "trials": state.get('trials', 0) + 1,
                    "writer_messages": writer_messages
                }
            
            if not hasattr(draft_result, 'email'):
                print(Fore.RED + f"Error: Draft result has no 'email' attribute. Type: {type(draft_result)}" + Style.RESET_ALL)
                print(Fore.RED + f"Draft result: {draft_result}" + Style.RESET_ALL)
                # 尝试直接访问所有属性
                print(Fore.YELLOW + f"Available attributes: {dir(draft_result)}" + Style.RESET_ALL)
                return {
                    "generated_email": "Error: Invalid draft result format", 
                    "trials": state.get('trials', 0) + 1,
                    "writer_messages": writer_messages
                }
            
            email = draft_result.email #! WriterOutput.email
            trials = state.get('trials', 0) + 1 #!
            
        except Exception as e:
            print(Fore.RED + f"Error writing email: {e}" + Style.RESET_ALL)
            return {
                "generated_email": "Error: Exception occurred during email generation", 
                "trials": state.get('trials', 0) + 1,
                "writer_messages": writer_messages
            } 

        # 打印生成的邮件草稿
        print(Fore.GREEN + "\n=== 生成的邮件草稿 ===" + Style.RESET_ALL)
        print(email)
        print(Fore.GREEN + "===========\n" + Style.RESET_ALL)

        # Append writer's draft to the message list
        writer_messages.append(f"**Draft {trials}:**\n{email}")

        return {
            "generated_email": email, 
            "trials": trials,
            "writer_messages": writer_messages
        }

    def verify_generated_email(self, state: GraphState) -> GraphState:
        """Verifies the generated email using the proofreader agent."""
        print(Fore.YELLOW + "Verifying generated email...\n" + Style.RESET_ALL)
        
        try:
            review = self.agents.email_proofreader().invoke({
                "initial_email": state["current_email"].body,
                "generated_email": state["generated_email"],
            })
            
            if review is None:
                print(Fore.RED + "Error: Email proofreader returned None" + Style.RESET_ALL)
                return {
                    "sendable": False,
                    "writer_messages": state.get('writer_messages', [])
                }
            
            if not hasattr(review, 'send') or not hasattr(review, 'feedback'):
                print(Fore.RED + f"Error: Review result has missing attributes. Type: {type(review)}" + Style.RESET_ALL)
                print(Fore.RED + f"Review result: {review}" + Style.RESET_ALL)
                return {
                    "sendable": False,
                    "writer_messages": state.get('writer_messages', [])
                }

            writer_messages = state.get('writer_messages', [])
            writer_messages.append(f"**Proofreader Feedback:**\n{review.feedback}")

            return {
                "sendable": review.send,
                "writer_messages": writer_messages
            }
                
        except Exception as e:
            print(Fore.RED + f"Error verifying email: {e}" + Style.RESET_ALL)
            return {
                "sendable": False,
                "writer_messages": state.get('writer_messages', [])
            }

    def must_rewrite(self, state: GraphState) -> str:
        """Determines if the email needs to be rewritten based on the review and trial count."""
        email_sendable = state["sendable"]
        if email_sendable:
            print(Fore.GREEN + "Email is good, ready to be sent!!!" + Style.RESET_ALL)
            state["emails"].pop()
            state["writer_messages"] = []
            return "send"
        elif state["trials"] >= 3:
            print(Fore.RED + "Email is not good, we reached max trials must stop!!!" + Style.RESET_ALL)
            state["emails"].pop()
            state["writer_messages"] = []
            return "stop"
        else:
            print(Fore.RED + "Email is not good, must rewrite it..." + Style.RESET_ALL)
            return "rewrite"

    def create_draft_response(self, state: GraphState) -> GraphState:
        """Creates a draft response."""
        print(Fore.YELLOW + "Creating draft email...\n" + Style.RESET_ALL)
        self.email_tools.create_draft_reply(state["current_email"], state["generated_email"])
        
        return {"retrieved_documents": "", "trials": 0}

    def send_email_response(self, state: GraphState) -> GraphState:
        """Sends the email response directly."""
        print(Fore.YELLOW + "Sending email...\n" + Style.RESET_ALL)
        self.email_tools.send_reply(state["current_email"], state["generated_email"])
        
        return {"retrieved_documents": "", "trials": 0}
    
    def skip_unrelated_email(self, state):
        """Skip unrelated email and remove from emails list."""
        print("Skipping unrelated email...\n")
        state["emails"].pop()
        return state