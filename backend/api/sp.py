"""
SP会话API路由
"""
from flask import Blueprint, request

from utils.response import APIResponse
from services.sp_service import SPService


def create_sp_blueprint(session_manager):
    """创建SP会话蓝图"""
    sp_bp = Blueprint('sp', __name__)
    sp_service = SPService(session_manager)
    
    @sp_bp.route('/api/sp/session/create', methods=['POST'])
    def create_sp_session():
        """创建新的SP会话"""
        try:
            data = request.json
            session_id = data.get('session_id')
            preset_file = data.get('preset_file')
            custom_data = data.get('custom_data')
            
            if not session_id:
                return APIResponse.error("session_id 不能为空")
            
            session_info = sp_service.create_sp_session(session_id, preset_file, custom_data)
            return APIResponse.success(session_info, f"SP会话 {session_id} 创建成功")
        
        except ValueError as e:
            return APIResponse.error(str(e))
        except Exception as e:
            return APIResponse.error(f"创建SP会话失败: {str(e)}")
    
    @sp_bp.route('/api/sp/session/<session_id>/chat', methods=['POST'])
    def chat_with_sp(session_id: str):
        """与SP进行对话"""
        try:
            data = request.json
            message = data.get('message')
            
            chat_response = sp_service.chat_with_sp(session_id, message)
            return APIResponse.success(chat_response, "对话成功")
        
        except ValueError as e:
            return APIResponse.error(str(e))
        except Exception as e:
            return APIResponse.error(f"对话失败: {str(e)}")
    
    @sp_bp.route('/api/sp/session/<session_id>/history', methods=['GET'])
    def get_chat_history(session_id: str):
        """获取对话历史"""
        try:
            history_data = sp_service.get_chat_history(session_id)
            return APIResponse.success(history_data, "获取对话历史成功")
        
        except ValueError as e:
            return APIResponse.error(str(e))
        except Exception as e:
            return APIResponse.error(f"获取对话历史失败: {str(e)}")
    
    @sp_bp.route('/api/sp/session/<session_id>/info', methods=['GET'])
    def get_session_info(session_id: str):
        """获取会话信息"""
        try:
            session_info = sp_service.get_session_info(session_id)
            return APIResponse.success(session_info, "获取会话信息成功")
        
        except ValueError as e:
            return APIResponse.error(str(e))
        except Exception as e:
            return APIResponse.error(f"获取会话信息失败: {str(e)}")
    
    @sp_bp.route('/api/sp/sessions', methods=['GET'])
    def list_sessions():
        """列出所有活跃的会话"""
        try:
            # 清理过期会话
            session_manager.clean_expired_sessions()
            
            sessions = session_manager.get_all_sessions()
            
            return APIResponse.success({
                "total_sessions": len(sessions),
                "max_sessions": session_manager.max_sessions,
                "sessions": sessions
            }, f"获取到 {len(sessions)} 个活跃会话")
        
        except Exception as e:
            return APIResponse.error(f"获取会话列表失败: {str(e)}")
    
    @sp_bp.route('/api/sp/session/<session_id>', methods=['DELETE'])
    def delete_session(session_id: str):
        """删除指定会话"""
        try:
            result = sp_service.delete_session(session_id)
            return APIResponse.success(result, f"会话 {session_id} 已删除")
        
        except ValueError as e:
            return APIResponse.error(str(e))
        except Exception as e:
            return APIResponse.error(f"删除会话失败: {str(e)}")
    
    @sp_bp.route('/api/sp/data/validate', methods=['POST'])
    def validate_sp_data():
        """验证SP数据格式"""
        try:
            data = request.json
            validation_result = SPService.validate_sp_data(data)
            return APIResponse.success(validation_result, "数据验证成功")
        
        except ValueError as e:
            return APIResponse.error(str(e))
        except Exception as e:
            return APIResponse.error(f"数据验证失败: {str(e)}")
    
    return sp_bp
