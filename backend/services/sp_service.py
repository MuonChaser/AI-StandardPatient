"""
SP会话服务
"""
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# 导入SP相关模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.models.sp import StandardPatient, patient_manager
from sp_data import Sp_data
from engine.gpt import GPTEngine
from backend.models.session import SessionManager
from backend.services.preset_service import PresetService


class SPService:
    """SP服务类"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    def create_sp_session(self, session_id: str, preset_file: Optional[str] = None, 
                         custom_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建新的SP会话（评分系统始终启用）"""
        # 检查会话数量限制
        if self.session_manager.is_at_capacity():
            raise ValueError("已达到最大会话数量限制")
        
        # 检查会话是否已存在
        if self.session_manager.session_exists(session_id):
            raise ValueError(f"会话 {session_id} 已存在")
        
        # 创建SP数据对象
        sp_data = Sp_data()
        if preset_file:
            if not PresetService.preset_exists(preset_file):
                raise ValueError(f"预设文件 {preset_file} 不存在")
            preset_path = PresetService.get_preset_path(preset_file)
            sp_data.load_from_json(preset_path)
        elif custom_data:
            sp_data.data = custom_data
        else:
            raise ValueError("必须提供 preset_file 或 custom_data")
        # 创建增强SP实例
        engine = GPTEngine()
        sp = patient_manager.create_session(session_id, sp_data, engine)
        
        # 也在原有的session_manager中注册，保持兼容性
        self.session_manager.create_session(session_id, sp, preset_file)
        metadata = self.session_manager.get_session_metadata(session_id)
        # 返回结构化病例主要信息
        basics = sp_data.basics if hasattr(sp_data, 'basics') else {}
        basics = basics if isinstance(basics, dict) else {}
        
        return {
            "session_id": session_id,
            "patient_name": basics.get("name", "未知"),
            "disease": getattr(sp_data, 'disease', ''),
            "chief_complaint": sp_data.data.get("chief_complaint", ""),
            "created_at": datetime.fromtimestamp(metadata["created_at"]).isoformat()
        }
    
    def chat_with_sp(self, session_id: str, message: str) -> Dict[str, Any]:
        """与SP进行对话（优化版）"""
        # 直接从patient_manager获取会话，简化查找逻辑
        sp = patient_manager.get_session(session_id)
        if not sp:
            raise ValueError(f"会话 {session_id} 不存在，请先创建会话")
        
        if not message:
            raise ValueError("消息内容不能为空")
        
        # 核心对话处理
        response = sp.speak(message)
        
        # 简化的响应构造
        return {
            "session_id": session_id,
            "user_message": message,
            "sp_response": response,
            "timestamp": datetime.now().isoformat(),
            "message_count": sp.conversation_count  # 直接使用SP的计数
        }
    
    def get_chat_history(self, session_id: str) -> Dict[str, Any]:
        """获取对话历史"""
        # 优先从patient_manager获取会话
        sp = patient_manager.get_session(session_id)
        if not sp:
            # 兼容性：从原有session_manager获取
            if not self.session_manager.session_exists(session_id):
                raise ValueError(f"会话 {session_id} 不存在")
            sp = self.session_manager.get_session(session_id)
        
        # 使用增强SP的方法获取对话历史
        if hasattr(sp, 'get_conversation_history'):
            conversation_history = sp.get_conversation_history()
            history = []
            
            # 将对话历史转换为配对格式
            for i in range(0, len(conversation_history), 2):
                if i + 1 < len(conversation_history):
                    user_msg = conversation_history[i]
                    assistant_msg = conversation_history[i + 1]
                    
                    if user_msg["role"] == "user" and assistant_msg["role"] == "assistant":
                        history.append({
                            "user_message": user_msg["content"],
                            "sp_response": assistant_msg["content"],
                            "timestamp": f"第{len(history)+1}轮对话"
                        })
        else:
            # 兼容性：使用原有方法
            history = []
            for i, memory in enumerate(sp.memories):
                if memory["role"] != "user" or i == 0:  # 跳过第一条系统消息
                    continue
                
                user_msg = memory["content"]
                # 查找对应的助手回复
                if i + 1 < len(sp.memories) and sp.memories[i + 1]["role"] == "assistant":
                    assistant_msg = sp.memories[i + 1]["content"]
                    history.append({
                        "user_message": user_msg,
                        "sp_response": assistant_msg,
                        "timestamp": f"第{len(history)+1}轮对话"
                    })
        
        return {
            "session_id": session_id,
            "total_messages": len(history),
            "history": history
        }
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """获取会话信息"""
        if not self.session_manager.session_exists(session_id):
            raise ValueError(f"会话 {session_id} 不存在")
        sp = self.session_manager.get_session(session_id)
        sp_data = sp.data
        info = dict(sp_data.data)
        info["session_id"] = session_id
        info["total_messages"] = len([m for m in sp.memories if m["role"] in ["user", "assistant"]]) // 2
        return info
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """删除指定会话"""
        if not self.session_manager.session_exists(session_id):
            raise ValueError(f"会话 {session_id} 不存在")
        
        # 获取会话信息用于返回
        session_info = self.session_manager.delete_session(session_id)
        
        return {
            "session_id": session_id,
            "patient_name": session_info.get("patient_name", "未知"),
            "message_count": session_info.get("message_count", 0)
        }
    
    @staticmethod
    def validate_sp_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """验证SP数据格式"""
        # 基本字段验证
        required_fields = ["basics", "disease", "symptoms"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise ValueError(f"缺少必需字段: {', '.join(missing_fields)}")
        
        # 数据类型验证
        if not isinstance(data.get("symptoms"), list):
            raise ValueError("symptoms 字段必须是数组")
        
        if not isinstance(data.get("disease"), str):
            raise ValueError("disease 字段必须是字符串")
        
        return {
            "valid": True,
            "message": "SP数据格式验证通过",
            "data_summary": {
                "patient_name": data.get("basics", {}).get("name", "未知"),
                "disease": data.get("disease"),
                "symptoms_count": len(data.get("symptoms", [])),
                "has_personalities": bool(data.get("personalities")),
                "has_hiddens": bool(data.get("hiddens")),
                "has_examinations": bool(data.get("examinations"))
            }
        }
