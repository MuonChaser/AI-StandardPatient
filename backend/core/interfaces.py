"""
核心接口定义 - 定义系统的主要抽象接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from sp_data import Sp_data


class IEngine(ABC):
    """AI引擎接口"""
    
    @abstractmethod
    def get_response(self, messages: List[Dict[str, str]]) -> str:
        """获取AI响应"""
        pass


class IScoringSystem(ABC):
    """评分系统接口"""
    
    @abstractmethod
    def record_message(self, message: str, role: str) -> None:
        """记录消息"""
        pass
    
    @abstractmethod
    def calculate_scores_from_history(self) -> Dict[str, Any]:
        """从历史对话计算评分"""
        pass
    
    @abstractmethod
    def get_detailed_report(self) -> Dict[str, Any]:
        """获取详细报告"""
        pass
    
    @abstractmethod
    def calculate_score(self) -> Dict[str, Any]:
        """计算总体评分"""
        pass
    
    @abstractmethod
    def get_suggestions(self) -> List[str]:
        """获取改进建议"""
        pass


class IPatient(ABC):
    """标准化病人接口"""
    
    @abstractmethod
    def speak(self, message: str) -> str:
        """与病人对话"""
        pass
    
    @abstractmethod
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        pass
    
    @abstractmethod
    def get_score_report(self) -> Dict[str, Any]:
        """获取评分报告"""
        pass
    
    @property
    @abstractmethod
    def patient_name(self) -> str:
        """病人姓名"""
        pass
    
    @property
    @abstractmethod
    def session_id(self) -> str:
        """会话ID"""
        pass


class IPatientFactory(ABC):
    """病人工厂接口"""
    
    @abstractmethod
    def create_patient(self, case_data: Sp_data, **kwargs) -> IPatient:
        """创建病人实例"""
        pass


class IPatientRepository(ABC):
    """病人仓储接口"""
    
    @abstractmethod
    def save_session(self, session_id: str, patient: IPatient) -> None:
        """保存会话"""
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[IPatient]:
        """获取会话"""
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        pass
    
    @abstractmethod
    def list_sessions(self) -> List[str]:
        """列出所有会话"""
        pass