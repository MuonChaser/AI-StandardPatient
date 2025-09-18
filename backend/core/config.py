"""
配置管理 - 统一管理所有配置项
"""
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "ai_patient"
    username: str = "postgres"
    password: str = ""


@dataclass
class AIConfig:
    """AI引擎配置"""
    default_engine: str = "gpt"
    api_key: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000
    temperature: float = 0.7


@dataclass
class ScoringConfig:
    """评分系统配置"""
    enable_detailed_scoring: bool = True
    scoring_threshold: float = 0.7
    max_suggestions: int = 5


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    cors_origins: list = field(default_factory=lambda: ["*"])


@dataclass
class ApplicationConfig:
    """应用程序主配置"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    
    # 路径配置
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    prompts_dir: Path = field(init=False)
    presets_dir: Path = field(init=False)
    
    def __post_init__(self):
        self.prompts_dir = self.base_dir / "prompts"
        self.presets_dir = self.base_dir / "presets"
        
        # 从环境变量加载配置
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # AI配置
        self.ai.api_key = os.getenv("OPENAI_API_KEY", self.ai.api_key)
        self.ai.model = os.getenv("AI_MODEL", self.ai.model)
        
        # 服务器配置
        self.server.port = int(os.getenv("PORT", self.server.port))
        self.server.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # 数据库配置
        if db_url := os.getenv("DATABASE_URL"):
            # 解析数据库URL（如果需要的话）
            pass


class ConfigManager:
    """配置管理器"""
    
    _instance: Optional[ApplicationConfig] = None
    
    @classmethod
    def get_config(cls) -> ApplicationConfig:
        """获取配置单例"""
        if cls._instance is None:
            cls._instance = ApplicationConfig()
        return cls._instance
    
    @classmethod
    def reload_config(cls) -> ApplicationConfig:
        """重新加载配置"""
        cls._instance = ApplicationConfig()
        return cls._instance


# 便捷访问函数
def get_config() -> ApplicationConfig:
    """获取应用配置"""
    return ConfigManager.get_config()