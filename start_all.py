#!/usr/bin/env python3
"""
AI标准化病人系统一键启动脚本
同时启动后        # 设置日志格式
        log_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        
        # 主服务管理器日志记录器
        self.logger = logging.getLogger('ServiceManager')
        self.logger.setLevel(logging.WARNING)  # 只显示警告和错误端Web界面
支持持续监测、自动重启和日志记录
"""

import os
import sys
import time
import signal
import subprocess
import threading
import webbrowser
import socket
import platform
import logging
import requests
from datetime import datetime
from pathlib import Path

os.environ['OPENAI_API_KEY'] = "sk-pkas0IqXTrYRK17XxTu7sLxW3yAtPvHxuVzj6n4usoMpD6E8"


class ServiceManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        self.restart_count = {'backend': 0, 'frontend': 0}
        self.max_restarts = 5
        
        # 首先设置python_cmd
        venv_python = self.project_root / '.venv' / 'bin' / 'python'
        if venv_python.exists():
            self.python_cmd = str(venv_python)
        else:
            self.python_cmd = sys.executable
            
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志记录"""
        # 创建logs目录
        log_dir = self.project_root / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # 设置日志格式
        log_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        
        # 主日志记录器
        self.logger = logging.getLogger('ServiceManager')
        self.logger.setLevel(logging.INFO)
        
        # 文件处理器
        file_handler = logging.FileHandler(
            log_dir / f'service_manager_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        file_handler.setFormatter(log_format)
        self.logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        self.logger.addHandler(console_handler)
        
        # 后端日志记录器
        self.backend_logger = logging.getLogger('Backend')
        self.backend_logger.setLevel(logging.ERROR)  # 只显示错误
        backend_handler = logging.FileHandler(
            log_dir / f'backend_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        backend_handler.setFormatter(log_format)
        self.backend_logger.addHandler(backend_handler)
        
        # 前端日志记录器
        self.frontend_logger = logging.getLogger('Frontend')
        self.frontend_logger.setLevel(logging.ERROR)  # 只显示错误
        frontend_handler = logging.FileHandler(
            log_dir / f'frontend_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        frontend_handler.setFormatter(log_format)
        self.frontend_logger.addHandler(frontend_handler)
        
    def check_dependencies(self):
        """检查依赖"""
        print("🔧 检查系统依赖...")
        
        # 检查关键文件
        required_files = [
            'backend/app.py',
            'frontend/index.html',
            'frontend/server.py'
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.logger.error(f"❌ 缺少关键文件: {file_path}")
                return False
        
        print("✅ 依赖检查完成")
        return True
        
        return True
    
    def _log_process_output(self, process, logger, service_name):
        """持续读取进程输出并记录到日志（主日志和后端日志）"""
        def log_stdout():
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    if line.strip():
                        logger.info(f"[{service_name}] {line.strip()}")
                        self.logger.info(f"[{service_name}] {line.strip()}")  # 同步到主日志

        def log_stderr():
            if process.stderr:
                for line in iter(process.stderr.readline, ''):
                    if line.strip():
                        logger.error(f"[{service_name}] ERROR: {line.strip()}")
                        self.logger.error(f"[{service_name}] ERROR: {line.strip()}")  # 同步到主日志

        # 启动输出监控线程
        stdout_thread = threading.Thread(target=log_stdout, daemon=True)
        stderr_thread = threading.Thread(target=log_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()
        return stdout_thread, stderr_thread

    def start_backend(self):
        """启动后端服务"""
        self.logger.info("启动后端服务...")
        
        backend_script = self.project_root / 'backend' / 'app.py'
        
        try:
            self.backend_process = subprocess.Popen(
                [self.python_cmd, str(backend_script)],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 启动输出监控
            self._log_process_output(self.backend_process, self.backend_logger, "Backend")
            
            # 等待后端启动
            self.logger.info("等待后端服务启动...")
            time.sleep(3)
            
            if self.backend_process.poll() is None:
                self.backend_logger.info("后端服务启动成功 (端口: 3000)")
                return True
            else:
                self.backend_logger.error("后端服务启动失败")
                return False
                
        except Exception as e:
            self.backend_logger.error(f"启动后端服务时出错: {e}")
            import traceback
            self.backend_logger.error(f"详细错误信息:\n{traceback.format_exc()}")
            return False
    
    def start_frontend(self):
        """启动前端服务"""
        self.logger.info("启动前端服务...")
        
        frontend_script = self.project_root / 'frontend' / 'server.py'
        
        try:
            self.frontend_process = subprocess.Popen(
                [self.python_cmd, str(frontend_script), '8080'],
                cwd=str(self.project_root / 'frontend'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 启动输出监控
            self._log_process_output(self.frontend_process, self.frontend_logger, "Frontend")
            
            # 等待前端启动
            self.logger.info("等待前端服务启动...")
            time.sleep(2)
            
            if self.frontend_process.poll() is None:
                self.frontend_logger.info("前端服务启动成功 (端口: 8080)")
                return True
            else:
                self.frontend_logger.error("前端服务启动失败")
                return False
                
        except Exception as e:
            self.frontend_logger.error(f"启动前端服务时出错: {e}")
            import traceback
            self.frontend_logger.error(f"详细错误信息:\n{traceback.format_exc()}")
            return False
    
    def check_service_health(self, service_type):
        """检查服务健康状态"""
        try:
            if service_type == 'backend':
                response = requests.get('http://localhost:3000/api/health', timeout=5)
                return response.status_code == 200
            elif service_type == 'frontend':
                response = requests.get('http://localhost:8080', timeout=5)
                return response.status_code == 200
        except:
            return False
        return False
    
    def restart_service(self, service_type):
        """重启指定服务"""
        if service_type == 'backend':
            if self.restart_count['backend'] >= self.max_restarts:
                self.backend_logger.error(f"后端服务重启次数已达上限 ({self.max_restarts})")
                return False
            
            self.backend_logger.warning("检测到后端服务异常，正在重启...")
            
            # 清理旧进程
            if self.backend_process:
                try:
                    self.backend_process.terminate()
                    self.backend_process.wait(timeout=5)
                except:
                    try:
                        self.backend_process.kill()
                    except:
                        pass
            
            # 重启服务
            if self.start_backend():
                self.restart_count['backend'] += 1
                self.backend_logger.info(f"后端服务重启成功 (第{self.restart_count['backend']}次)")
                return True
            else:
                self.backend_logger.error("后端服务重启失败")
                return False
                
        elif service_type == 'frontend':
            if self.restart_count['frontend'] >= self.max_restarts:
                self.frontend_logger.error(f"前端服务重启次数已达上限 ({self.max_restarts})")
                return False
            
            self.frontend_logger.warning("检测到前端服务异常，正在重启...")
            
            # 清理旧进程
            if self.frontend_process:
                try:
                    self.frontend_process.terminate()
                    self.frontend_process.wait(timeout=5)
                except:
                    try:
                        self.frontend_process.kill()
                    except:
                        pass
            
            # 重启服务
            if self.start_frontend():
                self.restart_count['frontend'] += 1
                self.frontend_logger.info(f"前端服务重启成功 (第{self.restart_count['frontend']}次)")
                return True
            else:
                self.frontend_logger.error("前端服务重启失败")
                return False
        
        return False
    
    def open_browser(self):
        pass
    
    def monitor_services(self):
        """监控服务状态"""
        check_interval = 30  # 减少检查频率到30秒
        print("🔍 开始监控服务状态...")
        consecutive_failures = {'backend': 0, 'frontend': 0}
        max_consecutive_failures = 3
        
        while self.running:
            time.sleep(check_interval)
            
            if not self.running:
                break
            
            try:
                # 检查后端进程状态
                backend_process_alive = self.backend_process and self.backend_process.poll() is None
                backend_health = self.check_service_health('backend')
                
                if not backend_process_alive:
                    self.logger.error("❌ 后端进程已停止")
                    consecutive_failures['backend'] += 1
                    if consecutive_failures['backend'] <= max_consecutive_failures:
                        if self.restart_service('backend'):
                            consecutive_failures['backend'] = 0
                            print("✅ 后端服务重启成功")
                        else:
                            self.logger.error(f"❌ 后端服务重启失败 (尝试 {consecutive_failures['backend']}/{max_consecutive_failures})")
                elif not backend_health:
                    consecutive_failures['backend'] += 1
                    if consecutive_failures['backend'] <= max_consecutive_failures:
                        self.logger.warning(f"⚠️ 后端健康检查失败 (尝试 {consecutive_failures['backend']}/{max_consecutive_failures})")
                        if self.restart_service('backend'):
                            consecutive_failures['backend'] = 0
                            print("✅ 后端服务重启成功")
                else:
                    consecutive_failures['backend'] = 0
                
                # 检查前端进程状态
                frontend_process_alive = self.frontend_process and self.frontend_process.poll() is None
                frontend_health = self.check_service_health('frontend')
                
                if not frontend_process_alive:
                    self.logger.error("❌ 前端进程已停止")
                    consecutive_failures['frontend'] += 1
                    if consecutive_failures['frontend'] <= max_consecutive_failures:
                        if self.restart_service('frontend'):
                            consecutive_failures['frontend'] = 0
                            print("✅ 前端服务重启成功")
                        else:
                            self.logger.error(f"❌ 前端服务重启失败 (尝试 {consecutive_failures['frontend']}/{max_consecutive_failures})")
                elif not frontend_health:
                    consecutive_failures['frontend'] += 1
                    if consecutive_failures['frontend'] <= max_consecutive_failures:
                        self.logger.warning(f"⚠️ 前端健康检查失败 (尝试 {consecutive_failures['frontend']}/{max_consecutive_failures})")
                        if self.restart_service('frontend'):
                            consecutive_failures['frontend'] = 0
                            print("✅ 前端服务重启成功")
                else:
                    consecutive_failures['frontend'] = 0
                
                # 只在达到最大重试次数时才退出
                if (consecutive_failures['backend'] >= max_consecutive_failures or 
                    consecutive_failures['frontend'] >= max_consecutive_failures):
                    self.logger.error("❌ 服务多次重启失败，等待60秒后继续尝试...")
                    time.sleep(60)
                    consecutive_failures = {'backend': 0, 'frontend': 0}  # 重置计数器
                    
            except KeyboardInterrupt:
                print("\n🛑 收到停止信号")
                break
            except Exception as e:
                self.logger.error(f"❌ 监控过程出错: {e}")
                import traceback
                self.logger.error(f"详细错误信息:\n{traceback.format_exc()}")
                time.sleep(10)  # 出错后等待10秒再继续
        
        self.logger.info("服务监控已停止")
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("正在停止服务...")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                self.backend_logger.info("后端服务已停止")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                self.backend_logger.warning("强制停止后端服务")
            except Exception as e:
                self.backend_logger.error(f"停止后端服务时出错: {e}")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                self.frontend_logger.info("前端服务已停止")
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                self.frontend_logger.warning("强制停止前端服务")
            except Exception as e:
                self.frontend_logger.error(f"停止前端服务时出错: {e}")
    
    def log_system_info(self):
        """记录系统信息"""
        self.logger.info("=" * 60)
        self.logger.info("AI标准化病人系统启动")
        self.logger.info(f"系统平台: {platform.system()} {platform.release()}")
        self.logger.info(f"Python版本: {sys.version}")
        self.logger.info(f"工作目录: {self.project_root}")
        self.logger.info(f"Python解释器: {self.python_cmd}")
        self.logger.info("=" * 60)
    
    def run(self):
        """运行服务管理器"""
        try:
            print("🏥 AI标准化病人系统启动...")
            
            # 检查依赖
            if not self.check_dependencies():
                self.logger.error("❌ 依赖检查失败")
                return
            
            # 启动后端
            if not self.start_backend():
                self.logger.error("❌ 后端服务启动失败")
                return
            
            # 启动前端
            if not self.start_frontend():
                self.logger.error("❌ 前端服务启动失败")
                self.cleanup()
                return
            
            # 打开浏览器
            self.open_browser()
            
            # 显示访问信息
            print("\n🎉 系统启动成功!")
            print(f"� 前端地址: http://localhost:8080")
            print(f"🔧 后端API: http://localhost:3000")
            print("⌨️  按 Ctrl+C 停止服务\n")
            print("⌨️  按 Ctrl+C 停止服务\n")
            
            # 监控服务
            monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
            monitor_thread.start()
            
            # 等待用户中断
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n� 正在停止服务...")
            self.running = False
        except Exception as e:
            self.logger.error(f"❌ 运行时错误: {e}")
            import traceback
            self.logger.error(f"详细错误信息:\n{traceback.format_exc()}")
            print(f"❌ 系统错误: {e}")
            self.running = False
        finally:
            self.cleanup()
            self.logger.info("所有服务已停止")
            print("\n🎬 所有服务已停止，谢谢使用！")

def check_port_and_kill(port):
    """检查端口是否被占用，并提供选项关闭占用的程序"""
    
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return False
            except OSError:
                return True
    
    def get_process_using_port(port):
        """获取占用端口的进程信息"""
        if platform.system() == "Windows":
            cmd = f'netstat -ano | findstr :{port}'
        else:
            cmd = f'lsof -ti:{port}'
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                if platform.system() == "Windows":
                    # Windows netstat 输出解析
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if f':{port}' in line and 'LISTENING' in line:
                            parts = line.split()
                            if len(parts) >= 5:
                                return parts[-1]  # PID
                else:
                    # Linux/macOS lsof 输出
                    pids = result.stdout.strip().split('\n')
                    return pids[0] if pids and pids[0].isdigit() else None
        except Exception:
            pass
        return None
    
    def kill_process(pid):
        """杀死指定进程"""
        try:
            if platform.system() == "Windows":
                subprocess.run(f'taskkill /PID {pid} /F', shell=True, check=True)
            else:
                subprocess.run(f'kill -9 {pid}', shell=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_process_name(pid):
        """获取进程名称"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(f'tasklist /FI "PID eq {pid}" /FO CSV', 
                                      shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        # CSV format: "Image Name","PID","Session Name",...
                        return lines[1].split(',')[0].strip('"')
            else:
                result = subprocess.run(f'ps -p {pid} -o comm=', 
                                      shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
        except Exception:
            pass
        return f"进程 {pid}"
    
    if not is_port_in_use(port):
        return True  # 端口可用
    
    print(f"⚠️  端口 {port} 已被占用")
    
    # 尝试找到占用端口的进程
    pid = get_process_using_port(port)
    if not pid:
        print(f"   无法找到占用端口 {port} 的进程")
        choice = input(f"   是否继续启动？(可能会失败) [y/N]: ").lower()
        return choice in ['y', 'yes']
    
    process_name = get_process_name(pid)
    print(f"   占用进程: {process_name} (PID: {pid})")
    
    # 询问用户是否要关闭进程
    choice = input(f"   是否关闭占用端口 {port} 的进程？[Y/n]: ").lower()
    
    if choice in ['', 'y', 'yes']:
        print(f"   正在关闭进程 {pid}...")
        if kill_process(pid):
            print(f"   ✅ 进程 {pid} 已关闭")
            # 等待端口释放
            time.sleep(2)
            if is_port_in_use(port):
                print(f"   ⚠️  端口 {port} 仍被占用，可能需要等待更长时间")
                return False
            else:
                print(f"   ✅ 端口 {port} 已释放")
                return True
        else:
            print(f"   ❌ 无法关闭进程 {pid}，可能需要管理员权限")
            return False
    else:
        print("   用户选择不关闭进程")
        return False

def check_ports():
    """检查所有需要的端口"""
    print("🔍 检查端口占用情况...")
    
    ports_to_check = [3000, 8080]
    all_available = True
    
    for port in ports_to_check:
        if not check_port_and_kill(port):
            all_available = False
            print(f"❌ 端口 {port} 不可用")
        else:
            print(f"✅ 端口 {port} 可用")
    
    if not all_available:
        print("\n💡 解决方案:")
        print("   1. 重新运行脚本并选择关闭占用的进程")
        print("   2. 手动停止占用端口的程序")
        print("   3. 修改配置文件中的端口设置")
        print("   4. 等待几分钟后重试")
        return False
    
    print("✅ 所有端口检查通过")
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
        print("\n❌ 端口检查失败，无法启动服务")
        print("   请解决端口占用问题后重试")
        return
    
    # 启动服务管理器
    manager = ServiceManager()
    manager.run()

if __name__ == '__main__':
    main()
