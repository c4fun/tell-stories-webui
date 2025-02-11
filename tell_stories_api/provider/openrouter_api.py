from openai import OpenAI
import os
from dotenv import load_dotenv
from tell_stories_api.logs import logger


class OpenRouterAPI:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        # Get API credentials from environment variables
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("OPENROUTER_BASE_URL")
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = "deepseek/deepseek-chat"  # Default model

    def format_history(self, history):
        """
        Format the history for OpenRouter API
        """
        formatted_history = []
        for human, assistant in history:
            formatted_history.append({"role": "user", "content": human})
            formatted_history.append({"role": "assistant", "content": assistant})
        return formatted_history

    def record_usage(self, response):
        """
        Record the usage of the response
        """
        usage = response.usage
        logger.info(f"prompt_tokens usage: {usage.prompt_tokens}")
        logger.info(f"completion_tokens usage: {usage.completion_tokens}")
        logger.info(f"total_tokens usage: {usage.total_tokens}")

    def predict_with_history(self, message, history=[]):
        """
        Predict using history in raw format
        """
        history.append({"role": "user", "content": message})
        logger.debug(f"history: {history}")

        for i in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=history,
                    stream=False
                )
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                if i == 2:
                    raise e

        self.record_usage(response=response)
        total_tokens = response.usage.total_tokens
        return response.choices[0].message, total_tokens

    def predict(self, message, history=[]):
        """
        Predict using formatted history
        """
        formatted_history = self.format_history(history)
        formatted_history.append({"role": "user", "content": message})

        for i in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_history,
                    stream=False
                )
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                if i == 2:
                    raise e

        self.record_usage(response=response)
        total_tokens = response.usage.total_tokens
        return response.choices[0].message, total_tokens

    def predict_v3(self, message, history=[]):
        """
        Predict with finish reason
        """
        formatted_history = self.format_history(history)
        formatted_history.append({"role": "user", "content": message})
        
        logger.info(f"formatted_history: {formatted_history}")
        
        for i in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_history,
                    stream=False
                )
                logger.info(f"response: {response}")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                if i == 2:
                    raise e

        self.record_usage(response=response)
        total_tokens = response.usage.total_tokens
        return response.choices[0].message, total_tokens, response.choices[0].finish_reason

    def predict_sse(self, message, history=[]):
        """
        Predict using server-sent events (streaming)
        """
        formatted_history = self.format_history(history)
        formatted_history.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_history,
            stream=True
        )

        partial_message = ""
        for chunk in response:
            if len(chunk.choices[0].delta.content) != 0:
                partial_message = partial_message + chunk.choices[0].delta.content
                yield partial_message

        return partial_message


if __name__ == '__main__':
    openrouter = OpenRouterAPI()
    message = "What is the capital of France?"
    response, total_tokens, finish_reason = openrouter.predict_v3(message)
    print(response.content)
    print(total_tokens)
    print("Done")
