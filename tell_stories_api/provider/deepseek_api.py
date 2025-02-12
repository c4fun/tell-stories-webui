
from openai import OpenAI

import os
from dotenv import load_dotenv
from tell_stories_api.logs import logger


class DeepSeekAPI:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        # Get the value of the API key from the environment variable
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL")
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def format_history(self, history):
        """
        Format the history for deepseek API
        """
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
                    model='deepseek-chat',
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
        history_zhipuai_format = self.format_history(history)
        history_zhipuai_format.append({"role": "user", "content": message})

        # Retry 3 times if bumped into Error; if exceeds, then throw error
        for i in range(3):
            try:
                response = self.client.chat.completions.create(
                    model='deepseek-chat',
                    messages=history_zhipuai_format,
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
        Predict using sse and stream is true
        """
        history_zhipuai_format = self.format_history(history)
        history_zhipuai_format.append({"role": "user", "content": message})

        logger.info(f"history_zhipuai_format: {history_zhipuai_format}")
        # Retry 3 times if bumped into Error; if exceeds, then throw error
        for i in range(3):
            try:
                # 不知道为啥加了这个参数 max_tokens=8192, deepseek经常返回错误的信息，所以暂时去掉了。
                response = self.client.chat.completions.create(
                    model='deepseek-chat',
                    messages=history_zhipuai_format,
                    max_tokens=8192,
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
        Predict using sse and stream is true
        """
        history_zhipuai_format = self.format_history(history)
        history_zhipuai_format.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model='deepseek-chat',
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

story = '''
The splendor before my eyes left me breathless, a vaulted ceiling painted with scenes from an ancient tale; tapestries that stretched across three walls depicting tales of heroes long dead.
However, as fate would have it, I was thoroughly distracted by the flurry of magic explosions obliterating my vision every time a magic spell hit its target: the dragon. After all, I was a mere human in the company of two magical beings, my companion Galena, a witch, and a fearsome crystal dragon. My presence here was not only an honor but also a grave danger.
"You know what to do, right?!" Galena shouted at me as she threw another fireball at the dragon's head.
I had been tasked with assisting Galena on this quest to save the world from the evil of a dragon. But how could I possibly help? 
"Do something!" Galena shouted at me while she threw her spells.
But what could I do? All I could do was watch the battle. And then a thought came to mind: What if there was another way?
The dragon said something: "You fool! You think you can kill me?! I will live forever!!"
Galena threw another spell. This one was stronger than the others. She must have felt confident in its strength because she started to walk forward.
As the witch approached the dragon, I could see that her confidence was misplaced. The dragon wasn't hurt.
"Foolish witch! Did you really think your pitiful spells would hurt me?"
Galena stunned. "No... it can't be!"
"Hahahahaha! Now it is my turn." The dragon let out a huge breath.
Fire!
A wall of flames surrounded the witch. She had no way to escape.
"NOOOOOO!!!"
"Galena!!!" I shouted.
The witch screamed. Then she fell to the ground and didn't move.
'''

message = '''
Analyze this story below, and see how many voice actors/actresses I need to read it. There are the rules:
1. Assign character for each VA, must include following properties according to the content:
  1.1 language(English, Chinese, Cantonese, Spanish, Japanese),
  1.2 gender(male, female),
  1.3 type(narration, action),
  1.4 age(child, teen, young adult, middle-aged, senior, monster),
  1.5 pitch(very high, high, medium, low, very low)
2. Don't dissect the narrator's line into smaller sections if they are sequential.
3. A character's line should only contain what the charater himself/herself said. Words like "he said/she said" are said by the narrator.
4. The narrator should also count as a character.
5. Output all things in JSON format as following. Do not output any extra explanations, just output the JSON itself.
{
	"characters": {
	  "count": 2,
	  "list": [
	    "Narrator": {
	      "language": "English",
	      "gender": "female",
	      "type": "narration",
	      "age": "middle-aged",
	      "pitch": "low"
	    },
	    "The little match girl": {
	      "language": "English",
	      "gender": "female",
	      "type": "action",
	      "age": "child",
	      "pitch": "high"
	    }
	  ]
	},
	"lines": [
	  {
	    "character": "Narrator",
	    "line": "It was late at night. The wind is howling fiercely."
	  },
	  {
	    "character": "The little match girl",
	    "line": "It's so cold!"
	  },
	]
}

Here's the story:
''' + story


if __name__ == '__main__':
    deepseek = DeepSeekAPI()
    message = """
What is the capital of France?
"""
    # response, total_tokens = deepseek.predict(message)
    response, total_tokens, finish_reason = deepseek.predict_v3(message)
    print(response)  # ChatCompletionMessage(content=' The capital of France is Paris.', role='assistant', function_call=None, tool_calls=None)
    print(response.content)
    print(total_tokens)
    print("Done")
