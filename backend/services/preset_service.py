"""
预设病例服务
"""
import os
import json
from typing import List, Dict, Any


class PresetService:
    """预设病例服务类"""
    
    @staticmethod
    def get_presets_directory() -> str:
        """获取预设文件目录"""
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'presets')
    
    @staticmethod
    def get_all_presets() -> List[Dict[str, Any]]:
        """获取所有预设病例列表"""
        presets_dir = PresetService.get_presets_directory()
        preset_files = []
        
        if os.path.exists(presets_dir):
            for file in os.listdir(presets_dir):
                if file.endswith('.json'):
                    try:
                        file_path = os.path.join(presets_dir, file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        preset_info = {
                            "filename": file,
                            "name": data.get("basics", {}).get("name", "未知"),
                            "disease": data.get("disease", "未知疾病"),
                            "symptoms": data.get("symptoms", []),
                            "description": f"{data.get('basics', {}).get('name', '未知')} - {data.get('disease', '未知疾病')}"  # 显示为"人名-病名"
                        }
                        preset_files.append(preset_info)
                    except Exception as e:
                        print(f"读取预设文件 {file} 时出错: {e}")
        
        return preset_files
    
    @staticmethod
    def get_preset_path(filename: str) -> str:
        """获取预设文件的完整路径"""
        return os.path.join(PresetService.get_presets_directory(), filename)
    
    @staticmethod
    def preset_exists(filename: str) -> bool:
        """检查预设文件是否存在"""
        return os.path.exists(PresetService.get_preset_path(filename))
