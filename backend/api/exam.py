"""
检查报告API路由
"""
from flask import Blueprint
from backend.utils.response import APIResponse
from backend.modules.exam_report import ExamReportGenerator

def create_exam_blueprint(session_manager):
    exam_bp = Blueprint('exam', __name__)

    @exam_bp.route('/api/sp/session/<session_id>/exam_report', methods=['GET'])
    def get_exam_report(session_id):
        """获取指定会话的检查报告"""
        if not session_manager.session_exists(session_id):
            return APIResponse.error(f"会话 {session_id} 不存在")
        sp = session_manager.get_session(session_id)
        report = ExamReportGenerator.get_report(sp.data)
        return APIResponse.success(report, "检查报告获取成功")

    return exam_bp
