"""
健康检查API路由
"""
from flask import Blueprint
from datetime import datetime

from utils.response import APIResponse


def create_health_blueprint(session_manager):
    """创建健康检查蓝图"""
    health_bp = Blueprint('health', __name__)
    
    @health_bp.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        from flask import current_app
        
        # 清理过期会话
        expired_count = session_manager.clean_expired_sessions()
        
        health_info = {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "active_sessions": session_manager.get_session_count(),
            "expired_sessions_cleaned": expired_count,
            "config": {
                "debug": current_app.config.get('DEBUG', False),
                "model_name": current_app.config.get('MODEL_NAME', 'unknown'),
                "max_sessions": current_app.config.get('MAX_SESSIONS', 100)
            }
        }
        return APIResponse.success(health_info, "服务正常运行")
    
    return health_bp
