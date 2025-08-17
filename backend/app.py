from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json
import time
from typing import Dict, List, Any
from datetime import datetime

# 添加项目根目录到路径，便于导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sp import SP
from sp_data import Sp_data
from engine.gpt import GPTEngine
from backend.config import Config

def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    from backend.config import config
    app.config.from_object(config[config_name])
    
    # 配置CORS
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    
    # 验证必要的环境变量
    config_errors = Config.validate_config()
    if config_errors:
        print("⚠️  配置警告:")
        for error in config_errors:
            print(f"   - {error}")
        print("   请检查环境变量设置或.env文件")
        print()
    
    return app

app = create_app(os.environ.get('ENVIRONMENT', 'development'))

# 全局变量存储SP实例和会话信息
current_sp_sessions: Dict[str, SP] = {}
session_metadata: Dict[str, Dict] = {}  # 存储会话元数据

def clean_expired_sessions():
    """清理过期的会话"""
    current_time = time.time()
    expired_sessions = []
    
    for session_id, metadata in session_metadata.items():
        if current_time - metadata.get('last_activity', 0) > app.config.get('SESSION_TIMEOUT', 3600):
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        if session_id in current_sp_sessions:
            del current_sp_sessions[session_id]
        if session_id in session_metadata:
            del session_metadata[session_id]
    
    return len(expired_sessions)

class APIResponse:
    """统一的API响应格式"""
    @staticmethod
    def success(data: Any = None, message: str = "操作成功"):
        return jsonify({
            "code": 200,
            "success": True,
            "message": message,
            "data": data
        })
    
    @staticmethod
    def error(message: str = "操作失败", code: int = 400):
        return jsonify({
            "code": code,
            "success": False,
            "message": message,
            "data": None
        }), code


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    # 清理过期会话
    expired_count = clean_expired_sessions()
    
    health_info = {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(current_sp_sessions),
        "expired_sessions_cleaned": expired_count,
        "config": {
            "debug": app.config.get('DEBUG', False),
            "model_name": app.config.get('MODEL_NAME', 'unknown'),
            "max_sessions": app.config.get('MAX_SESSIONS', 100)
        }
    }
    return APIResponse.success(health_info, "服务正常运行")

@app.route('/api/sp/presets', methods=['GET'])
def get_presets():
    """获取所有预设病例列表"""
    try:
        presets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'presets')
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
                            "description": f"{data.get('basics', {}).get('name', '未知')} - {data.get('disease', '未知疾病')}"
                        }
                        preset_files.append(preset_info)
                    except Exception as e:
                        print(f"读取预设文件 {file} 时出错: {e}")
        
        return APIResponse.success(preset_files, f"获取到 {len(preset_files)} 个预设病例")
    
    except Exception as e:
        return APIResponse.error(f"获取预设病例失败: {str(e)}")

@app.route('/api/sp/session/create', methods=['POST'])
def create_sp_session():
    """创建新的SP会话"""
    try:
        # 检查会话数量限制
        if len(current_sp_sessions) >= app.config.get('MAX_SESSIONS', 100):
            return APIResponse.error("已达到最大会话数量限制")
        
        data = request.json
        session_id = data.get('session_id')
        preset_file = data.get('preset_file')
        custom_data = data.get('custom_data')
        
        if not session_id:
            return APIResponse.error("session_id 不能为空")
        
        # 检查会话是否已存在
        if session_id in current_sp_sessions:
            return APIResponse.error(f"会话 {session_id} 已存在")
        
        # 创建SP数据对象
        sp_data = Sp_data()
        
        if preset_file:
            # 从预设文件加载
            preset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'presets', preset_file)
            if not os.path.exists(preset_path):
                return APIResponse.error(f"预设文件 {preset_file} 不存在")
            sp_data.load_from_json(preset_path)
        elif custom_data:
            # 从自定义数据加载
            sp_data.basics = custom_data.get("basics", {})
            sp_data.disease = custom_data.get("disease", "")
            sp_data.symptoms = custom_data.get("symptoms", [])
            sp_data.hiddens = custom_data.get("hiddens", [])
            sp_data.personalities = custom_data.get("personalities", [])
            sp_data.examinations = custom_data.get("examinations", [])
        else:
            return APIResponse.error("必须提供 preset_file 或 custom_data")
        
        # 创建SP实例
        engine = GPTEngine()
        sp = SP(sp_data, engine)
        current_sp_sessions[session_id] = sp
        
        # 记录会话元数据
        session_metadata[session_id] = {
            "created_at": time.time(),
            "last_activity": time.time(),
            "message_count": 0,
            "preset_file": preset_file,
            "patient_name": sp_data.basics.get("name", "未知") if isinstance(sp_data.basics, dict) else "未知"
        }
        
        session_info = {
            "session_id": session_id,
            "patient_name": session_metadata[session_id]["patient_name"],
            "disease": sp_data.disease,
            "symptoms": sp_data.symptoms,
            "created_at": datetime.fromtimestamp(session_metadata[session_id]["created_at"]).isoformat()
        }
        
        return APIResponse.success(session_info, f"SP会话 {session_id} 创建成功")
    
    except Exception as e:
        return APIResponse.error(f"创建SP会话失败: {str(e)}")

@app.route('/api/sp/session/<session_id>/chat', methods=['POST'])
def chat_with_sp(session_id: str):
    """与SP进行对话"""
    try:
        if session_id not in current_sp_sessions:
            return APIResponse.error(f"会话 {session_id} 不存在，请先创建会话")
        
        data = request.json
        message = data.get('message')
        
        if not message:
            return APIResponse.error("消息内容不能为空")
        
        sp = current_sp_sessions[session_id]
        response = sp.speak(message)
        
        # 更新会话活动时间和消息计数
        if session_id in session_metadata:
            session_metadata[session_id]["last_activity"] = time.time()
            session_metadata[session_id]["message_count"] += 1
        
        chat_response = {
            "session_id": session_id,
            "user_message": message,
            "sp_response": response,
            "timestamp": datetime.now().isoformat(),
            "message_count": session_metadata.get(session_id, {}).get("message_count", 0)
        }
        
        return APIResponse.success(chat_response, "对话成功")
    
    except Exception as e:
        return APIResponse.error(f"对话失败: {str(e)}")

@app.route('/api/sp/session/<session_id>/history', methods=['GET'])
def get_chat_history(session_id: str):
    """获取对话历史"""
    try:
        if session_id not in current_sp_sessions:
            return APIResponse.error(f"会话 {session_id} 不存在")
        
        sp = current_sp_sessions[session_id]
        # 过滤掉系统消息，只返回用户和助手的对话
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
        
        return APIResponse.success({
            "session_id": session_id,
            "total_messages": len(history),
            "history": history
        }, "获取对话历史成功")
    
    except Exception as e:
        return APIResponse.error(f"获取对话历史失败: {str(e)}")

@app.route('/api/sp/session/<session_id>/info', methods=['GET'])
def get_session_info(session_id: str):
    """获取会话信息"""
    try:
        if session_id not in current_sp_sessions:
            return APIResponse.error(f"会话 {session_id} 不存在")
        
        sp = current_sp_sessions[session_id]
        sp_data = sp.data
        
        session_info = {
            "session_id": session_id,
            "basics": sp_data.basics,
            "disease": sp_data.disease,
            "symptoms": sp_data.symptoms,
            "personalities": sp_data.personalities,
            "examinations": sp_data.examinations,
            "total_messages": len([m for m in sp.memories if m["role"] in ["user", "assistant"]]) // 2
        }
        
        return APIResponse.success(session_info, "获取会话信息成功")
    
    except Exception as e:
        return APIResponse.error(f"获取会话信息失败: {str(e)}")

@app.route('/api/sp/sessions', methods=['GET'])
def list_sessions():
    """列出所有活跃的会话"""
    try:
        # 清理过期会话
        clean_expired_sessions()
        
        sessions = []
        for session_id, sp in current_sp_sessions.items():
            metadata = session_metadata.get(session_id, {})
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
        
        return APIResponse.success({
            "total_sessions": len(sessions),
            "max_sessions": app.config.get('MAX_SESSIONS', 100),
            "sessions": sessions
        }, f"获取到 {len(sessions)} 个活跃会话")
    
    except Exception as e:
        return APIResponse.error(f"获取会话列表失败: {str(e)}")

@app.route('/api/sp/session/<session_id>', methods=['DELETE'])
def delete_session(session_id: str):
    """删除指定会话"""
    try:
        if session_id not in current_sp_sessions:
            return APIResponse.error(f"会话 {session_id} 不存在")
        
        # 获取会话信息用于返回
        session_info = session_metadata.get(session_id, {})
        
        # 删除会话和元数据
        del current_sp_sessions[session_id]
        if session_id in session_metadata:
            del session_metadata[session_id]
        
        return APIResponse.success({
            "session_id": session_id,
            "patient_name": session_info.get("patient_name", "未知"),
            "message_count": session_info.get("message_count", 0)
        }, f"会话 {session_id} 已删除")
    
    except Exception as e:
        return APIResponse.error(f"删除会话失败: {str(e)}")

@app.route('/api/sp/data/validate', methods=['POST'])
def validate_sp_data():
    """验证SP数据格式"""
    try:
        data = request.json
        
        # 基本字段验证
        required_fields = ["basics", "disease", "symptoms"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return APIResponse.error(f"缺少必需字段: {', '.join(missing_fields)}")
        
        # 数据类型验证
        if not isinstance(data.get("symptoms"), list):
            return APIResponse.error("symptoms 字段必须是数组")
        
        if not isinstance(data.get("disease"), str):
            return APIResponse.error("disease 字段必须是字符串")
        
        validation_result = {
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
        
        return APIResponse.success(validation_result, "数据验证成功")
    
    except Exception as e:
        return APIResponse.error(f"数据验证失败: {str(e)}")

@app.errorhandler(404)
def not_found(error):
    return APIResponse.error("接口不存在", 404)

@app.errorhandler(500)
def internal_error(error):
    return APIResponse.error("服务器内部错误", 500)

if __name__ == '__main__':
    print("🏥 AI标准化病人后端服务启动中...")
    print("📋 可用接口:")
    print("  GET  /api/health                    - 健康检查")
    print("  GET  /api/sp/presets                - 获取预设病例")
    print("  POST /api/sp/session/create         - 创建SP会话")
    print("  POST /api/sp/session/<id>/chat      - 与SP对话")
    print("  GET  /api/sp/session/<id>/history   - 获取对话历史")
    print("  GET  /api/sp/session/<id>/info      - 获取会话信息")
    print("  GET  /api/sp/sessions               - 获取所有会话")
    print("  DELETE /api/sp/session/<id>         - 删除会话")
    print("  POST /api/sp/data/validate          - 验证SP数据")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=3000)