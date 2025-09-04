from .openai_agent import OpenAIAgent

class OpenRouterAgent(OpenAIAgent):
    def _initialize_client(self):
        import openai
        return openai.Client(
            api_key=self.config.api_key,
            base_url="https://openrouter.ai/api/v1"
        )