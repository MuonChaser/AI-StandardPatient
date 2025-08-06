

import json

from typing import List, Literal


class Sp_data:
    def __init__(self):
        # 应该有：基本信息，检测指标，隐含信息
        self._basics = []     # 基本信息
        self._disease = ""  # 疾病名称
        self._symptoms = []
        self._hiddens = []
        self._examinations = []
        self._personalities = []
    
    @property
    def basics(self) -> List[tuple[str, str]]:
        return self._basics
    @basics.setter
    def basics(self, value: List[tuple[str, str]]):
        self._basics = value
    
    @property
    def disease(self) -> str:
        return self._disease
    @disease.setter
    def disease(self, value: str):
        self._disease = value
    
    @property
    def symptoms(self) -> List[str]:
        return self._symptoms
    @symptoms.setter
    def symptoms(self, value: List[str]):
        self._symptoms = value

    @property
    def hiddens(self) -> List[tuple[str, str]]:
        return self._hiddens
    @hiddens.setter
    def hiddens(self, value: List[tuple[str, str]]):
        self._hiddens = value
    
    @property
    def personalities(self) -> List[str]:
        return self._personalities
    @personalities.setter
    def personalities(self, value: List[str]):
        self._personalities = value

    @property
    def examinations(self) -> List[tuple[str, str]]:
        return self._examinations
    @examinations.setter
    def examinations(self, value: List[tuple[str, str]]):
        self._examinations = value
    


    def load_from_json(self, json_path: str):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.basics = data.get("basics", [])
        self.disease = data.get("disease", "")
        self.symptoms = data.get("symptoms", [])
        self.hiddens = data.get("hiddens", [])
        self.personalities = data.get("personalities", [])
        self.examinations = data.get("examinations", [])

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False, indent=2)
    
if __name__ == "__main__":
    sp_data = Sp_data()
    sp_data.basics = [('name', '张三'), ('性别', '男'), ('年龄', '30')]
    sp_data.disease = "感冒"
    sp_data.symptoms = ['头痛', '发热']
    sp_data.hiddens = [('发热细节', '每次都在37.2度'),('过敏史', '对大多数疫苗过敏'), ('家族史', '家族有高血压，男性亲属都有高血压'), ('生活习惯', '吸烟，偶尔饮酒')]
    sp_data.personalities = ["文化水平低，不懂得医生的专业表述，不理解就反复发问", "在百度上查过一些症状，认为自己得了重病，不相信医生的诊断", "情绪容易激动，喜欢夸大自己的症状"]
    print(sp_data.disease)