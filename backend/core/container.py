"""
依赖注入容器 - 管理所有依赖关系
"""
from typing import Dict, Type, TypeVar, Any, Callable
from functools import wraps


T = TypeVar('T')


class DIContainer:
    """依赖注入容器"""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
    
    def register_singleton(self, interface: Type[T], implementation: T) -> None:
        """注册单例服务"""
        self._singletons[interface] = implementation
    
    def register_transient(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """注册瞬时服务（每次获取都创建新实例）"""
        self._factories[interface] = factory
    
    def register_service(self, interface: Type[T], implementation: Type[T]) -> None:
        """注册服务类型"""
        self._services[interface] = implementation
    
    def get(self, interface: Type[T]) -> T:
        """获取服务实例"""
        # 优先检查单例
        if interface in self._singletons:
            return self._singletons[interface]
        
        # 检查工厂方法
        if interface in self._factories:
            return self._factories[interface]()
        
        # 检查注册的服务类型
        if interface in self._services:
            implementation = self._services[interface]
            instance = implementation()
            return instance
        
        raise ValueError(f"Service {interface} not registered")
    
    def create_scope(self) -> 'DIContainer':
        """创建新的作用域"""
        scoped_container = DIContainer()
        scoped_container._services = self._services.copy()
        scoped_container._singletons = self._singletons.copy()
        scoped_container._factories = self._factories.copy()
        return scoped_container


# 全局容器实例
container = DIContainer()


def inject(interface: Type[T]):
    """依赖注入装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            service = container.get(interface)
            return func(service, *args, **kwargs)
        return wrapper
    return decorator


def service(interface: Type[T]):
    """服务注册装饰器"""
    def decorator(cls):
        container.register_service(interface, cls)
        return cls
    return decorator