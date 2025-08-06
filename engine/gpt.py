from openai import OpenAI
from .base_engine import Engine
import os

class GPTEngine(Engine):
    
    def __init__(self, model_name=None, model_base=None, streaming=False):
       
        super().__init__()

        
        self._model_name = model_name or os.getenv("MODEL_NAME", "gpt-4o-mini")
        self._model_base = model_base or os.getenv("MODEL_BASE", "https://xiaoai.plus/v1")
        self._api_key = os.getenv("API_KEY")
        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._model_base,
        )
    
    def get_response(self, memories):
        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=memories,
        )

        return response.choices[0].message.content
    
  
if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = "sk-pkas0IqXTrYRK17XxTu7sLxW3yAtPvHxuVzj6n4usoMpD6E8"
    gpt_engine = GPTEngine()
    print(gpt_engine.get_response([{"role": "user", "content": "Hello, how are you?"}]))