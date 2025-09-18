

"""
prompt管理与测试API
"""
import os
import re
import shutil
import sys
from flask import Blueprint, request
from backend.utils.response import APIResponse
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_loader import PromptLoader
from sp_data import Sp_data
from engine.gpt import GPTEngine
from models.sp import SP

PROMPT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts')
BACKUP_DIR = os.path.join(PROMPT_DIR, 'backups')

# 确保备份目录存在
os.makedirs(BACKUP_DIR, exist_ok=True)

prompt_bp = Blueprint('prompt', __name__)

# 新建prompt文件
@prompt_bp.route('/api/prompt/create', methods=['POST'])
def create_prompt():
    data = request.json
    filename = data.get('filename')
    content = data.get('content', '')
    path = os.path.join(PROMPT_DIR, filename)
    if os.path.exists(path):
        return APIResponse.error('文件已存在')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return APIResponse.success(filename, '新建成功')

# 删除prompt文件
@prompt_bp.route('/api/prompt/delete', methods=['POST'])
def delete_prompt():
    data = request.json
    filename = data.get('filename')
    path = os.path.join(PROMPT_DIR, filename)
    if not os.path.exists(path):
        return APIResponse.error('文件不存在')
    os.remove(path)
    return APIResponse.success(filename, '删除成功')

# 副本恢复为正式文件
@prompt_bp.route('/api/prompt/restore', methods=['POST'])
def restore_backup():
    data = request.json
    backup_filename = data.get('backup_filename')
    target_filename = data.get('target_filename')
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    target_path = os.path.join(PROMPT_DIR, target_filename)
    if not os.path.exists(backup_path):
        return APIResponse.error('副本不存在')
    shutil.copy(backup_path, target_path)
    return APIResponse.success(target_filename, '副本已恢复为正式文件')

# 获取所有prompt文件列表
@prompt_bp.route('/api/prompt/list', methods=['GET'])
def list_prompts():
    files = [f for f in os.listdir(PROMPT_DIR) if f.endswith('.txt')]
    print(files)
    return APIResponse.success(files, "获取prompt文件列表成功")

# 加载指定prompt内容
@prompt_bp.route('/api/prompt/load', methods=['GET'])
def load_prompt():
    filename = request.args.get('filename')
    path = os.path.join(PROMPT_DIR, filename)
    if not os.path.exists(path):
        return APIResponse.error("文件不存在")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return APIResponse.success(content, "加载成功")

# 保存副本
@prompt_bp.route('/api/prompt/backup', methods=['POST'])
def backup_prompt():
    data = request.json
    filename = data.get('filename')
    content = data.get('content')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{filename.replace('.txt','')}_{timestamp}.txt"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return APIResponse.success(backup_name, "副本保存成功")

# 覆盖保存
@prompt_bp.route('/api/prompt/save', methods=['POST'])
def save_prompt():
    data = request.json
    filename = data.get('filename')
    content = data.get('content')
    path = os.path.join(PROMPT_DIR, filename)
    if not os.path.exists(path):
        return APIResponse.error("文件不存在")
    # 先备份原文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{filename.replace('.txt','')}_before_{timestamp}.txt"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy(path, backup_path)
    # 覆盖保存
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return APIResponse.success(filename, "覆盖保存成功")

# 获取所有副本列表
@prompt_bp.route('/api/prompt/backups', methods=['GET'])
def list_backups():
    files = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.txt')]
    return APIResponse.success(files, "获取副本列表成功")

# 加载副本内容
@prompt_bp.route('/api/prompt/backup_load', methods=['GET'])
def load_backup():
    filename = request.args.get('filename')
    path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(path):
        return APIResponse.error("副本不存在")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return APIResponse.success(content, "加载副本成功")

# 解析prompt变量名
@prompt_bp.route('/api/prompt/vars', methods=['GET'])
def get_prompt_vars():
    filename = request.args.get('filename')
    path = os.path.join(PROMPT_DIR, filename)
    if not os.path.exists(path):
        return APIResponse.error("文件不存在")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    vars_found = re.findall(r'\{(\w+)\}', content)
    return APIResponse.success(list(set(vars_found)), "变量名解析成功")

# 对话测试API
@prompt_bp.route('/api/prompt/test', methods=['POST'])
def test_prompt():
    data = request.json
    prompt_content = data.get('prompt_content')
    context = data.get('context', {})
    doctor_message = data.get('doctor_message', '')
    # 临时保存prompt到文件
    temp_path = os.path.join(PROMPT_DIR, 'temp_test_prompt.txt')
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(prompt_content)
    # 构造SP
    sp_data = Sp_data()
    sp_data.data = context
    sp = SP(sp_data, GPTEngine(), prompt_path=temp_path)
    # 对话
    sp.memorize(doctor_message, 'user')
    response = sp.engine.get_response(sp.memories)
    return APIResponse.success(response, "对话测试成功")

# 获取当前使用的prompt文件
@prompt_bp.route('/api/prompt/current', methods=['GET'])
def get_current_prompt():
    # 默认使用 standard_patient.txt
    current_file = 'standard_patient.txt'
    path = os.path.join(PROMPT_DIR, current_file)
    if os.path.exists(path):
        return APIResponse.success(current_file, "获取当前prompt成功")
    else:
        # 如果默认文件不存在，返回第一个可用文件
        files = [f for f in os.listdir(PROMPT_DIR) if f.endswith('.txt')]
        if files:
            return APIResponse.success(files[0], "获取当前prompt成功")
        else:
            return APIResponse.error("无可用prompt文件")

# 设置当前使用的prompt文件
@prompt_bp.route('/api/prompt/set_current', methods=['POST'])
def set_current_prompt():
    data = request.json
    filename = data.get('filename')
    path = os.path.join(PROMPT_DIR, filename)
    if not os.path.exists(path):
        return APIResponse.error('Prompt文件不存在')
    
    # 这里可以将当前选择的prompt保存到配置文件或数据库
    # 现在简单返回成功
    return APIResponse.success(filename, "设置当前prompt成功")

if __name__ == '__main__':
    files = [f for f in os.listdir(PROMPT_DIR) if f.endswith('.txt')]
    print(files)
