import uuid
from typing import List, Dict, Any
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

class Agent:
    def __init__(self, name: str, system_instruction: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.system_instruction = system_instruction
        self.memory: List[Dict[str, Any]] = []  # Memory should be overridden in the subclass

    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("process_message method must be implemented in the subclass")

    def send_message(self, recipient: 'Agent', content: str):
        return recipient.process_message(content)

class OpenAIAgent(Agent):
    def __init__(self, name: str, system_instruction: str, model="gpt-4o-mini"):
        super().__init__(name, system_instruction)
        self.model = model
        self.input_tokens = 0
        self.total_tokens = 0
        self.completion_tokens = 0
        self.api_calls = 0
        self.chat_history = [
            {"role": "system", "content": system_instruction}
        ]

    def process_message(self, message: str) -> str:
        # Append user message to chat history
        self.chat_history.append({
            "role": "user",
            "content": message,
        })
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[ {"role": "system", "content": self.system_instruction},
                       {"role": "user", "content": message} ]
        )
        self.api_calls += 1
        self.input_tokens += response.usage.prompt_tokens
        self.total_tokens += response.usage.total_tokens
        self.completion_tokens += response.usage.completion_tokens
        # Extract and append model response to chat history
        response_text = response.choices[0].message.content
        
        self.chat_history.append({
            "role": "assistant",
            "content": response_text,
        })
        
        return response_text
    

