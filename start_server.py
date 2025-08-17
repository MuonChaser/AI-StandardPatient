#!/usr/bin/env python3
"""
AI标准化病人后端服务启动脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print(f"   当前版本: {sys.version}")
        sys.exit(1)
    print(f"✅ Python版本: {sys.version}")

def check_environment():
    """检查环境配置"""
    project_root = Path(__file__).parent
    env_file = project_root / '.env'
    env_example = project_root / '.env.example'
    
    print("🔍 检查环境配置...")
    
    if not env_file.exists():
        if env_example.exists():
            print(f"⚠️  未找到.env文件，请复制.env.example并配置:")
            print(f"   cp {env_example} {env_file}")
            print("   然后编辑.env文件，设置正确的API_KEY等配置")
        else:
            print("⚠️  未找到环境配置文件")
        return False
    
    # 读取.env文件检查关键配置
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    if 'API_KEY=your-openai-api-key-here' in env_content:
        print("⚠️  请在.env文件中设置正确的API_KEY")
        return False
    
    print("✅ 环境配置检查通过")
    return True

def install_dependencies():
    """安装依赖"""
    print("📦 检查并安装依赖...")
    
    # 检查虚拟环境
    venv_python = Path(__file__).parent / '.venv' / 'bin' / 'python'
    if venv_python.exists():
        python_cmd = str(venv_python)
        print(f"✅ 使用虚拟环境: {python_cmd}")
    else:
        python_cmd = sys.executable
        print(f"⚠️  未检测到虚拟环境，使用系统Python: {python_cmd}")
    
    # 安装依赖
    try:
        required_packages = [
            'flask',
            'flask-cors', 
            'openai',
            'python-dotenv'
        ]
        
        for package in required_packages:
            result = subprocess.run(
                [python_cmd, '-m', 'pip', 'install', package],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ {package}")
            else:
                print(f"❌ 安装{package}失败: {result.stderr}")
                
    except Exception as e:
        print(f"❌ 安装依赖时出错: {e}")
        return False
    
    return True

def check_preset_files():
    """检查预设文件"""
    print("📋 检查预设病例文件...")
    
    presets_dir = Path(__file__).parent / 'presets'
    if not presets_dir.exists():
        print("⚠️  预设文件目录不存在")
        return False
    
    json_files = list(presets_dir.glob('*.json'))
    if not json_files:
        print("⚠️  未找到预设病例文件")
        return False
    
    print(f"✅ 找到 {len(json_files)} 个预设病例文件")
    for file in json_files:
        print(f"   - {file.name}")
    
    return True

def start_server():
    """启动服务器"""
    print("\n🚀 启动AI标准化病人后端服务...")
    
    # 设置Python路径
    project_root = Path(__file__).parent
    os.environ['PYTHONPATH'] = str(project_root)
    
    # 启动Flask应用
    app_path = project_root / 'backend' / 'app.py'
    
    # 检查虚拟环境
    venv_python = project_root / '.venv' / 'bin' / 'python'
    if venv_python.exists():
        python_cmd = str(venv_python)
    else:
        python_cmd = sys.executable
    
    try:
        subprocess.run([python_cmd, str(app_path)], cwd=str(project_root))
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动服务时出错: {e}")

def main():
    """主函数"""
    print("🏥 AI标准化病人后端服务")
    print("=" * 50)
    
    # 检查Python版本
    check_python_version()
    
    # 检查环境配置
    env_ok = check_environment()
    
    # 安装依赖
    deps_ok = install_dependencies()
    
    # 检查预设文件
    presets_ok = check_preset_files()
    
    print("\n📊 检查结果:")
    print(f"   环境配置: {'✅' if env_ok else '⚠️'}")
    print(f"   依赖安装: {'✅' if deps_ok else '❌'}")
    print(f"   预设文件: {'✅' if presets_ok else '⚠️'}")
    
    if not deps_ok:
        print("\n❌ 依赖安装失败，无法启动服务")
        sys.exit(1)
    
    if not env_ok:
        print("\n⚠️  环境配置有问题，但仍可启动服务（部分功能可能不可用）")
    
    # 启动服务
    start_server()

if __name__ == '__main__':
    main()
