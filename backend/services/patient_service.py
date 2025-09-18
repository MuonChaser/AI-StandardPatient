"""
重构的服务层 - 基于依赖注入和面向对象设计
"""
from typing import Dict, Any, List, Optional
from sp_data import Sp_data
from engine.gpt import GPTEngine

# 导入本地模块
try:
    from backend.core.interfaces import IPatient, IEngine
except ImportError:
    # 如果核心模块不可用，使用临时类型定义
    from abc import ABC
    class IPatient(ABC):
        pass
    class IEngine(ABC):
        pass

from backend.models.sp import StandardPatient, PatientFactory, PatientManager


class PatientService:
    """病人服务类 - 业务逻辑层"""
    
    def __init__(self, 
                 patient_manager: PatientManager = None,
                 default_engine: IEngine = None):
        """
        初始化病人服务
        
        Args:
            patient_manager: 病人管理器
            default_engine: 默认AI引擎
        """
        self._patient_manager = patient_manager or PatientManager()
        self._default_engine = default_engine or GPTEngine()
    
    def create_patient_session(self, 
                             session_id: str, 
                             case_data: Dict[str, Any],
                             engine: Optional[IEngine] = None) -> Dict[str, Any]:
        """
        创建病人会话
        
        Args:
            session_id: 会话ID
            case_data: 病例数据
            engine: AI引擎（可选）
            
        Returns:
            创建结果信息
        """
        try:
            # 检查会话是否已存在
            if self._patient_manager.session_exists(session_id):
                return {
                    "success": False,
                    "message": f"会话 {session_id} 已存在",
                    "session_id": session_id
                }
            
            # 准备数据
            sp_data = self._prepare_patient_data(case_data)
            used_engine = engine or self._default_engine
            
            # 创建会话
            patient = self._patient_manager.create_session(
                session_id=session_id,
                case_data=sp_data,
                engine=used_engine
            )
            
            return {
                "success": True,
                "message": "会话创建成功",
                "session_id": session_id,
                "patient_name": patient.patient_name,
                "chief_complaint": patient.chief_complaint
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"创建会话失败: {str(e)}",
                "session_id": session_id
            }
    
    def _prepare_patient_data(self, case_data: Dict[str, Any]) -> Sp_data:
        """准备病人数据"""
        sp_data = Sp_data()
        
        # 如果传入的是完整的数据字典
        if isinstance(case_data, dict):
            sp_data.data = case_data
            # 提取基本信息
            basics = case_data.get("basics", {})
            if isinstance(basics, dict):
                sp_data.basics = basics
            # 提取疾病信息
            sp_data.disease = case_data.get("diagnosis", {}).get("primary", "")
        
        return sp_data
    
    def chat_with_patient(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        与病人对话
        
        Args:
            session_id: 会话ID
            message: 用户消息
            
        Returns:
            对话结果
        """
        try:
            # 获取会话
            patient = self._patient_manager.get_session(session_id)
            if not patient:
                return {
                    "success": False,
                    "message": f"会话 {session_id} 不存在"
                }
            
            # 进行对话
            response = patient.speak(message)
            
            return {
                "success": True,
                "response": response,
                "session_id": session_id,
                "message_count": patient.conversation_length
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"对话失败: {str(e)}",
                "session_id": session_id
            }
    
    def get_patient_summary(self, session_id: str) -> Dict[str, Any]:
        """
        获取病人会话摘要
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话摘要
        """
        try:
            patient = self._patient_manager.get_session(session_id)
            if not patient:
                return {
                    "success": False,
                    "message": f"会话 {session_id} 不存在"
                }
            
            summary = patient.get_conversation_summary()
            return {
                "success": True,
                "summary": summary
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"获取摘要失败: {str(e)}"
            }
    
    def get_scoring_report(self, session_id: str) -> Dict[str, Any]:
        """
        获取评分报告
        
        Args:
            session_id: 会话ID
            
        Returns:
            评分报告
        """
        try:
            patient = self._patient_manager.get_session(session_id)
            if not patient:
                return {
                    "success": False,
                    "message": f"会话 {session_id} 不存在"
                }
            
            # 获取评分报告
            score_report = patient.get_score_report()
            suggestions = patient.get_suggestions()
            
            return {
                "success": True,
                "score_report": score_report,
                "suggestions": suggestions,
                "session_id": session_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"获取评分报告失败: {str(e)}"
            }
    
    def list_all_sessions(self) -> Dict[str, Any]:
        """
        列出所有会话
        
        Returns:
            会话列表
        """
        try:
            sessions = self._patient_manager.get_all_sessions_summary()
            return {
                "success": True,
                "sessions": sessions,
                "total_count": len(sessions)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"获取会话列表失败: {str(e)}"
            }
    
    def delete_patient_session(self, session_id: str) -> Dict[str, Any]:
        """
        删除病人会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            删除结果
        """
        try:
            if self._patient_manager.delete_session(session_id):
                return {
                    "success": True,
                    "message": f"会话 {session_id} 删除成功"
                }
            else:
                return {
                    "success": False,
                    "message": f"会话 {session_id} 不存在"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"删除会话失败: {str(e)}"
            }
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        获取会话统计信息
        
        Returns:
            统计信息
        """
        try:
            total_sessions = self._patient_manager.session_count
            sessions = self._patient_manager.get_all_sessions_summary()
            
            # 计算统计信息
            total_messages = sum(s.get("total_messages", 0) for s in sessions)
            avg_messages = total_messages / total_sessions if total_sessions > 0 else 0
            
            # 按病人姓名分组
            patient_names = {}
            for session in sessions:
                name = session.get("patient_name", "Unknown")
                patient_names[name] = patient_names.get(name, 0) + 1
            
            return {
                "success": True,
                "statistics": {
                    "total_sessions": total_sessions,
                    "total_messages": total_messages,
                    "average_messages_per_session": round(avg_messages, 2),
                    "unique_patients": len(patient_names),
                    "patient_distribution": patient_names
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"获取统计信息失败: {str(e)}"
            }


# 创建默认服务实例
default_patient_service = PatientService()