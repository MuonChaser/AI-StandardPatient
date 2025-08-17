#!/usr/bin/env python3
"""
前端静态文件服务器
用于在开发环境中提供前端文件服务
"""

import os
import sys
import time
import http.server
import socketserver
import webbrowser
from pathlib import Path

def start_frontend_server(port=8080):
    """启动前端服务器"""
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
        
        def do_GET(self):
            """处理GET请求，支持SPA路由"""
            # 如果请求根路径，直接返回index.html
            if self.path == '/':
                self.path = '/index.html'
            
            # 检查文件是否存在，如果不存在且不是API请求，返回index.html
            # 这样可以支持前端路由
            if not os.path.exists(self.path[1:]) and not self.path.startswith('/api'):
                # 如果是请求静态资源文件但不存在，返回404
                if any(self.path.endswith(ext) for ext in ['.js', '.css', '.png', '.jpg', '.ico']):
                    super().do_GET()
                    return
                # 否则返回index.html，支持前端路由
                self.path = '/index.html'
            
            super().do_GET()
        
        def do_OPTIONS(self):
            """处理OPTIONS请求，用于CORS预检"""
            self.send_response(200)
            self.end_headers()
        
        def log_message(self, format, *args):
            """自定义日志格式"""
            timestamp = time.strftime('%H:%M:%S')
            print(f"[{timestamp}] {self.address_string()} - {format % args}")
    
    try:
        with socketserver.TCPServer(("", port), CORSHTTPRequestHandler) as httpd:
            print("🌐 AI标准化病人前端服务")
            print("=" * 40)
            print(f"📍 服务地址: http://localhost:{port}")
            print(f"📂 服务目录: {frontend_dir}")
            print("=" * 40)
            print("💡 使用说明:")
            print("  1. 确保后端服务正在运行 (端口8080)")
            print("  2. 在浏览器中打开前端地址")
            print("  3. 创建会话开始与AI病人对话")
            print("=" * 40)
            print("⌨️  按 Ctrl+C 停止服务")
            print()
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 前端服务已停止")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ 端口 {port} 已被占用，请尝试其他端口")
            print(f"   使用方法: python {sys.argv[0]} [端口号]")
        else:
            print(f"❌ 启动服务器时出错: {e}")
    except Exception as e:
        print(f"❌ 意外错误: {e}")

def main():
    """主函数"""
    port = 8080
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ 端口号必须是数字")
            sys.exit(1)
    
    # 检查前端文件是否存在
    frontend_dir = Path(__file__).parent
    index_file = frontend_dir / 'index.html'
    
    if not index_file.exists():
        print("❌ 未找到 index.html 文件")
        print(f"   请确保在 {frontend_dir} 目录下运行此脚本")
        sys.exit(1)
    
    start_frontend_server(port)

if __name__ == '__main__':
    main()
