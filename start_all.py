#!/usr/bin/env python3
"""
AI标准化病人系统一键启动脚本
同时启动后端API服务和前端Web界面
"""

import os
import sys
import time
import signal
import subprocess
import threading
import webbrowser
from pathlib import Path

os.environ['OPENAI_API_KEY'] = "sk-pkas0IqXTrYRK17XxTu7sLxW3yAtPvHxuVzj6n4usoMpD6E8"


class ServiceManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
    def check_dependencies(self):
        """检查依赖"""
        print("🔍 检查项目依赖...")
        
        # 检查Python虚拟环境
        venv_python = self.project_root / '.venv' / 'bin' / 'python'
        if venv_python.exists():
            self.python_cmd = str(venv_python)
            print(f"✅ 使用虚拟环境: {self.python_cmd}")
        else:
            self.python_cmd = sys.executable
            print(f"⚠️  使用系统Python: {self.python_cmd}")
        
        # 检查关键文件
        required_files = [
            'backend/app.py',
            'frontend/index.html',
            'frontend/server.py'
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                print(f"❌ 缺少文件: {file_path}")
                return False
            print(f"✅ {file_path}")
        
        return True
    
    def start_backend(self):
        """启动后端服务"""
        print("\n🔧 启动后端服务...")
        
        backend_script = self.project_root / 'backend' / 'app.py'
        
        try:
            self.backend_process = subprocess.Popen(
                [self.python_cmd, str(backend_script)],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待后端启动
            time.sleep(3)
            
            if self.backend_process.poll() is None:
                print("✅ 后端服务启动成功 (端口: 3000)")
                return True
            else:
                stdout, stderr = self.backend_process.communicate()
                print(f"❌ 后端服务启动失败:")
                print(f"   stdout: {stdout}")
                print(f"   stderr: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 启动后端服务时出错: {e}")
            return False
    
    def start_frontend(self):
        """启动前端服务"""
        print("\n🌐 启动前端服务...")
        
        frontend_script = self.project_root / 'frontend' / 'server.py'
        
        try:
            self.frontend_process = subprocess.Popen(
                [self.python_cmd, str(frontend_script), '8080'],
                cwd=str(self.project_root / 'frontend'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待前端启动
            time.sleep(2)
            
            if self.frontend_process.poll() is None:
                print("✅ 前端服务启动成功 (端口: 8080)")
                return True
            else:
                stdout, stderr = self.frontend_process.communicate()
                print(f"❌ 前端服务启动失败:")
                print(f"   stdout: {stdout}")
                print(f"   stderr: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 启动前端服务时出错: {e}")
            return False
    
    def open_browser(self):
        pass
    
    def monitor_services(self):
        """监控服务状态"""
        while self.running:
            time.sleep(5)
            
            # 检查后端状态
            if self.backend_process and self.backend_process.poll() is not None:
                print("⚠️  后端服务已停止")
                self.running = False
                break
            
            # 检查前端状态
            if self.frontend_process and self.frontend_process.poll() is not None:
                print("⚠️  前端服务已停止")
                self.running = False
                break
    
    def cleanup(self):
        """清理资源"""
        print("\n🧹 正在停止服务...")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("✅ 后端服务已停止")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                print("⚠️  强制停止后端服务")
            except Exception as e:
                print(f"⚠️  停止后端服务时出错: {e}")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                print("✅ 前端服务已停止")
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                print("⚠️  强制停止前端服务")
            except Exception as e:
                print(f"⚠️  停止前端服务时出错: {e}")
    
    def run(self):
        """运行服务管理器"""
        try:
            print("🏥 AI标准化病人系统")
            print("=" * 60)
            
            # 检查依赖
            if not self.check_dependencies():
                print("\n❌ 依赖检查失败，无法启动服务")
                return
            
            # 启动后端
            if not self.start_backend():
                print("\n❌ 后端服务启动失败")
                return
            
            # 启动前端
            if not self.start_frontend():
                print("\n❌ 前端服务启动失败")
                self.cleanup()
                return
            
            # 打开浏览器
            self.open_browser()
            
            # 显示访问信息
            print("\n" + "=" * 60)
            print("🎉 所有服务启动成功！")
            print()
            print("📋 服务信息:")
            print("   后端API: http://localhost:8080/api")
            print("   前端界面: http://localhost:3000")
            print("   直接访问: http://localhost:3000/ (推荐)")
            print()
            print("💡 使用指南:")
            print("   1. 点击上方链接或在浏览器中访问前端地址")
            print("   2. 在前端界面创建会话")
            print("   3. 选择预设病例或自定义病例") 
            print("   4. 开始与AI标准化病人对话")
            print()
            print("⌨️  按 Ctrl+C 停止所有服务")
            print("=" * 60)
            
            # 监控服务
            monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
            monitor_thread.start()
            
            # 等待用户中断
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，正在停止服务...")
            self.running = False
        except Exception as e:
            print(f"\n❌ 运行时错误: {e}")
            self.running = False
        finally:
            self.cleanup()
            print("\n🎬 所有服务已停止，谢谢使用！")

def check_ports():
    """检查端口是否被占用"""
    import socket
    
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return False
            except OSError:
                return True
    
    print("🔍 检查端口占用情况...")
    
    if is_port_in_use(8080):
        print("⚠️  端口 8080 已被占用，后端服务可能无法启动")
        return False
    
    if is_port_in_use(3000):
        print("⚠️  端口 3000 已被占用，前端服务可能无法启动")
        return False
    
    print("✅ 端口检查通过")
    return True

def main():
    """主函数"""
    # 设置信号处理
    def signal_handler(signum, frame):
        print("\n\n🛑 接收到停止信号...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 检查端口
    if not check_ports():
        print("\n💡 解决方案:")
        print("   1. 停止占用端口的程序")
        print("   2. 修改配置文件中的端口设置")
        print("   3. 等待几分钟后重试")
        return
    
    # 启动服务管理器
    manager = ServiceManager()
    manager.run()

if __name__ == '__main__':
    main()
