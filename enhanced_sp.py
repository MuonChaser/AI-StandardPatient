"""
增强的标准化病人类
集成智能评分系统和模块化设计
"""

import os
from typing import Literal, Dict, Any, Optional, List
from engine.gpt import GPTEngine
from sp_data import Sp_data
from prompt_loader import PromptLoader
from modules.intelligent_scoring import IntelligentScoringSystem


class EnhancedSP:
    """增强的标准化病人类"""
    
    def __init__(self, data: Sp_data, engine, prompt_path=None, session_id=None, enable_scoring=True):
        self.data = data
        self.engine = engine
        self.session_id = session_id or "default"
        self.prompt_path = prompt_path or os.path.join("prompts", "standard_patient.txt")
        self.enable_scoring = enable_scoring  # 评分开关
        
        # 初始化系统消息和记忆
        self.system_message = self.load_system_message()
        self.memories = [{"role": "user", "content": self.system_message}]
        
        # 条件初始化智能评分系统
        if self.enable_scoring:
            self.scoring_system = IntelligentScoringSystem(self.data.data, engine=self.engine)
        else:
            self.scoring_system = None
        
        # 对话统计
        self.conversation_count = 0
        self.start_time = None
        
    def load_system_message(self) -> str:
        """加载系统提示消息"""
        d = self.data.data
        context = {
            "basics": d.get("basics", {}),
            "chief_complaint": d.get("chief_complaint", ""),
            "present_illness": d.get("present_illness", {}),
            "physical_exam": d.get("physical_exam", {}),
            "diagnosis": d.get("diagnosis", {}),
            "treatment": d.get("treatment", {}),
            "personalities": d.get("personalities", []),
            "patient_emotion": d.get("patient_emotion", ""),
            "patient_expectation": d.get("patient_expectation", "")
        }
        return PromptLoader.load_prompt(self.prompt_path, context)
    
    def memorize(self, message: str, role: Literal['user', 'assistant']):
        """记录对话"""
        self.memories.append({"role": role, "content": message})
        
        # 仅记录对话历史到评分系统，不进行实时评分计算
        if self.enable_scoring and self.scoring_system:
            self.scoring_system.record_message(message, role)
    
    def speak(self, message: str) -> str:
        """与病人对话"""
        self.memorize(message, "user")
        self.conversation_count += 1
        
        # 获取AI响应
        response = self.engine.get_response(self.memories)
        self.memorize(response, "assistant")
        
        return response
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史（不包含系统消息）"""
        return self.memories[1:]  # 跳过第一条系统消息
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        user_messages = [msg for msg in self.memories if msg["role"] == "user"]
        assistant_messages = [msg for msg in self.memories if msg["role"] == "assistant"]
        
        return {
            "session_id": self.session_id,
            "patient_name": self.data.basics.get("name", "Unknown"),
            "chief_complaint": self.data.data.get("chief_complaint", ""),
            "total_messages": len(self.memories) - 1,  # 减去系统消息
            "user_messages": len(user_messages) - 1,   # 减去系统消息
            "assistant_messages": len(assistant_messages),
            "conversation_count": self.conversation_count
        }
    
    def get_score_report(self) -> Dict[str, Any]:
        """获取评分报告（延迟计算）"""
        if self.scoring_system:
            # 在获取报告时才从对话历史进行评分计算
            self.scoring_system.calculate_scores_from_history()
            return self.scoring_system.get_detailed_report()
        return {"error": "评分系统未启用"}
    
    def get_score_summary(self) -> Dict[str, Any]:
        """获取评分摘要（延迟计算）"""
        if self.scoring_system:
            # 在获取报告时才从对话历史进行评分计算
            self.scoring_system.calculate_scores_from_history()
            return self.scoring_system.calculate_score()
        return {"error": "评分系统未启用"}
    
    def get_suggestions(self) -> List[str]:
        """获取改进建议"""
        if self.scoring_system:
            return self.scoring_system.get_suggestions()
        return ["评分系统未启用，无法提供建议"]
    
    def export_session_data(self) -> Dict[str, Any]:
        """导出完整会话数据"""
        return {
            "session_info": {
                "session_id": self.session_id,
                "prompt_path": self.prompt_path,
                "conversation_count": self.conversation_count
            },
            "case_data": self.data.data,
            "conversation_history": self.get_conversation_history(),
            "conversation_summary": self.get_conversation_summary(),
            "score_report": self.get_score_report(),
            "suggestions": self.get_suggestions()
        }


class SPFactory:
    """SP 工厂类，用于创建和管理SP实例"""
    
    @staticmethod
    def create_sp(case_data: Sp_data, engine=None, prompt_path=None, session_id=None, enable_scoring=True) -> EnhancedSP:
        """创建SP实例"""
        if engine is None:
            engine = GPTEngine()
        
        return EnhancedSP(
            data=case_data,
            engine=engine,
            prompt_path=prompt_path,
            session_id=session_id,
            enable_scoring=enable_scoring
        )
    
    @staticmethod
    def create_from_preset(preset_path: str, engine=None, prompt_path=None, session_id=None) -> EnhancedSP:
        """从预设文件创建SP实例"""
        sp_data = Sp_data()
        sp_data.load_from_json(preset_path)
        
        return SPFactory.create_sp(
            case_data=sp_data,
            engine=engine,
            prompt_path=prompt_path,
            session_id=session_id
        )


class SPManager:
    """SP 管理器，管理多个SP会话"""
    
    def __init__(self):
        self.active_sessions: Dict[str, EnhancedSP] = {}
    
    def create_session(self, session_id: str, case_data: Sp_data, 
                      engine=None, prompt_path=None, enable_scoring=True) -> EnhancedSP:
        """创建新的SP会话"""
        sp = SPFactory.create_sp(
            case_data=case_data,
            engine=engine,
            prompt_path=prompt_path,
            session_id=session_id,
            enable_scoring=enable_scoring
        )
        self.active_sessions[session_id] = sp
        return sp
    
    def get_session(self, session_id: str) -> Optional[EnhancedSP]:
        """获取SP会话"""
        return self.active_sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """删除SP会话"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> List[str]:
        """列出所有活动会话"""
        return list(self.active_sessions.keys())
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话摘要"""
        sp = self.get_session(session_id)
        if sp:
            return sp.get_conversation_summary()
        return None
    
    def get_all_sessions_summary(self) -> List[Dict[str, Any]]:
        """获取所有会话摘要"""
        summaries = []
        for session_id, sp in self.active_sessions.items():
            summary = sp.get_conversation_summary()
            summaries.append(summary)
        return summaries


# 兼容性：保持原有的SP类接口
class SP(EnhancedSP):
    """原始SP类的兼容包装"""
    
    def __init__(self, data: Sp_data, engine, prompt_path=None):
        super().__init__(data, engine, prompt_path)


# 全局SP管理器实例
sp_manager = SPManager()
