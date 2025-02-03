
from openai import OpenAI

import os
from dotenv import load_dotenv
from tell_stories_api.logs import logger


class QwenAPI:
    def __init__(self, model="qwen-plus"):
        # Load environment variables from .env file
        load_dotenv()
        # Get the value of the API key from the environment variable
        api_key = os.getenv("DASHSCOPE_API_KEY")
        base_url = os.getenv("DASHSCOPE_BASE_URL")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def format_history(self, history):
        history_zhipuai_format = []
        for human, assistant in history:
            history_zhipuai_format.append({"role": "user", "content": human})
            history_zhipuai_format.append({"role": "assistant", "content": assistant})
        return history_zhipuai_format

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
        Predict using sse and stream is true
        """
        history.append({"role": "user", "content": message})
        logger.debug(f"history: {history}")

        # Retry 3 times if bumped into Error; if exceeds, then throw error
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
        Predict using sse and stream is true
        """
        history = self.format_history(history)
        history.append({"role": "user", "content": message})
        logger.debug(f"history: {history}")

        # Retry 3 times if bumped into Error; if exceeds, then throw error
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
        return response.choices[0].message, total_tokens, response.choices[0].finish_reason
    
    def predict_sse(self, message, history=[]):
        """
        Predict using sse and stream is true
        """
        history_zhipuai_format = self.format_history(history)
        history_zhipuai_format.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=history_zhipuai_format,
            stream=True
        )

        partial_message = ""
        for chunk in response:
            if len(chunk.choices[0].delta.content) != 0:
                partial_message = partial_message + chunk.choices[0].delta.content
                yield partial_message

        # self.record_usage(response=response)
        return partial_message

