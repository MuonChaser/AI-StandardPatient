"""
重构的标准化病人模型 - 基于新的面向对象架构
"""
import os
from typing import Dict, Any, List, Optional, Literal
from sp_data import Sp_data
from modules.intelligent_scoring import IntelligentScoringSystem
from engine.gpt import GPTEngine

# 导入新的核心模块
try:
    from core.interfaces import IPatient, IEngine, IScoringSystem
    from core.domain import Message, MessageRole, ConversationStats, PatientCase, ScoreReport
except ImportError:
    # 如果核心模块不可用，使用临时类型定义
    from abc import ABC, abstractmethod
    class IPatient(ABC):
        pass
    class IEngine(ABC):
        pass
    class IScoringSystem(ABC):
        pass


class StandardPatient:
    """标准化病人类 - 重构版本，实现更好的面向对象设计"""
    
    def __init__(self, 
                 data: Sp_data,
                 engine,
                 prompt_path: Optional[str] = None,
                 session_id: Optional[str] = None):
        """
        初始化标准化病人
        
        Args:
            data: 病人数据
            engine: AI引擎
            prompt_path: 提示文件路径
            session_id: 会话ID
        """
        self._data = data
        self._engine = engine
        self._session_id = session_id or "default"
        self._prompt_path = prompt_path or os.path.join("prompts", "standard_patient.txt")
        
        # 初始化对话相关组件
        self._messages: List[Dict[str, str]] = []
        self._conversation_count = 0
        self._start_time = None
        
        # 初始化系统消息
        self._system_message = self._load_system_message()
        self._messages.append({"role": "system", "content": self._system_message})
        
        # 智能评分系统 - 始终启用
        self._scoring_system = IntelligentScoringSystem(self._data.data, engine=self._engine)
    
    def _load_system_message(self) -> str:
        """加载系统提示消息"""
        case_data = self._data.data
        context = {
            "basics": case_data.get("basics", {}),
            "chief_complaint": case_data.get("chief_complaint", ""),
            "present_illness": case_data.get("present_illness", {}),
            "physical_exam": case_data.get("physical_exam", {}),
            "diagnosis": case_data.get("diagnosis", {}),
            "treatment": case_data.get("treatment", {}),
            "personalities": case_data.get("personalities", []),
            "patient_emotion": case_data.get("patient_emotion", ""),
            "patient_expectation": case_data.get("patient_expectation", "")
        }
        
        # 加载提示模板
        try:
            with open(self._prompt_path, 'r', encoding='utf-8') as f:
                template = f.read()
            return template.format(**context)
        except FileNotFoundError:
            basics = case_data.get("basics", {})
            name = basics.get("name", "Unknown") if isinstance(basics, dict) else "Unknown"
            return f"你是一位名叫{name}的标准化病人。"
    
    def speak(self, message: str) -> str:
        """与病人对话"""
        if not message.strip():
            raise ValueError("消息内容不能为空")
        
        # 记录用户消息
        self._record_user_message(message)
        
        # 生成AI响应
        response = self._generate_response()
        
        # 记录助手消息
        self._record_assistant_message(response)
        
        return response
    
    def _record_user_message(self, message: str) -> None:
        """记录用户消息"""
        self._messages.append({"role": "user", "content": message})
        self._conversation_count += 1
        
        # 记录到评分系统
        self._scoring_system.record_message(message, "user")
    
    def _generate_response(self) -> str:
        """生成AI响应"""
        return self._engine.get_response(self._messages)
    
    def _record_assistant_message(self, response: str) -> None:
        """记录助手响应"""
        self._messages.append({"role": "assistant", "content": response})
        
        # 记录到评分系统
        self._scoring_system.record_message(response, "assistant")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        user_messages = [msg for msg in self._messages if msg["role"] == "user"]
        assistant_messages = [msg for msg in self._messages if msg["role"] == "assistant"]
        
        return {
            "session_id": self._session_id,
            "patient_name": self.patient_name,
            "chief_complaint": self.chief_complaint,
            "total_messages": len(self._messages) - 1,  # 减去系统消息
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "conversation_count": self._conversation_count
        }
    
    def get_score_report(self) -> Dict[str, Any]:
        """获取评分报告（延迟计算）"""
        self._scoring_system.calculate_scores_from_history()
        return self._scoring_system.get_detailed_report()
    
    def get_score_summary(self) -> Dict[str, Any]:
        """获取评分摘要（延迟计算）"""
        self._scoring_system.calculate_scores_from_history()
        return self._scoring_system.calculate_score()
    
    def get_suggestions(self) -> List[str]:
        """获取改进建议"""
        return self._scoring_system.get_suggestions()
    
    @property
    def data(self) -> Sp_data:
        """获取病人数据（向后兼容）"""
        return self._data
    
    @property
    def scoring_system(self):
        """获取评分系统（向后兼容）"""
        return self._scoring_system
    
    @property
    def memories(self) -> List[Dict[str, str]]:
        """获取消息历史（向后兼容）"""
        return self._messages
    
    @property
    def engine(self):
        """获取AI引擎（向后兼容）"""
        return self._engine
    
    def memorize(self, message: str, role: str) -> None:
        """记录对话（向后兼容）"""
        self._messages.append({"role": role, "content": message})
        if role == "user":
            self._conversation_count += 1
            self._scoring_system.record_message(message, role)
        elif role == "assistant":
            self._scoring_system.record_message(message, role)
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史（向后兼容）"""
        # 跳过系统消息，返回用户和助手的对话
        return [msg for msg in self._messages if msg["role"] in ["user", "assistant"]]
    
    def export_session_data(self) -> Dict[str, Any]:
        """导出会话数据（向后兼容）"""
        return self.export_conversation()
    
    @property
    def patient_name(self) -> str:
        """获取病人姓名"""
        basics = getattr(self._data, 'basics', {})
        if isinstance(basics, dict):
            return basics.get("name", "Unknown")
        return "Unknown"
    
    @property
    def chief_complaint(self) -> str:
        """获取主诉"""
        return self._data.data.get("chief_complaint", "")
    
    @property
    def session_id(self) -> str:
        """获取会话ID"""
        return self._session_id
    
    @property
    def conversation_count(self) -> int:
        """获取对话次数（向后兼容）"""
        return self._conversation_count
    
    @property
    def conversation_length(self) -> int:
        """获取对话长度（不包含系统消息）"""
        return len(self._messages) - 1
    
    @property
    def user_message_count(self) -> int:
        """获取用户消息数量"""
        return len([msg for msg in self._messages if msg["role"] == "user"])
    
    @property
    def assistant_message_count(self) -> int:
        """获取助手消息数量"""
        return len([msg for msg in self._messages if msg["role"] == "assistant"])
    
    @property
    def message_history(self) -> List[Dict[str, str]]:
        """获取消息历史"""
        return self._messages.copy()
    
    def export_conversation(self) -> Dict[str, Any]:
        """导出完整对话数据"""
        return {
            "session_id": self._session_id,
            "patient_case": {
                "name": self.patient_name,
                "chief_complaint": self.chief_complaint
            },
            "messages": self._messages,
            "stats": {
                "total_messages": len(self._messages) - 1,
                "user_messages": self.user_message_count,
                "assistant_messages": self.assistant_message_count,
                "conversation_count": self._conversation_count
            }
        }


class PatientFactory:
    """病人工厂类，用于创建标准化病人实例"""
    
    @staticmethod
    def create_sp(case_data: Sp_data, 
                  engine=None, 
                  prompt_path=None, 
                  session_id=None) -> StandardPatient:
        """创建SP实例"""
        if engine is None:
            engine = GPTEngine()
        
        return StandardPatient(
            data=case_data,
            engine=engine,
            prompt_path=prompt_path,
            session_id=session_id
        )
    
    @staticmethod  
    def create_from_preset(preset_path: str, 
                          engine=None, 
                          prompt_path=None, 
                          session_id=None) -> StandardPatient:
        """从预设文件创建SP实例"""
        sp_data = Sp_data()
        sp_data.load_from_json(preset_path)
        
        if engine is None:
            engine = GPTEngine()
        
        return PatientFactory.create_sp(
            case_data=sp_data,
            engine=engine,
            prompt_path=prompt_path,
            session_id=session_id
        )


class PatientManager:
    """病人会话管理器"""
    
    def __init__(self):
        self.active_sessions: Dict[str, StandardPatient] = {}

    def create_session(self, session_id: str, case_data: Sp_data, 
                      engine=None, prompt_path=None) -> StandardPatient:
        """创建新的SP会话"""
        sp = PatientFactory.create_sp(
            case_data=case_data,
            engine=engine,
            prompt_path=prompt_path,
            session_id=session_id
        )
        self.active_sessions[session_id] = sp
        return sp

    def get_session(self, session_id: str) -> Optional[StandardPatient]:
        """获取会话"""
        return self.active_sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False

    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return session_id in self.active_sessions

    def list_sessions(self) -> List[str]:
        """列出所有会话ID"""
        return list(self.active_sessions.keys())
        
    @property
    def session_count(self) -> int:
        """获取当前活跃会话数量"""
        return len(self.active_sessions)
        
    def get_sessions_by_patient_name(self, patient_name: str) -> List[StandardPatient]:
        """根据病人姓名查找会话"""
        return [sp for sp in self.active_sessions.values() 
                if sp.patient_name == patient_name]
    
    def clear_all_sessions(self) -> int:
        """清除所有会话，返回清除的数量"""
        count = len(self.active_sessions)
        self.active_sessions.clear()
        return count

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话摘要"""
        sp = self.get_session(session_id)
        return sp.get_conversation_summary() if sp else None

    def get_all_sessions_summary(self) -> List[Dict[str, Any]]:
        """获取所有会话摘要"""
        summaries = []
        for session_id, sp in self.active_sessions.items():
            summary = sp.get_conversation_summary()
            summary['session_id'] = session_id
            summaries.append(summary)
        return summaries


# 全局实例
patient_manager = PatientManager()


# 兼容性：保持原有的SP类接口
class SP(StandardPatient):
    """原始SP类的兼容包装"""
    
    def __init__(self, data: Sp_data, engine, prompt_path=None):
        super().__init__(data, engine, prompt_path)