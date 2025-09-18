"""
智能评分系统API
提供AI驱动的评分报告和分析功能
"""

from flask import Blueprint, request, jsonify
from backend.utils.response import APIResponse
from models.sp import patient_manager


def create_scoring_blueprint():
    """创建评分蓝图"""
    scoring_bp = Blueprint('scoring', __name__)
    
    @scoring_bp.route('/api/scoring/report/<session_id>', methods=['GET'])
    def get_score_report(session_id):
        """获取详细评分报告"""
        try:
            sp = patient_manager.get_session(session_id)
            if not sp:
                return APIResponse.error("会话不存在")
            
            report = sp.get_score_report()
            return APIResponse.success(report, "获取评分报告成功")
            
        except Exception as e:
            return APIResponse.error(f"获取评分报告失败: {str(e)}")
    
    @scoring_bp.route('/api/scoring/summary/<session_id>', methods=['GET'])
    def get_score_summary(session_id):
        """获取评分摘要"""
        try:
            sp = patient_manager.get_session(session_id)
            if not sp:
                return APIResponse.error("会话不存在")
            
            summary = sp.get_score_summary()
            return APIResponse.success(summary, "获取评分摘要成功")
            
        except Exception as e:
            return APIResponse.error(f"获取评分摘要失败: {str(e)}")
    
    @scoring_bp.route('/api/scoring/suggestions/<session_id>', methods=['GET'])
    def get_suggestions(session_id):
        """获取改进建议"""
        try:
            sp = patient_manager.get_session(session_id)
            if not sp:
                return APIResponse.error("会话不存在")
            
            suggestions = sp.get_suggestions()
            return APIResponse.success(suggestions, "获取建议成功")
            
        except Exception as e:
            return APIResponse.error(f"获取建议失败: {str(e)}")
    
    @scoring_bp.route('/api/scoring/export/<session_id>', methods=['GET'])
    def export_session_data(session_id):
        """导出完整会话数据"""
        try:
            sp = patient_manager.get_session(session_id)
            if not sp:
                return APIResponse.error("会话不存在")
            
            export_data = sp.export_session_data()
            return APIResponse.success(export_data, "导出数据成功")
            
        except Exception as e:
            return APIResponse.error(f"导出数据失败: {str(e)}")
    
    @scoring_bp.route('/api/scoring/config/<session_id>', methods=['GET'])
    def get_scoring_config(session_id):
        """获取评分系统配置信息"""
        try:
            sp = patient_manager.get_session(session_id)
            if not sp:
                return APIResponse.error("会话不存在")
            
            # 获取评分系统信息
            scoring_system = sp.scoring_system
            
            config = {
                "scoring_method": "AI智能评分",
                "threshold": getattr(scoring_system, 'threshold', 60.0),
                "ai_model": "gpt-3.5-turbo",
                "total_questions": len(scoring_system.question_items),
                "question_categories": list(set(item.category for item in scoring_system.question_items)),
                "supports_partial_matching": True,
                "features": [
                    "语义匹配分析",
                    "部分匹配得分",
                    "AI智能建议",
                    "专业性评估",
                    "上下文理解"
                ]
            }
            
            return APIResponse.success(config, "获取评分配置成功")
            
        except Exception as e:
            return APIResponse.error(f"获取评分配置失败: {str(e)}")
    
    @scoring_bp.route('/api/scoring/config/<session_id>', methods=['POST'])
    def update_scoring_config(session_id):
        """更新评分系统配置"""
        try:
            sp = patient_manager.get_session(session_id)
            if not sp:
                return APIResponse.error("会话不存在")
            
            data = request.get_json()
            new_threshold = data.get('threshold')
            
            if new_threshold is not None:
                if not (0 <= new_threshold <= 100):
                    return APIResponse.error("阈值必须在0-100之间")
                
                # 更新阈值
                scoring_system = sp.scoring_system
                scoring_system.threshold = new_threshold
                
                # 更新所有问题项的阈值
                for item in scoring_system.question_items:
                    item.threshold = new_threshold
                
                return APIResponse.success({"threshold": new_threshold}, "评分配置更新成功")
            
            return APIResponse.error("无有效配置更新")
            
        except Exception as e:
            return APIResponse.error(f"更新评分配置失败: {str(e)}")
    
    @scoring_bp.route('/api/scoring/stats', methods=['GET'])
    def get_global_stats():
        """获取全局统计信息"""
        try:
            all_summaries = patient_manager.get_all_sessions_summary()
            
            # 计算统计信息
            total_sessions = len(all_summaries)
            total_conversations = sum(s.get('conversation_count', 0) for s in all_summaries)
            
            # 获取所有评分信息
            scores = []
            scoring_methods = []
            for session_id in patient_manager.list_sessions():
                sp = patient_manager.get_session(session_id)
                if sp:
                    score_summary = sp.get_score_summary()
                    # 使用推荐得分（智能评分）
                    score = score_summary.get('recommended_score', score_summary.get('percentage', 0))
                    scores.append(score)
                    scoring_methods.append(score_summary.get('scoring_method', 'traditional'))
            
            avg_score = sum(scores) / len(scores) if scores else 0
            
            stats = {
                "total_sessions": total_sessions,
                "total_conversations": total_conversations,
                "average_score": round(avg_score, 2),
                "scoring_method": "AI智能评分" if "intelligent" in str(scoring_methods) else "传统评分",
                "score_distribution": {
                    "excellent": len([s for s in scores if s >= 90]),
                    "good": len([s for s in scores if 80 <= s < 90]),
                    "average": len([s for s in scores if 70 <= s < 80]),
                    "poor": len([s for s in scores if s < 70])
                }
            }
            
            return APIResponse.success(stats, "获取统计信息成功")
            
        except Exception as e:
            return APIResponse.error(f"获取统计信息失败: {str(e)}")
    
    return scoring_bp
