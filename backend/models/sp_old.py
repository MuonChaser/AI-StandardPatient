
import os
from typing import Dict, Any, List, Optional, Literal
from sp_data import Sp_data
from modules.intelligent_scoring import IntelligentScoringSystem
from engine.gpt import GPTEngine

# 导入新的核心模块
from core.interfaces import IPatient, IEngine, IScoringSystem
from core.domain import Message, MessageRole, ConversationStats, PatientCase, ScoreReport


class StandardPatient(IPatient):
    """标准化病人类 - 重构版本，实现更好的面向对象设计"""
    
    def __init__(self, 
                 case: PatientCase,
                 engine: IEngine,
                 scoring_system: IScoringSystem,
                 session_id: str,
                 prompt_path: Optional[str] = None):
        """
        初始化标准化病人
        
        Args:
            case: 病人病例信息
            engine: AI引擎
            scoring_system: 评分系统
            session_id: 会话ID
            prompt_path: 提示文件路径
        """
        self._case = case
        self._engine = engine
        self._scoring_system = scoring_system
        self._session_id = session_id
        self._prompt_path = prompt_path or os.path.join("prompts", "standard_patient.txt")
        
        # 初始化对话相关组件
        self._messages: List[Message] = []
        self._stats = ConversationStats()
        self._system_message = self._load_system_message()
        
        # 添加系统消息
        self._add_system_message()
    
    def _add_system_message(self) -> None:
        """添加系统消息"""
        system_msg = Message(
            content=self._system_message,
            role=MessageRole.SYSTEM
        )
        self._messages.append(system_msg)
    
    def _load_system_message(self) -> str:
        """加载系统提示消息"""
        context = {
            "basics": {
                "name": self._case.basics.name,
                "age": self._case.basics.age,
                "gender": self._case.basics.gender,
                "occupation": self._case.basics.occupation
            },
            "chief_complaint": self._case.chief_complaint,
            "present_illness": self._case.present_illness,
            "physical_exam": self._case.physical_exam,
            "diagnosis": self._case.diagnosis,
            "treatment": self._case.treatment,
            "personalities": self._case.personalities,
            "patient_emotion": self._case.patient_emotion,
            "patient_expectation": self._case.patient_expectation
        }
        
        # 加载提示模板
        try:
            with open(self._prompt_path, 'r', encoding='utf-8') as f:
                template = f.read()
            return template.format(**context)
        except FileNotFoundError:
            return f"你是一位名叫{self._case.basics.name}的标准化病人。"
    
    def speak(self, message: str) -> str:
        """与病人对话"""
        if not message.strip():
            raise ValueError("消息内容不能为空")
        
        # 记录用户消息
        user_msg = Message(content=message, role=MessageRole.USER)
        self._messages.append(user_msg)
        self._stats.add_message(MessageRole.USER)
        
        # 记录到评分系统
        self._scoring_system.record_message(message, MessageRole.USER.value)
        
        # 生成AI响应
        response = self._generate_response()
        
        # 记录助手消息
        assistant_msg = Message(content=response, role=MessageRole.ASSISTANT)
        self._messages.append(assistant_msg)
        self._stats.add_message(MessageRole.ASSISTANT)
        
        # 记录到评分系统
        self._scoring_system.record_message(response, MessageRole.ASSISTANT.value)
        
        return response
    
    def _generate_response(self) -> str:
        """生成AI响应"""
        # 转换消息格式
        engine_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in self._messages
        ]
        return self._engine.get_response(engine_messages)
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        return {
            "session_id": self._session_id,
            "patient_name": self.patient_name,
            "chief_complaint": self._case.chief_complaint,
            "total_messages": self._stats.total_messages,
            "user_messages": self._stats.user_messages,
            "assistant_messages": self._stats.assistant_messages,
            "conversation_duration_minutes": self._stats.duration_minutes,
            "start_time": self._stats.start_time.isoformat() if self._stats.start_time else None,
            "last_message_time": self._stats.last_message_time.isoformat() if self._stats.last_message_time else None
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
    def patient_name(self) -> str:
        """获取病人姓名"""
        return self._case.basics.name
    
    @property
    def session_id(self) -> str:
        """获取会话ID"""
        return self._session_id
    
    @property
    def case_info(self) -> PatientCase:
        """获取病例信息"""
        return self._case
    
    @property
    def conversation_stats(self) -> ConversationStats:
        """获取对话统计"""
        return self._stats
    
    @property
    def message_history(self) -> List[Message]:
        """获取消息历史"""
        return self._messages.copy()
    
    def export_conversation(self) -> Dict[str, Any]:
        """导出完整对话数据"""
        return {
            "session_id": self._session_id,
            "patient_case": {
                "name": self._case.basics.name,
                "chief_complaint": self._case.chief_complaint,
                "diagnosis": self._case.diagnosis
            },
            "messages": [msg.to_dict() for msg in self._messages],
            "stats": {
                "total_messages": self._stats.total_messages,
                "user_messages": self._stats.user_messages,
                "assistant_messages": self._stats.assistant_messages,
                "duration_minutes": self._stats.duration_minutes
            }
        }


import os
import sys
from typing import Literal, Dict, Any, Optional, List

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from engine.gpt import GPTEngine
from sp_data import Sp_data
from prompt_loader import PromptLoader
from modules.intelligent_scoring import IntelligentScoringSystem


class StandardPatient:
    """标准化病人类 - 集成智能评分系统"""
    
    def __init__(self, data: Sp_data, engine, prompt_path=None, session_id=None):
        self.data = data
        self.engine = engine
        self.session_id = session_id or "default"
        self.prompt_path = prompt_path or os.path.join("prompts", "standard_patient.txt")
        
        # 初始化系统消息和记忆
        self.system_message = self._load_system_message()
        self.memories = [{"role": "user", "content": self.system_message}]
        
        # 智能评分系统 - 始终启用
        self._initialize_scoring_system()
        
        # 对话统计
        self._initialize_conversation_stats()
        
    def _initialize_scoring_system(self):
        """初始化智能评分系统"""
        self.scoring_system = IntelligentScoringSystem(self.data.data, engine=self.engine)
        
    def _initialize_conversation_stats(self):
        """初始化对话统计"""
        self.conversation_count = 0
        self.start_time = None
        
    def _load_system_message(self) -> str:
        """加载系统提示消息"""
        case_data = self.data.data
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
        return PromptLoader.load_prompt(self.prompt_path, context)
    
    def memorize(self, message: str, role: Literal['user', 'assistant']):
        """记录对话"""
        self.memories.append({"role": role, "content": message})
        
        # 记录对话历史到评分系统（延迟评分模式）
        self.scoring_system.record_message(message, role)
    
    def speak(self, message: str) -> str:
        """与病人对话"""
        if not message.strip():
            raise ValueError("消息内容不能为空")
            
        self._record_user_message(message)
        response = self._generate_response()
        self._record_assistant_message(response)
        
        return response
    
    def _record_user_message(self, message: str):
        """记录用户消息"""
        self.memorize(message, "user")
        self.conversation_count += 1
        
    def _generate_response(self) -> str:
        """生成AI响应"""
        return self.engine.get_response(self.memories)
        
    def _record_assistant_message(self, response: str):
        """记录助手响应"""
        self.memorize(response, "assistant")
    
    @property
    def patient_name(self) -> str:
        """获取病人姓名"""
        return self.data.basics.get("name", "Unknown")
    
    @property
    def chief_complaint(self) -> str:
        """获取主诉"""
        return self.data.data.get("chief_complaint", "")
    
    @property
    def conversation_length(self) -> int:
        """获取对话长度（不包含系统消息）"""
        return len(self.memories) - 1
        
    @property
    def user_message_count(self) -> int:
        """获取用户消息数量（不包含系统消息）"""
        user_messages = [msg for msg in self.memories if msg["role"] == "user"]
        return len(user_messages) - 1  # 减去系统消息
        
    @property
    def assistant_message_count(self) -> int:
        """获取助手消息数量"""
        return len([msg for msg in self.memories if msg["role"] == "assistant"])
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史（不包含系统消息）"""
        return self.memories[1:]  # 跳过第一条系统消息
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        return {
            "session_id": self.session_id,
            "patient_name": self.patient_name,
            "chief_complaint": self.chief_complaint,
            "total_messages": self.conversation_length,
            "user_messages": self.user_message_count,
            "assistant_messages": self.assistant_message_count,
            "conversation_count": self.conversation_count
        }
    
    def get_score_report(self) -> Dict[str, Any]:
        """获取评分报告（延迟计算）"""
        # 在获取报告时才从对话历史进行评分计算
        self.scoring_system.calculate_scores_from_history()
        return self.scoring_system.get_detailed_report()
    
    def get_score_summary(self) -> Dict[str, Any]:
        """获取评分摘要（延迟计算）"""
        # 在获取报告时才从对话历史进行评分计算
        self.scoring_system.calculate_scores_from_history()
        return self.scoring_system.calculate_score()
    
    def get_suggestions(self) -> List[str]:
        """获取改进建议"""
        return self.scoring_system.get_suggestions()
    
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


class PatientFactory:
    """病人工厂类，用于创建标准化病人实例"""
    
    @staticmethod
    def create_sp(case_data: Sp_data, engine=None, prompt_path=None, session_id=None) -> 'StandardPatient':
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
    def create_from_preset(preset_path: str, engine=None, prompt_path=None, session_id=None) -> 'StandardPatient':
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
        self.active_sessions: Dict[str, 'StandardPatient'] = {}

    def create_session(self, session_id: str, case_data: Sp_data, 
                      engine=None, prompt_path=None) -> 'StandardPatient':
        """创建新的SP会话"""
        sp = PatientFactory.create_sp(
            case_data=case_data,
            engine=engine,
            prompt_path=prompt_path,
            session_id=session_id
        )
        self.active_sessions[session_id] = sp
        return sp

    def get_session(self, session_id: str) -> Optional['StandardPatient']:
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
        
    def get_sessions_by_patient_name(self, patient_name: str) -> List['StandardPatient']:
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
patient_manager = PatientManager()
