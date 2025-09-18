"""
评分系统模块
基于隐藏问题的医学问诊评分
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class QuestionItem:
    """单个隐藏问题项目"""
    
    def __init__(self, question: str, weight: float = 1.0, category: str = "general", 
                 keywords: List[str] = None, description: str = ""):
        self.question = question
        self.weight = weight  # 权重，用于计算总分
        self.category = category  # 问题分类（如：病史、体格检查、症状等）
        self.keywords = keywords or []  # 关键词，用于判断是否被问到
        self.description = description  # 问题描述
        self.is_asked = False  # 是否被问到
        self.asked_messages = []  # 问到这个问题的对话记录
    
    def check_if_asked(self, message: str) -> bool:
        """检查消息是否涉及此问题"""
        message_lower = message.lower()
        
        # 检查问题本身是否在消息中
        if self.question.lower() in message_lower:
            return True
        
        # 检查关键词
        for keyword in self.keywords:
            if keyword.lower() in message_lower:
                return True
        
        return False
    
    def mark_as_asked(self, message: str):
        """标记问题被问到"""
        if not self.is_asked:
            self.is_asked = True
        self.asked_messages.append(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "question": self.question,
            "weight": self.weight,
            "category": self.category,
            "keywords": self.keywords,
            "description": self.description,
            "is_asked": self.is_asked,
            "asked_messages": self.asked_messages
        }


class ScoringSystem:
    """评分系统核心类"""
    
    def __init__(self, case_data: Dict[str, Any]):
        self.case_data = case_data
        self.question_items: List[QuestionItem] = []
        self.total_weight = 0
        self.conversation_history = []
        self._initialize_questions()
    
    def _initialize_questions(self):
        """根据病例数据初始化隐藏问题"""
        hidden_questions = self.case_data.get("hidden_questions", [])
        
        for item in hidden_questions:
            if isinstance(item, str):
                # 简单字符串格式
                question_item = QuestionItem(
                    question=item,
                    weight=1.0,
                    category="general"
                )
            elif isinstance(item, dict):
                # 详细字典格式
                question_item = QuestionItem(
                    question=item.get("question", ""),
                    weight=item.get("weight", 1.0),
                    category=item.get("category", "general"),
                    keywords=item.get("keywords", []),
                    description=item.get("description", "")
                )
            else:
                continue
            
            self.question_items.append(question_item)
            self.total_weight += question_item.weight
    
    def process_message(self, message: str, role: str = "user"):
        """处理对话消息，检查是否涉及隐藏问题"""
        # 记录对话历史
        self.conversation_history.append({
            "role": role,
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # 只处理用户（医生）的消息
        if role == "user":
            for question_item in self.question_items:
                if question_item.check_if_asked(message):
                    question_item.mark_as_asked(message)
    
    def calculate_score(self) -> Dict[str, Any]:
        """计算评分结果"""
        if self.total_weight == 0:
            return {
                "total_score": 100,
                "percentage": 100,
                "message": "没有隐藏问题，满分"
            }
        
        asked_weight = sum(item.weight for item in self.question_items if item.is_asked)
        percentage = (asked_weight / self.total_weight) * 100
        
        # 按分类统计
        category_stats = {}
        for item in self.question_items:
            if item.category not in category_stats:
                category_stats[item.category] = {
                    "total_questions": 0,
                    "asked_questions": 0,
                    "total_weight": 0,
                    "asked_weight": 0
                }
            
            category_stats[item.category]["total_questions"] += 1
            category_stats[item.category]["total_weight"] += item.weight
            
            if item.is_asked:
                category_stats[item.category]["asked_questions"] += 1
                category_stats[item.category]["asked_weight"] += item.weight
        
        # 计算各分类的完成率
        for category, stats in category_stats.items():
            if stats["total_weight"] > 0:
                stats["completion_rate"] = (stats["asked_weight"] / stats["total_weight"]) * 100
            else:
                stats["completion_rate"] = 100
        
        return {
            "total_score": round(percentage, 2),
            "percentage": round(percentage, 2),
            "asked_questions": len([item for item in self.question_items if item.is_asked]),
            "total_questions": len(self.question_items),
            "asked_weight": asked_weight,
            "total_weight": self.total_weight,
            "category_stats": category_stats,
            "evaluation": self._get_evaluation(percentage)
        }
    
    def _get_evaluation(self, percentage: float) -> Dict[str, str]:
        """根据得分给出评价"""
        if percentage >= 90:
            level = "优秀"
            comment = "问诊非常全面，几乎涵盖了所有重要问题"
        elif percentage >= 80:
            level = "良好"
            comment = "问诊较为全面，涵盖了大部分重要问题"
        elif percentage >= 70:
            level = "中等"
            comment = "问诊基本合格，但还有一些重要问题遗漏"
        elif percentage >= 60:
            level = "及格"
            comment = "问诊不够全面，遗漏了较多重要问题"
        else:
            level = "不及格"
            comment = "问诊严重不足，需要大幅改进"
        
        return {
            "level": level,
            "comment": comment
        }
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """获取详细评分报告"""
        score_result = self.calculate_score()
        
        # 未问到的问题
        missed_questions = []
        asked_questions = []
        
        for item in self.question_items:
            item_dict = item.to_dict()
            if item.is_asked:
                asked_questions.append(item_dict)
            else:
                missed_questions.append(item_dict)
        
        return {
            "score_summary": score_result,
            "asked_questions": asked_questions,
            "missed_questions": missed_questions,
            "conversation_count": len([msg for msg in self.conversation_history if msg["role"] == "user"]),
            "report_time": datetime.now().isoformat(),
            "case_info": {
                "patient_name": self.case_data.get("basics", {}).get("name", "Unknown"),
                "chief_complaint": self.case_data.get("chief_complaint", ""),
                "diagnosis": self.case_data.get("diagnosis", {})
            }
        }
    
    def get_suggestions(self) -> List[str]:
        """获取改进建议"""
        suggestions = []
        missed_questions = [item for item in self.question_items if not item.is_asked]
        
        if not missed_questions:
            suggestions.append("问诊非常全面，没有遗漏重要问题！")
            return suggestions
        
        # 按分类给出建议
        category_missed = {}
        for item in missed_questions:
            if item.category not in category_missed:
                category_missed[item.category] = []
            category_missed[item.category].append(item.question)
        
        for category, questions in category_missed.items():
            if len(questions) == 1:
                suggestions.append(f"建议询问{category}相关问题：{questions[0]}")
            else:
                suggestions.append(f"建议完善{category}相关问题，包括：{', '.join(questions[:3])}" + 
                                ("等" if len(questions) > 3 else ""))
        
        return suggestions


class ScoringManager:
    """评分管理器，提供统一的接口"""
    
    def __init__(self):
        self.active_sessions = {}  # session_id -> ScoringSystem
    
    def create_session(self, session_id: str, case_data: Dict[str, Any]):
        """创建评分会话"""
        scoring_system = ScoringSystem(case_data)
        self.active_sessions[session_id] = scoring_system
        return scoring_system
    
    def get_session(self, session_id: str) -> Optional[ScoringSystem]:
        """获取评分会话"""
        return self.active_sessions.get(session_id)
    
    def process_message(self, session_id: str, message: str, role: str = "user"):
        """处理消息"""
        scoring_system = self.get_session(session_id)
        if scoring_system:
            scoring_system.process_message(message, role)
    
    def get_score_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取评分报告"""
        scoring_system = self.get_session(session_id)
        if scoring_system:
            return scoring_system.get_detailed_report()
        return None
    
    def delete_session(self, session_id: str):
        """删除评分会话"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]


# 全局评分管理器实例
scoring_manager = ScoringManager()
