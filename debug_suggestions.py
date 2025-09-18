#!/usr/bin/env python3
"""
调试智能评分系统get_suggestions方法的问题
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from backend.models.sp import StandardPatient
from sp_data import Sp_data
from engine.gpt import GPTEngine
from modules.intelligent_scoring import IntelligentScoringSystem

def debug_suggestions():
    """调试suggestions方法"""
    print("🔍 调试智能评分系统get_suggestions方法")
    print("="*50)
    
    try:
        # 1. 测试直接创建IntelligentScoringSystem
        print("1. 测试直接创建IntelligentScoringSystem...")
        engine = GPTEngine()
        test_data = {
            "hiddens": [
                {"过敏史": "无明显过敏史"},
                {"家族史": "父亲有高血压"}
            ]
        }
        
        scoring_system = IntelligentScoringSystem(test_data, engine=engine)
        print(f"   ✅ 创建成功，类型: {type(scoring_system)}")
        
        # 检查方法是否存在
        print("2. 检查方法存在性...")
        print(f"   hasattr(scoring_system, 'get_suggestions'): {hasattr(scoring_system, 'get_suggestions')}")
        print(f"   hasattr(scoring_system, 'get_intelligent_suggestions'): {hasattr(scoring_system, 'get_intelligent_suggestions')}")
        
        # 查看所有可用方法
        methods = [method for method in dir(scoring_system) if not method.startswith('_')]
        print(f"   可用方法: {methods}")
        
        # 3. 测试方法调用
        print("3. 测试方法调用...")
        if hasattr(scoring_system, 'get_suggestions'):
            suggestions = scoring_system.get_suggestions()
            print(f"   ✅ get_suggestions() 调用成功")
            print(f"   返回类型: {type(suggestions)}")
            print(f"   返回内容: {suggestions}")
        else:
            print("   ❌ get_suggestions方法不存在")
            
        # 4. 测试通过StandardPatient
        print("4. 测试通过StandardPatient调用...")
        preset_data = Sp_data()
        preset_data.load_from_json("presets/test.json")
        
        sp = EnhancedSP(
            data=preset_data,
            engine=engine,
            enable_scoring=True
        )
        
        print(f"   SP评分系统类型: {type(sp.scoring_system)}")
        print(f"   SP评分系统是否为None: {sp.scoring_system is None}")
        
        if sp.scoring_system:
            print(f"   SP hasattr get_suggestions: {hasattr(sp.scoring_system, 'get_suggestions')}")
            try:
                sp_suggestions = sp.get_suggestions()
                print(f"   ✅ SP.get_suggestions() 调用成功: {sp_suggestions}")
            except Exception as e:
                print(f"   ❌ SP.get_suggestions() 调用失败: {e}")
        
    except Exception as e:
        print(f"❌ 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_suggestions()
