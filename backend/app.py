"""
Flask应用创建工厂
"""
from flask import Flask
from flask_cors import CORS
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config, Config
from models.session import SessionManager
from api.health import create_health_blueprint
from api.preset import create_preset_blueprint
from api.sp import create_sp_blueprint
from utils.response import APIResponse


def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
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
    
    # 创建会话管理器
    session_manager = SessionManager(
        max_sessions=app.config.get('MAX_SESSIONS', 100),
        session_timeout=app.config.get('SESSION_TIMEOUT', 3600)
    )
    
    # 注册蓝图
    app.register_blueprint(create_health_blueprint(session_manager))
    app.register_blueprint(create_preset_blueprint())
    app.register_blueprint(create_sp_blueprint(session_manager))
    # 注册检查报告API
    from api.exam import create_exam_blueprint
    app.register_blueprint(create_exam_blueprint(session_manager))
    # 注册prompt管理API
    from backend.prompt_api import prompt_bp
    app.register_blueprint(prompt_bp)
    # 注册评分系统API
    from api.scoring import create_scoring_blueprint
    app.register_blueprint(create_scoring_blueprint())
    
    # 错误处理器
    @app.errorhandler(404)
    def not_found(error):
        return APIResponse.error("接口不存在", 404)
    
    @app.errorhandler(500)
    def internal_error(error):
        return APIResponse.error("服务器内部错误", 500)
    
    return app


def print_available_routes():
    """打印可用的API路由"""
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


if __name__ == '__main__':
    # 创建应用
    app = create_app(os.environ.get('ENVIRONMENT', 'development'))
    
    # 打印路由信息
    print_available_routes()
    
    # 启动应用
    app.run(debug=True, host='0.0.0.0', port=3000)
