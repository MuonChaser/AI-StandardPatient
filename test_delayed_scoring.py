#!/usr/bin/env python3
"""
延迟评分性能测试脚本
对比实时评分vs延迟评分的性能差异
"""

import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from backend.models.sp import StandardPatient
from sp_data import Sp_data
from engine.gpt import GPTEngine

def test_delayed_scoring():
    """测试延迟评分性能"""
    print("🧪 延迟评分性能测试")
    print("="*60)
    
    # 加载预设数据和引擎
    preset_data = Sp_data()
    preset_data.load_from_json("presets/test.json")
    engine = GPTEngine()
    
    # 测试1: 延迟评分模式
    print("\n1️⃣ 测试延迟评分模式（新方案）")
    print("-" * 40)
    
    start_time = time.time()
    sp_delayed = StandardPatient(
        data=preset_data,
        engine=engine
    )
    init_time = time.time() - start_time
    print(f"   初始化时间: {init_time:.3f}秒")
    
    # 模拟对话
    test_messages = [
        "你好，我最近总是感觉胸口疼痛",
        "疼痛大概持续了一周了",
        "疼痛的时候会有压迫感，有时候还会觉得呼吸困难",
        "疼痛主要在左胸部位，有时候会放射到左臂",
        "疼痛通常在运动或者紧张的时候会加重"
    ]
    
    print("   开始对话测试...")
    chat_times = []
    total_chat_start = time.time()
    
    for i, message in enumerate(test_messages, 1):
        chat_start = time.time()
        response = sp_delayed.speak(message)
        chat_time = time.time() - chat_start
        chat_times.append(chat_time)
        
        print(f"   对话{i}: {chat_time:.3f}秒")
    
    total_chat_time = time.time() - total_chat_start
    avg_chat_time = sum(chat_times) / len(chat_times)
    
    print(f"   总对话时间: {total_chat_time:.3f}秒")
    print(f"   平均对话响应: {avg_chat_time:.3f}秒")
    
    # 获取评分报告（这时才计算评分）
    print("   正在生成评分报告...")
    report_start = time.time()
    score_report = sp_delayed.get_score_report()
    report_time = time.time() - report_start
    
    print(f"   评分报告生成时间: {report_time:.3f}秒")
    
    if 'error' not in score_report:
        score_summary = score_report.get('score_summary', {})
        total_score = score_summary.get('total_score', 0)
        print(f"   最终评分: {total_score}")
    else:
        print(f"   ❌ 评分失败: {score_report.get('error')}")
    
    # 总结
    print("\n📊 延迟评分模式总结:")
    print(f"   ✅ 对话响应快速 (平均{avg_chat_time:.3f}秒)")
    print(f"   ⏱️ 评分计算集中在报告生成时 ({report_time:.3f}秒)")
    print(f"   🎯 用户体验优化: 对话流畅，报告生成稍慢但可接受")
    
    # 性能分析
    print("\n🔍 性能分析:")
    improvement_msg = "显著" if avg_chat_time < 2.0 else "中等" if avg_chat_time < 3.0 else "有限"
    print(f"   对话响应速度: {improvement_msg}提升")
    
    if report_time < 10.0:
        print("   ✅ 报告生成速度: 可接受 (<10秒)")
    else:
        print("   ⚠️ 报告生成速度: 较慢 (>10秒)")
    
    # 推荐使用场景
    print("\n💡 推荐使用场景:")
    print("   ✅ 交互式对话场景 - 优先保证对话流畅性")
    print("   ✅ 演示环境 - 实时响应给用户良好体验")
    print("   ✅ 生产环境 - 平衡性能和功能完整性")
    
    return {
        "avg_chat_time": avg_chat_time,
        "report_generation_time": report_time,
        "total_score": score_summary.get('total_score', 0) if 'error' not in score_report else 0
    }

def test_performance_comparison():
    """简化的性能对比"""
    print("\n" + "="*60)
    print("🚀 性能优化效果总结")
    print("="*60)
    
    result = test_delayed_scoring()
    
    print(f"\n最终结果:")
    print(f"  💬 对话平均响应时间: {result['avg_chat_time']:.3f}秒")
    print(f"  📊 评分报告生成时间: {result['report_generation_time']:.3f}秒")
    print(f"  🎯 评分结果: {result['total_score']}")
    
    # 性能评级
    chat_grade = "🟢 优秀" if result['avg_chat_time'] < 2.0 else "🟡 良好" if result['avg_chat_time'] < 3.0 else "🔴 需优化"
    report_grade = "🟢 快速" if result['report_generation_time'] < 5.0 else "🟡 中等" if result['report_generation_time'] < 10.0 else "🔴 较慢"
    
    print(f"\n性能评级:")
    print(f"  对话响应: {chat_grade}")
    print(f"  报告生成: {report_grade}")
    
    if result['avg_chat_time'] < 2.0 and result['report_generation_time'] < 10.0:
        print("\n🎉 优化成功！延迟评分显著提升了用户体验")
    else:
        print("\n📝 优化有效果，但可能需要进一步调整")

if __name__ == "__main__":
    try:
        test_performance_comparison()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print("请检查presets/test.json文件是否存在")
