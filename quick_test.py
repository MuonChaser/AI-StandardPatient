#!/usr/bin/env python3
"""
快速性能测试脚本 - 测试优化后的系统性能
"""

import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from backend.models.sp import StandardPatient, PatientFactory
from sp_data import Sp_data
from engine.gpt import GPTEngine

def test_sp_performance():
    """测试SP性能"""
    print("AI-StandardPatient 快速性能测试")
    print("="*50)
    
    # 加载预设数据
    preset_data = Sp_data()
    preset_data.load_from_json("presets/test.json")
    
    # 创建AI引擎
    engine = GPTEngine()
    
    # 测试1: 关闭评分的SP
    print("\n1. 测试关闭评分的SP (性能优化)")
    start_time = time.time()
    
    sp_fast = StandardPatient(
        data=preset_data,
        engine=engine
    )
    
    init_time = time.time() - start_time
    print(f"   初始化时间: {init_time:.3f}秒")
    
    # 测试对话响应
    test_messages = [
        "你好，我最近总是感觉胸口疼痛",
        "疼痛大概持续了一周了",
        "疼痛的时候会有压迫感"
    ]
    
    chat_times = []
    for i, message in enumerate(test_messages, 1):
        start_time = time.time()
        response = sp_fast.speak(message)
        chat_time = time.time() - start_time
        chat_times.append(chat_time)
        
        print(f"   对话{i}: {chat_time:.3f}秒")
        print(f"     用户: {message}")
        print(f"     SP: {response[:60]}...")
    
    avg_fast = sum(chat_times) / len(chat_times)
    print(f"   平均响应时间: {avg_fast:.3f}秒")
    
    # 测试2: 开启评分的SP
    print("\n2. 测试开启评分的SP (完整功能)")
    start_time = time.time()
    
    sp_full = StandardPatient(
        data=preset_data,
        engine=engine
    )
    
    init_time = time.time() - start_time
    print(f"   初始化时间: {init_time:.3f}秒")
    
    chat_times_full = []
    for i, message in enumerate(test_messages, 1):
        start_time = time.time()
        response = sp_full.speak(message)
        chat_time = time.time() - start_time
        chat_times_full.append(chat_time)
        
        print(f"   对话{i}: {chat_time:.3f}秒")
    
    avg_full = sum(chat_times_full) / len(chat_times_full)
    print(f"   平均响应时间: {avg_full:.3f}秒")
    
    # 获取评分
    score_data = sp_full.get_score_summary()
    print(f"   最终评分: {score_data.get('total_score', 0)}")
    
    # 性能对比
    print("\n3. 性能对比结果")
    print("="*30)
    improvement = ((avg_full - avg_fast) / avg_full) * 100 if avg_full > 0 else 0
    
    print(f"关闭评分平均响应: {avg_fast:.3f}秒")
    print(f"开启评分平均响应: {avg_full:.3f}秒")
    print(f"性能提升幅度: {improvement:.1f}%")
    
    if improvement > 20:
        print("✓ 显著性能提升!")
    elif improvement > 10:
        print("✓ 中等性能提升")
    elif improvement > 0:
        print("✓ 轻微性能提升")
    else:
        print("⚠️ 无明显性能提升")
    
    # 推荐配置
    print("\n4. 配置建议")
    print("="*20)
    if avg_fast < 3.0:
        print("✓ 关闭评分时响应速度良好 (<3秒)")
    else:
        print("⚠️ 关闭评分时响应仍较慢 (>3秒)")
        
    if avg_full < 5.0:
        print("✓ 开启评分时响应速度可接受 (<5秒)")
    else:
        print("❌ 开启评分时响应过慢 (>5秒)，建议仅在必要时开启")

if __name__ == "__main__":
    try:
        test_sp_performance()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("请检查presets/test.json文件是否存在")
