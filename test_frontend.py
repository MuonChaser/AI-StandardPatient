#!/usr/bin/env python3
"""
快速测试前端服务器
"""

import subprocess
import time
import webbrowser
from pathlib import Path

def test_frontend():
    """测试前端服务器"""
    print("🧪 测试前端服务器...")
    
    frontend_dir = Path(__file__).parent / 'frontend'
    if not frontend_dir.exists():
        print("❌ frontend目录不存在")
        return
    
    # 启动前端服务器
    try:
        print("🚀 启动前端服务器...")
        process = subprocess.Popen(
            ['python3', 'server.py', '3001'],
            cwd=str(frontend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待启动
        time.sleep(2)
        
        if process.poll() is None:
            print("✅ 前端服务器启动成功")
            print("📋 访问地址:")
            print("   http://localhost:3001")
            print("   http://localhost:3001/")
            print("   http://localhost:3001/index.html")
            

            input()
            
            # 停止服务器
            process.terminate()
            process.wait()
            print("✅ 前端服务器已停止")
            
        else:
            stdout, stderr = process.communicate()
            print("❌ 前端服务器启动失败")
            print(f"stdout: {stdout.decode()}")
            print(f"stderr: {stderr.decode()}")
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")

if __name__ == '__main__':
    test_frontend()
