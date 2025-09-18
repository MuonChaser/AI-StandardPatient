import os

class PromptLoader:
    @staticmethod
    def load_prompt(prompt_path: str, context: dict) -> str:
        """
        加载prompt文件并用context填充
        """
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
        # 用 context 替换 {xxx} 占位符
        for k, v in context.items():
            if isinstance(v, dict):
                v_str = str(v)
            else:
                v_str = v
            prompt = prompt.replace(f'{{{k}}}', str(v_str))
        return prompt
