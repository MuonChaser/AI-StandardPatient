"""
领域模型 - 定义核心业务实体
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """对话消息实体"""
    content: str
    role: MessageRole
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "role": self.role.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ConversationStats:
    """对话统计信息"""
    total_messages: int = 0
    user_messages: int = 0
    assistant_messages: int = 0
    start_time: Optional[datetime] = None
    last_message_time: Optional[datetime] = None
    
    def add_message(self, role: MessageRole) -> None:
        """添加消息统计"""
        self.total_messages += 1
        if role == MessageRole.USER:
            self.user_messages += 1
        elif role == MessageRole.ASSISTANT:
            self.assistant_messages += 1
        
        current_time = datetime.now()
        if self.start_time is None:
            self.start_time = current_time
        self.last_message_time = current_time
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """对话持续时间（分钟）"""
        if self.start_time and self.last_message_time:
            return (self.last_message_time - self.start_time).total_seconds() / 60
        return None


@dataclass
class PatientBasics:
    """病人基本信息"""
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PatientBasics':
        """从字典创建实例"""
        return cls(
            name=data.get("name", "Unknown"),
            age=data.get("age"),
            gender=data.get("gender"),
            occupation=data.get("occupation")
        )


@dataclass
class PatientCase:
    """病人病例信息"""
    basics: PatientBasics
    chief_complaint: str
    present_illness: Dict[str, Any] = field(default_factory=dict)
    physical_exam: Dict[str, Any] = field(default_factory=dict)
    diagnosis: Dict[str, Any] = field(default_factory=dict)
    treatment: Dict[str, Any] = field(default_factory=dict)
    personalities: List[str] = field(default_factory=list)
    patient_emotion: str = ""
    patient_expectation: str = ""
    
    @classmethod
    def from_sp_data(cls, sp_data) -> 'PatientCase':
        """从Sp_data创建实例"""
        case_data = sp_data.data
        return cls(
            basics=PatientBasics.from_dict(case_data.get("basics", {})),
            chief_complaint=case_data.get("chief_complaint", ""),
            present_illness=case_data.get("present_illness", {}),
            physical_exam=case_data.get("physical_exam", {}),
            diagnosis=case_data.get("diagnosis", {}),
            treatment=case_data.get("treatment", {}),
            personalities=case_data.get("personalities", []),
            patient_emotion=case_data.get("patient_emotion", ""),
            patient_expectation=case_data.get("patient_expectation", "")
        )


@dataclass
class ScoreReport:
    """评分报告"""
    overall_score: float
    detailed_scores: Dict[str, float]
    suggestions: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "overall_score": self.overall_score,
            "detailed_scores": self.detailed_scores,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat()
        }