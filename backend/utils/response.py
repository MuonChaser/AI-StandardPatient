"""
API响应工具类
"""
from flask import jsonify
from typing import Any


class APIResponse:
    """统一的API响应格式"""
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功"):
        """成功响应"""
        return jsonify({
            "code": 200,
            "success": True,
            "message": message,
            "data": data
        })
    
    @staticmethod
    def error(message: str = "操作失败", code: int = 400):
        """错误响应"""
        return jsonify({
            "code": code,
            "success": False,
            "message": message,
            "data": None
        }), code
