import json
import os
from typing import Literal
from engine.gpt import GPTEngine
from sp_data import Sp_data

class SP:
    def __init__(self, data: Sp_data, engine):
        self.data = data
        self.engine = engine
        self.set_system_message()
        self.memories = [{"role": "user", "content": self.system_message}]

    def set_system_message(self):
        self.system_message = f"""
        1.你应当进行角色扮演，扮演一个标准化的病人，按照病历和基本资料的设定进行对话，稍微简短一些。你的疾病为{self.data.disease}，你应该适当演出真实症状，但绝不能直接说出自己的疾病\n
        2.你的基本信息如下
        {self.data.basics}\n
        3.你应该主动表达自己的主诉，在医生询问后，也应该强调自己的主诉。主诉如下：
        {self.data.symptoms}\n
        4.仅当医生的问题与对应隐藏信息有关，你才能说出自己对应的隐藏信息。医生问题和隐藏信息的对应关系如下：
        {self.data.hiddens}\n
        5.你的相关个人特质如下，请模仿这些特质进行对话，但不要模仿过度。尽量简短的回答，减少每次重复的话
        {self.data.personalities}\n
        """

    def memorize(self, message: str, role: Literal['user', 'assistant']):
        self.memories.append({"role": role, "content": message})

    def speak(self, message):
        self.memorize(message, "user")
        response = self.engine.get_response(self.memories)
        self.memorize(response, "assistant")
        return response


if __name__ == "__main__":
    sp_data = Sp_data()
    sp_data.load_from_json("presets/test.json")

    sp = SP(sp_data, GPTEngine())
    while True:
        user_input = input("你: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = sp.speak(user_input)
        print(f"病人: {response}")
    print(f"对话记录: {sp.memories[:]}")
