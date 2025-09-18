"""
重构的API控制器 - 基于现代化的面向对象设计
"""
from flask import Blueprint, request, jsonify
from typing import Dict, Any

from backend.services.patient_service import PatientService, default_patient_service


class PatientController:
    """病人API控制器"""
    
    def __init__(self, patient_service: PatientService = None):
        """
        初始化控制器
        
        Args:
            patient_service: 病人服务实例
        """
        self._service = patient_service or default_patient_service
        self._blueprint = self._create_blueprint()
    
    def _create_blueprint(self) -> Blueprint:
        """创建Flask蓝图"""
        bp = Blueprint('patient', __name__, url_prefix='/api/patient')
        
        # 注册路由
        bp.add_url_rule('/create', 'create_session', self.create_session, methods=['POST'])
        bp.add_url_rule('/chat', 'chat', self.chat, methods=['POST'])
        bp.add_url_rule('/summary/<session_id>', 'get_summary', self.get_summary, methods=['GET'])
        bp.add_url_rule('/score/<session_id>', 'get_score', self.get_score, methods=['GET'])
        bp.add_url_rule('/sessions', 'list_sessions', self.list_sessions, methods=['GET'])
        bp.add_url_rule('/delete/<session_id>', 'delete_session', self.delete_session, methods=['DELETE'])
        bp.add_url_rule('/statistics', 'get_statistics', self.get_statistics, methods=['GET'])
        
        return bp
    
    @property
    def blueprint(self) -> Blueprint:
        """获取Flask蓝图"""
        return self._blueprint
    
    def create_session(self):
        """创建病人会话"""
        try:
            data = request.get_json()
            
            # 验证必需参数
            if not data or 'session_id' not in data or 'case_data' not in data:
                return jsonify({
                    "success": False,
                    "message": "缺少必需参数: session_id 和 case_data"
                }), 400
            
            session_id = data['session_id']
            case_data = data['case_data']
            
            # 调用服务
            result = self._service.create_patient_session(session_id, case_data)
            
            status_code = 200 if result['success'] else 400
            return jsonify(result), status_code
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"服务器错误: {str(e)}"
            }), 500
    
    def chat(self):
        """与病人对话"""
        try:
            data = request.get_json()
            
            # 验证必需参数
            if not data or 'session_id' not in data or 'message' not in data:
                return jsonify({
                    "success": False,
                    "message": "缺少必需参数: session_id 和 message"
                }), 400
            
            session_id = data['session_id']
            message = data['message']
            
            # 调用服务
            result = self._service.chat_with_patient(session_id, message)
            
            status_code = 200 if result['success'] else 400
            return jsonify(result), status_code
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"服务器错误: {str(e)}"
            }), 500
    
    def get_summary(self, session_id: str):
        """获取会话摘要"""
        try:
            result = self._service.get_patient_summary(session_id)
            
            status_code = 200 if result['success'] else 404
            return jsonify(result), status_code
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"服务器错误: {str(e)}"
            }), 500
    
    def get_score(self, session_id: str):
        """获取评分报告"""
        try:
            result = self._service.get_scoring_report(session_id)
            
            status_code = 200 if result['success'] else 404
            return jsonify(result), status_code
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"服务器错误: {str(e)}"
            }), 500
    
    def list_sessions(self):
        """列出所有会话"""
        try:
            result = self._service.list_all_sessions()
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"服务器错误: {str(e)}"
            }), 500
    
    def delete_session(self, session_id: str):
        """删除会话"""
        try:
            result = self._service.delete_patient_session(session_id)
            
            status_code = 200 if result['success'] else 404
            return jsonify(result), status_code
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"服务器错误: {str(e)}"
            }), 500
    
    def get_statistics(self):
        """获取统计信息"""
        try:
            result = self._service.get_session_statistics()
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"服务器错误: {str(e)}"
            }), 500


# 创建默认控制器实例
default_patient_controller = PatientController()


def create_patient_blueprint(patient_service: PatientService = None) -> Blueprint:
    """
    创建病人API蓝图的工厂函数
    
    Args:
        patient_service: 可选的病人服务实例
        
    Returns:
        Flask蓝图
    """
    controller = PatientController(patient_service)
    return controller.blueprint