"""
预设病例API路由
"""
from flask import Blueprint

from utils.response import APIResponse
from services.preset_service import PresetService


def create_preset_blueprint():
    """创建预设病例蓝图"""
    preset_bp = Blueprint('preset', __name__)
    
    @preset_bp.route('/api/sp/presets', methods=['GET'])
    def get_presets():
        """获取所有预设病例列表"""
        try:
            preset_files = PresetService.get_all_presets()
            return APIResponse.success(preset_files, f"获取到 {len(preset_files)} 个预设病例")
        
        except Exception as e:
            return APIResponse.error(f"获取预设病例失败: {str(e)}")
    
    return preset_bp
