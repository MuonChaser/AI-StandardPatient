"""
重构的应用程序 - 基于现代化架构和依赖注入
"""
from flask import Flask, jsonify
from flask_cors import CORS
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from backend.core.config import get_config
except ImportError:
    # 如果配置模块不可用，使用默认配置
    class DefaultConfig:
        def __init__(self):
            self.server = type('ServerConfig', (), {
                'host': '0.0.0.0',
                'port': 8080,
                'debug': True,
                'cors_origins': ['*']
            })()
    
    def get_config():
        return DefaultConfig()

from backend.controllers.patient_controller import create_patient_blueprint
from backend.services.patient_service import PatientService


class Application:
    """应用程序类"""
    
    def __init__(self):
        """初始化应用程序"""
        self._config = get_config()
        self._app = self._create_flask_app()
        self._setup_services()
        self._register_blueprints()
        self._setup_error_handlers()
    
    def _create_flask_app(self) -> Flask:
        """创建Flask应用"""
        app = Flask(__name__)
        
        # 配置CORS
        CORS(app, origins=self._config.server.cors_origins)
        
        # Flask配置
        app.config['DEBUG'] = self._config.server.debug
        
        return app
    
    def _setup_services(self):
        """设置服务"""
        # 这里可以进行依赖注入的设置
        self._patient_service = PatientService()
    
    def _register_blueprints(self):
        """注册蓝图"""
        # 注册病人API蓝图
        patient_bp = create_patient_blueprint(self._patient_service)
        self._app.register_blueprint(patient_bp)
        
        # 注册健康检查端点
        self._app.add_url_rule('/health', 'health_check', self._health_check)
        self._app.add_url_rule('/api/health', 'api_health_check', self._health_check)
    
    def _setup_error_handlers(self):
        """设置错误处理器"""
        
        @self._app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "success": False,
                "message": "API端点不存在",
                "error_code": 404
            }), 404
        
        @self._app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                "success": False,
                "message": "服务器内部错误",
                "error_code": 500
            }), 500
        
        @self._app.errorhandler(400)
        def bad_request(error):
            return jsonify({
                "success": False,
                "message": "请求参数错误",
                "error_code": 400
            }), 400
    
    def _health_check(self):
        """健康检查端点"""
        return jsonify({
            "status": "healthy",
            "service": "AI Standard Patient",
            "version": "2.0.0",
            "timestamp": self._config.server.debug
        })
    
    @property
    def app(self) -> Flask:
        """获取Flask应用实例"""
        return self._app
    
    def run(self, host: str = None, port: int = None, debug: bool = None):
        """运行应用程序"""
        run_host = host or self._config.server.host
        run_port = port or self._config.server.port
        run_debug = debug if debug is not None else self._config.server.debug
        
        print(f"🚀 启动AI标准化病人服务...")
        print(f"📍 地址: http://{run_host}:{run_port}")
        print(f"🔧 调试模式: {'开启' if run_debug else '关闭'}")
        print(f"🏥 API文档: http://{run_host}:{run_port}/api/patient/")
        
        self._app.run(
            host=run_host,
            port=run_port,
            debug=run_debug
        )


def create_application() -> Application:
    """应用程序工厂函数"""
    return Application()


# 创建应用程序实例
application = create_application()
app = application.app  # Flask实例，用于部署


if __name__ == "__main__":
    # 开发服务器启动
    application.run()