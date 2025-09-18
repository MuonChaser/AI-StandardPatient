

import json

from typing import List, Literal



class Sp_data:
    def __init__(self):
        self.data = {}

    def load_from_json(self, json_path: str):
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    # 兼容旧属性，推荐直接用 self.data['xxx']
    @property
    def basics(self):
        return self.data.get("basics", {})
    @basics.setter
    def basics(self, value):
        self.data["basics"] = value

    @property
    def disease(self):
        # 支持新旧字段
        return self.data.get("disease") or self.data.get("diagnosis", {}).get("primary", "")
    @disease.setter
    def disease(self, value):
        self.data["disease"] = value

    @property
    def symptoms(self):
        return self.data.get("symptoms", [])
    @symptoms.setter
    def symptoms(self, value):
        self.data["symptoms"] = value

    @property
    def hiddens(self):
        # 新格式为 hidden_questions
        return self.data.get("hidden_questions", [])
    @hiddens.setter
    def hiddens(self, value):
        self.data["hidden_questions"] = value

    @property
    def personalities(self):
        return self.data.get("personalities", [])
    @personalities.setter
    def personalities(self, value):
        self.data["personalities"] = value

    @property
    def examinations(self):
        # 新格式为 physical_exam + auxiliary_exam
        exams = []
        if "physical_exam" in self.data:
            exams.append(self.data["physical_exam"])
        if "auxiliary_exam" in self.data:
            exams.append(self.data["auxiliary_exam"])
        return exams
    @examinations.setter
    def examinations(self, value):
        self.data["examinations"] = value

    def __str__(self):
        return json.dumps(self.data, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    sp_data = Sp_data()
    sp_data.load_from_json("presets/test.json")
    print(sp_data)