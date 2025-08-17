#!/usr/bin/env python3
"""
API测试客户端
用于测试AI标准化病人后端API的所有功能
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class SPAPIClient:
    """SP API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:5000/api"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()
    
    def get_presets(self) -> Dict[str, Any]:
        """获取预设病例"""
        response = self.session.get(f"{self.base_url}/sp/presets")
        return response.json()
    
    def create_session(self, session_id: str, preset_file: str = None, custom_data: Dict = None) -> Dict[str, Any]:
        """创建会话"""
        data = {"session_id": session_id}
        if preset_file:
            data["preset_file"] = preset_file
        elif custom_data:
            data["custom_data"] = custom_data
        
        response = self.session.post(f"{self.base_url}/sp/session/create", json=data)
        return response.json()
    
    def chat(self, session_id: str, message: str) -> Dict[str, Any]:
        """发送消息"""
        data = {"message": message}
        response = self.session.post(f"{self.base_url}/sp/session/{session_id}/chat", json=data)
        return response.json()
    
    def get_history(self, session_id: str) -> Dict[str, Any]:
        """获取对话历史"""
        response = self.session.get(f"{self.base_url}/sp/session/{session_id}/history")
        return response.json()
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """获取会话信息"""
        response = self.session.get(f"{self.base_url}/sp/session/{session_id}/info")
        return response.json()
    
    def list_sessions(self) -> Dict[str, Any]:
        """获取会话列表"""
        response = self.session.get(f"{self.base_url}/sp/sessions")
        return response.json()
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """删除会话"""
        response = self.session.delete(f"{self.base_url}/sp/session/{session_id}")
        return response.json()
    
    def validate_data(self, data: Dict) -> Dict[str, Any]:
        """验证SP数据"""
        response = self.session.post(f"{self.base_url}/sp/data/validate", json=data)
        return response.json()

def print_response(title: str, response: Dict[str, Any]):
    """打印响应结果"""
    print(f"\n{'='*50}")
    print(f"📋 {title}")
    print(f"{'='*50}")
    
    if response.get('success'):
        print(f"✅ {response.get('message', '成功')}")
        if response.get('data'):
            print(f"📊 数据: {json.dumps(response['data'], ensure_ascii=False, indent=2)}")
    else:
        print(f"❌ {response.get('message', '失败')}")
    print()

def test_api():
    """测试API功能"""
    print("🧪 开始测试AI标准化病人API")
    print("=" * 60)
    
    # 创建客户端
    client = SPAPIClient()
    
    try:
        # 1. 健康检查
        print("1️⃣ 测试健康检查...")
        health = client.health_check()
        print_response("健康检查", health)
        
        if not health.get('success'):
            print("❌ 服务未运行，请先启动后端服务")
            return
        
        # 2. 获取预设病例
        print("2️⃣ 测试获取预设病例...")
        presets = client.get_presets()
        print_response("预设病例列表", presets)
        
        # 3. 创建会话
        print("3️⃣ 测试创建会话...")
        session_id = f"test_session_{int(time.time())}"
        
        if presets.get('success') and presets.get('data'):
            # 使用第一个预设文件
            preset_file = presets['data'][0]['filename']
            session_result = client.create_session(session_id, preset_file=preset_file)
        else:
            # 使用自定义数据
            custom_data = {
                "basics": {
                    "name": "测试病人",
                    "性别": "男",
                    "年龄": 35
                },
                "disease": "感冒",
                "symptoms": ["头痛", "发热", "咳嗽"],
                "hiddens": [
                    {"过敏史": "无明显过敏史"},
                    {"家族史": "父亲有高血压"}
                ],
                "personalities": ["性格开朗", "配合治疗", "有一定医学常识"]
            }
            session_result = client.create_session(session_id, custom_data=custom_data)
        
        print_response("创建会话", session_result)
        
        if not session_result.get('success'):
            print("❌ 会话创建失败，跳过后续测试")
            return
        
        # 4. 测试对话
        print("4️⃣ 测试对话功能...")
        
        # 模拟医生对话
        conversations = [
            "您好，请问您哪里不舒服？",
            "症状持续多长时间了？",
            "除了这些症状，还有其他不适吗？",
            "您有什么过敏史吗？",
            "您的家族病史如何？"
        ]
        
        for i, message in enumerate(conversations, 1):
            print(f"   👨‍⚕️ 医生问: {message}")
            chat_result = client.chat(session_id, message)
            
            if chat_result.get('success'):
                sp_response = chat_result['data']['sp_response']
                print(f"   🤒 病人答: {sp_response}")
            else:
                print(f"   ❌ 对话失败: {chat_result.get('message')}")
            
            print()
            time.sleep(1)  # 稍微延迟，模拟真实对话
        
        # 5. 获取对话历史
        print("5️⃣ 测试获取对话历史...")
        history = client.get_history(session_id)
        print_response("对话历史", history)
        
        # 6. 获取会话信息
        print("6️⃣ 测试获取会话信息...")
        session_info = client.get_session_info(session_id)
        print_response("会话信息", session_info)
        
        # 7. 获取会话列表
        print("7️⃣ 测试获取会话列表...")
        sessions = client.list_sessions()
        print_response("会话列表", sessions)
        
        # 8. 验证数据格式
        print("8️⃣ 测试数据验证...")
        test_data = {
            "basics": {"name": "验证测试", "性别": "女"},
            "disease": "测试疾病",
            "symptoms": ["症状1", "症状2"]
        }
        validation = client.validate_data(test_data)
        print_response("数据验证", validation)
        
        # 9. 删除会话
        print("9️⃣ 测试删除会话...")
        delete_result = client.delete_session(session_id)
        print_response("删除会话", delete_result)
        
        print("🎉 所有测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 无法连接到后端服务")
        print("   请确保后端服务正在运行 (python backend/app.py)")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

def interactive_test():
    """交互式测试"""
    print("🎮 交互式API测试")
    print("=" * 30)
    
    client = SPAPIClient()
    
    # 检查服务状态
    try:
        health = client.health_check()
        if not health.get('success'):
            print("❌ 服务未运行")
            return
        print("✅ 服务正常运行")
    except:
        print("❌ 无法连接到服务")
        return
    
    # 获取预设病例
    presets = client.get_presets()
    if presets.get('success') and presets.get('data'):
        print("\n📋 可用预设病例:")
        for i, preset in enumerate(presets['data']):
            print(f"   {i+1}. {preset['description']}")
        
        # 选择预设
        choice = input(f"\n请选择预设病例 (1-{len(presets['data'])}): ").strip()
        try:
            preset_idx = int(choice) - 1
            if 0 <= preset_idx < len(presets['data']):
                selected_preset = presets['data'][preset_idx]['filename']
            else:
                print("❌ 选择无效")
                return
        except ValueError:
            print("❌ 输入无效")
            return
    else:
        print("⚠️ 无可用预设，使用默认数据")
        selected_preset = None
    
    # 创建会话
    session_id = f"interactive_{int(time.time())}"
    if selected_preset:
        session_result = client.create_session(session_id, preset_file=selected_preset)
    else:
        custom_data = {
            "basics": {"name": "互动测试病人", "性别": "男", "年龄": 30},
            "disease": "感冒",
            "symptoms": ["头痛", "发热"],
            "personalities": ["配合治疗"]
        }
        session_result = client.create_session(session_id, custom_data=custom_data)
    
    if not session_result.get('success'):
        print(f"❌ 创建会话失败: {session_result.get('message')}")
        return
    
    print(f"✅ 会话创建成功: {session_result['data']['patient_name']}")
    print("\n💬 开始对话 (输入 'quit' 退出, 'history' 查看历史):")
    print("-" * 50)
    
    # 对话循环
    while True:
        user_input = input("\n👨‍⚕️ 医生: ").strip()
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'history':
            history = client.get_history(session_id)
            if history.get('success'):
                print("\n📜 对话历史:")
                for i, conv in enumerate(history['data']['history'], 1):
                    print(f"   {i}. 医生: {conv['user_message']}")
                    print(f"      病人: {conv['sp_response']}")
            continue
        elif not user_input:
            continue
        
        # 发送消息
        chat_result = client.chat(session_id, user_input)
        if chat_result.get('success'):
            print(f"🤒 病人: {chat_result['data']['sp_response']}")
        else:
            print(f"❌ 对话失败: {chat_result.get('message')}")
    
    # 清理会话
    client.delete_session(session_id)
    print(f"\n👋 会话已结束并清理")

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_test()
    else:
        test_api()

if __name__ == '__main__':
    main()
