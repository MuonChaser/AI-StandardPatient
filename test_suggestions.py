#!/usr/bin/env python3
"""
测试智能建议功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from modules.intelligent_scoring import IntelligentScoringSystem
from sp_data import Sp_data
from engine.gpt import GPTEngine

def test_suggestions():
    """测试建议功能"""
    print("🧪 测试智能建议功能")
    print("="*40)
    
    # 加载测试数据
    preset_data = Sp_data()
    preset_data.load_from_json("presets/test.json")
    
    # 创建引擎和评分系统
    engine = GPTEngine()
    scoring_system = IntelligentScoringSystem(preset_data.data, engine=engine)
    
    # 检查方法是否存在
    print("1. 检查get_suggestions方法是否存在:")
    if hasattr(scoring_system, 'get_suggestions'):
        print("   ✅ get_suggestions方法存在")
    else:
        print("   ❌ get_suggestions方法不存在")
        return
    
    if hasattr(scoring_system, 'get_intelligent_suggestions'):
        print("   ✅ get_intelligent_suggestions方法存在")
    else:
        print("   ❌ get_intelligent_suggestions方法不存在")
        return
    
    # 测试调用
    print("\n2. 测试方法调用:")
    try:
        suggestions = scoring_system.get_suggestions()
        print(f"   ✅ get_suggestions()调用成功")
        print(f"   📝 返回建议数量: {len(suggestions)}")
        
        if suggestions:
            print("   建议内容:")
            for i, suggestion in enumerate(suggestions[:3], 1):
                print(f"      {i}. {suggestion}")
        else:
            print("   📝 没有返回建议")
            
    except Exception as e:
        print(f"   ❌ get_suggestions()调用失败: {e}")
        return
    
    print("\n3. 测试问题初始化:")
    print(f"   📊 问题项数量: {len(scoring_system.question_items)}")
    if scoring_system.question_items:
        print("   问题示例:")
        for i, item in enumerate(scoring_system.question_items[:3], 1):
            print(f"      {i}. {item.question}")
    
    print("\n🎉 智能建议功能测试完成!")

if __name__ == "__main__":
    try:
        test_suggestions()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
