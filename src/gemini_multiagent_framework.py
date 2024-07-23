import uuid
from typing import List, Dict, Any
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv
from typing import Callable

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Global generation config
GENERATION_CONFIG = {
    "temperature": 1,
    "top_k": 64,
    "max_output_tokens": 1000,
    "response_mime_type": "text/plain",
}

class Agent:
    def __init__(self, name: str, system_instruction: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.system_instruction = system_instruction
        self.memory: List[Dict[str, Any]] = [] # Memory should be overridden in the subclass

    # TO BE OVERRIDDEN
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("process_message method must be implemented in the subclass")


    def send_message(self, recipient: 'Agent', content: str):
        return recipient.process_message(content)

class GeminiAgent(Agent):
    def __init__(self, name: str, system_instruction: str, end_condition = False, tools = []):
        super().__init__(name, system_instruction)
        self.model = self.create_gemini_model(tools=tools, system_instruction=system_instruction)
        self.chat_session = self.model.start_chat(enable_automatic_function_calling=True)
        self.memory = self.chat_session.history
        self.end_condition = end_condition

    def create_gemini_model(self, tools, system_instruction: str = ""):
        return genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=GENERATION_CONFIG,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
            system_instruction=system_instruction,
            tools=tools,
        )
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        # Append user message to history
        self.chat_session.history.append({
            "role": "user",
            "parts": [message],
        })
        
        response = self.chat_session.send_message(message)
        
        # Append model response to history
        self.chat_session.history.append({
            "role": "model",
            "parts": [response.text],
        })
        
        return response.text

class UserAgent(Agent):
    def __init__(self, name: str, system_instruction: str):
        super().__init__(name, system_instruction)
        self.memory = []

    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        # Append user message to history
        print("Do nothing for now")
    
    def send_message(self, recipient: 'Agent', content: str):
        input_content = input(content)
        print("[user]",input_content)
        message = input_content
        # Append user message to memory
        self.memory.append({
            "role": "user",
            "parts": [input_content],
        })
        return recipient.process_message(message)

class Mediator:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.agents["user"] = UserAgent("User", "") # Add an user agent as a default agent

    def add_agent(self, agent: Agent):
        self.agents[agent.id] = agent

    def get_agent(self, agent_id: str) -> Agent:
        return self.agents.get(agent_id)

    def send(self, sender_id: str, recipient_id: str, content: str):
        sender = self.get_agent(sender_id)
        recipient = self.get_agent(recipient_id)
        if sender and recipient:
            return sender.send_message(recipient, content)
        else:
            raise ValueError("Invalid sender or recipient ID")
    
    def chat(self, sender_id: str, recipient_id: str, content: str, str_condition: str = "", max_turns: int = 4):
        sender = self.get_agent(sender_id)
        recipient = self.get_agent(recipient_id)
        res_recipient = content
        res_sender = " "
        counter = 0
        end = False
    
        # Repeat for max_turns or until recipient.end_condition is true
        while counter < max_turns and not end:
            res_recipient = self.send(sender_id, recipient_id, res_recipient if counter == 0 else res_sender)
            print(f'[{recipient.name}]', res_recipient)
            if str_condition and str_condition in res_recipient:
                break
            
            if callable(recipient.end_condition):
                # Check if receiver has a function as end_condition
                end = recipient.end_condition()
            
            if end:
                break
                
            res_sender = self.send(recipient_id, sender_id, res_recipient)
            print(f'[{sender.name}]', res_sender)
            if str_condition and str_condition in res_sender:
                break

            # Check if receiver has a function as end_condition
            if callable(sender.end_condition):
                end = sender.end_condition()
                
            counter += 1
        
        return res_sender
    
    def user_chat(self, sender_id: str, recipient_id: str, hint: str="Write your message", str_condition: str = "",  max_turns: int = 4):
        sender = self.get_agent(sender_id)
        res_sender = self.send("user", sender_id, hint)
        print(f'[{sender.name}]', res_sender)
        res = self.chat(sender_id, recipient_id, content=res_sender, str_condition=str_condition, max_turns=4)
        return res
    
    def conductor_chat(self, sender_id: str, recipient_id: str, conductor_id: str, content: str, hint: str="Write your message", max_turns: int = 4, independent: bool = False):
        # Validate agents
        sender = self.get_agent(sender_id)
        recipient = self.get_agent(recipient_id)
        conductor = self.get_agent(conductor_id)
        if not sender or not recipient or not conductor:
            raise ValueError("Invalid sender, recipient, or conductor ID")
        counter = 0
        
        res_sender = self.send(conductor_id, sender_id, content=content) # coductor_id is irrelevant
        print(f'[{sender.name}]', res_sender)
        res = res_sender

        while counter < max_turns:
            # Chat operations
            res_filtered_sender = self.chat(sender_id, conductor_id, res, max_turns=max_turns)
            res_filtered_recipient = self.chat(conductor_id, recipient_id, res_filtered_sender, max_turns=max_turns)
            
            # Update response based on the independent flag
            res = " " if independent else res_filtered_recipient

            counter += 1
            print(f"turn {counter}")