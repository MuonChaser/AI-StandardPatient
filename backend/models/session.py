"""
会话管理模型
"""
import time
from typing import Dict, Any
from datetime import datetime

# 导入SP相关模块
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .sp import SP


class SessionManager:
    """SP会话管理器"""
    
    def __init__(self, max_sessions: int = 100, session_timeout: int = 3600):
        self.current_sp_sessions: Dict[str, SP] = {}
        self.session_metadata: Dict[str, Dict] = {}
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout
    
    def clean_expired_sessions(self) -> int:
        """清理过期的会话"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, metadata in self.session_metadata.items():
            if current_time - metadata.get('last_activity', 0) > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            if session_id in self.current_sp_sessions:
                del self.current_sp_sessions[session_id]
            if session_id in self.session_metadata:
                del self.session_metadata[session_id]
        
        return len(expired_sessions)
    
    def create_session(self, session_id: str, sp: SP, preset_file: str = None) -> None:
        """创建新会话"""
        self.current_sp_sessions[session_id] = sp
        self.session_metadata[session_id] = {
            "created_at": time.time(),
            "last_activity": time.time(),
            "message_count": 0,
            "preset_file": preset_file,
            "patient_name": sp.data.basics.get("name", "未知") if isinstance(sp.data.basics, dict) else "未知"
        }
    
    def get_session(self, session_id: str) -> SP:
        """获取会话"""
        return self.current_sp_sessions.get(session_id)
    
    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return session_id in self.current_sp_sessions
    
    def update_activity(self, session_id: str) -> None:
        """更新会话活动时间"""
        if session_id in self.session_metadata:
            self.session_metadata[session_id]["last_activity"] = time.time()
            self.session_metadata[session_id]["message_count"] += 1
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """删除会话并返回会话信息"""
        session_info = self.session_metadata.get(session_id, {})
        
        if session_id in self.current_sp_sessions:
            del self.current_sp_sessions[session_id]
        if session_id in self.session_metadata:
            del self.session_metadata[session_id]
        
        return session_info
    
    def get_session_count(self) -> int:
        """获取当前会话数量"""
        return len(self.current_sp_sessions)
    
    def is_at_capacity(self) -> bool:
        """检查是否达到最大会话数量"""
        return len(self.current_sp_sessions) >= self.max_sessions
    
    def get_all_sessions(self) -> list:
        """获取所有会话信息"""
        sessions = []
        for session_id, sp in self.current_sp_sessions.items():
            metadata = self.session_metadata.get(session_id, {})
            sessions.append({
                "session_id": session_id,
                "patient_name": metadata.get("patient_name", "未知"),
                "disease": sp.data.disease,
                "message_count": metadata.get("message_count", 0),
                "created_at": datetime.fromtimestamp(metadata.get("created_at", 0)).isoformat() if metadata.get("created_at") else "未知",
                "last_activity": datetime.fromtimestamp(metadata.get("last_activity", 0)).isoformat() if metadata.get("last_activity") else "未知",
                "status": "active"
            })
        
        # 按最后活动时间排序
        sessions.sort(key=lambda x: x["last_activity"], reverse=True)
        return sessions
    
    def get_session_metadata(self, session_id: str) -> Dict[str, Any]:
        """获取会话元数据"""
        return self.session_metadata.get(session_id, {})
