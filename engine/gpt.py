from openai import OpenAI
from .base_engine import Engine
import os
import time

class GPTEngine(Engine):
    
    def __init__(self, model_name=None, model_base=None, streaming=False, timeout=30):
       
        super().__init__()

        
        self._model_name = model_name or os.getenv("MODEL_NAME", "deepseek-chat")
        self._model_base = model_base or os.getenv("MODEL_BASE", "https://api.deepseek.com")
        self._api_key = os.getenv("API_KEY", "sk-d3ed372f11114bbeaf9bedfc7cdc0d60")
        self._timeout = timeout
        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._model_base,
            timeout=self._timeout  # 添加超时设置
        )
    
    def get_response(self, memories):
        """获取AI响应（带性能优化）"""
        start_time = time.time()
        
        try:
            # 限制对话历史长度以提升性能
            max_history = 20  # 最多保留20轮对话
            if len(memories) > max_history:
                # 保留系统消息和最近的对话
                system_msg = memories[0] if memories and memories[0].get("role") == "system" else None
                recent_memories = memories[-max_history:]
                if system_msg and recent_memories[0].get("role") != "system":
                    memories = [system_msg] + recent_memories
                else:
                    memories = recent_memories
            
            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=memories,
                timeout=self._timeout
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 记录性能日志（如果响应时间过长）
            if response_time > 5.0:
                print(f"⚠️ 慢响应警告: AI调用耗时 {response_time:.2f}秒")
            elif response_time > 10.0:
                print(f"❌ 极慢响应: AI调用耗时 {response_time:.2f}秒")
            
            return response.choices[0].message.content
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            print(f"❌ AI调用失败 (耗时{response_time:.2f}s): {e}")
            raise e
    
  
if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = "sk-pkas0IqXTrYRK17XxTu7sLxW3yAtPvHxuVzj6n4usoMpD6E8"
    gpt_engine = GPTEngine()
    print(gpt_engine.get_response([{"role": "user", "content": "Hello, how are you?"}]))