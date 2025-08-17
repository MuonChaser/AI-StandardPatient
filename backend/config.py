import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

class Config:
    """应用配置类"""
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 3000))
    
    # API配置
    API_KEY = os.environ.get('API_KEY', '')
    MODEL_BASE = os.environ.get('MODEL_BASE', 'https://xiaoai.plus/v1')
    MODEL_NAME = os.environ.get('MODEL_NAME', 'gpt-4o')
    
    # CORS配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # 会话配置
    MAX_SESSIONS = int(os.environ.get('MAX_SESSIONS', 100))
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 秒
    
    @classmethod
    def validate_config(cls):
        """验证配置"""
        errors = []
        
        if not cls.API_KEY:
            errors.append("API_KEY 环境变量未设置")
        
        if not cls.MODEL_BASE:
            errors.append("MODEL_BASE 环境变量未设置")
            
        if not cls.MODEL_NAME:
            errors.append("MODEL_NAME 环境变量未设置")
        
        return errors

# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True

# 生产环境配置
class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key'

# 测试环境配置
class TestingConfig(Config):
    TESTING = True
    DEBUG = True

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
