"""
智能评分系统模块
使用项目Engine进行AI Agent评判
"""

import json
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class IntelligentScoringAgent:
    """智能评分Agent，使用项目Engine进行AI判断"""
    
    def __init__(self, engine=None):
        # 使用传入的engine或创建默认engine
        if engine is None:
            from engine.gpt import GPTEngine
            self.engine = GPTEngine()
        else:
            self.engine = engine
        
    def evaluate_question_match(self, doctor_question: str, target_question: str, 
                              target_answer: str = "", context: str = "") -> Dict[str, Any]:
        """
        评估医生问题是否匹配目标问题点
        
        Args:
            doctor_question: 医生询问的问题
            target_question: 目标隐藏问题
            target_answer: 预期的标准答案
            context: 对话上下文
            
        Returns:
            评估结果，包含匹配度、得分、理由等
        """
        
        prompt = f"""
你是一个医学问诊评估专家。请评估医生的问题是否有效询问了目标信息点。

目标问题点: {target_question}
标准答案: {target_answer}
医生询问: {doctor_question}
对话上下文: {context}

请从以下几个维度评估:
1. 语义匹配度(0-100): 医生问题与目标问题的语义相似程度
2. 信息获取度(0-100): 医生问题能否获取到目标信息
3. 专业性(0-100): 问题的医学专业性和准确性
4. 完整性(0-100): 问题是否完整覆盖了目标信息点

评估规则:
- 即使用词不同，但能获取相同医学信息的问题应该给高分
- 考虑医学术语的同义词和不同表达方式
- 部分匹配也应该给予相应分数，不要求100%字面匹配
- 考虑临床实际情况下的问诊习惯

请返回JSON格式，格式如下：
{{
  "semantic_match": 85,
  "information_coverage": 90,
  "professionalism": 80,
  "completeness": 75,
  "overall_score": 82.5,
  "is_match": true,
  "confidence": 0.9,
  "reasoning": "详细的评估理由",
  "suggestions": "改进建议（如有）"
}}

overall_score是四个维度的加权平均(权重可以根据重要性调整)
is_match: overall_score >= 60 为true
confidence: 评估的置信度(0-1)
"""

        try:
            # 使用项目engine进行AI调用
            messages = [
                {"role": "system", "content": "你是一个专业的医学问诊评估专家，擅长分析医生问诊质量。"},
                {"role": "user", "content": prompt}
            ]
            
            response_text = self.engine.get_response(messages)
            
            # 尝试解析JSON
            try:
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # 如果没有找到JSON，构建默认结果
                    result = self._create_fallback_result(doctor_question, target_question)
            except json.JSONDecodeError:
                result = self._create_fallback_result(doctor_question, target_question)
                
            # 确保所有必需字段存在
            result = self._validate_result(result)
            
            return result
            
        except Exception as e:
            print(f"AI评估出错: {e}")
            return self._create_fallback_result(doctor_question, target_question)
    
    def _create_fallback_result(self, doctor_question: str, target_question: str) -> Dict[str, Any]:
        """创建备用评估结果（基于简单规则）"""
        # 简单的关键词匹配作为备用方案
        doctor_lower = doctor_question.lower()
        target_lower = target_question.lower()
        
        # 基本匹配检查
        common_words = set(doctor_lower.split()) & set(target_lower.split())
        match_ratio = len(common_words) / max(len(set(target_lower.split())), 1)
        
        score = min(match_ratio * 100, 85)  # 最高85分
        is_match = score >= 50
        
        return {
            "semantic_match": score,
            "information_coverage": score,
            "professionalism": 70,
            "completeness": score,
            "overall_score": score,
            "is_match": is_match,
            "confidence": 0.6,
            "reasoning": f"备用评估：基于关键词匹配度 {match_ratio:.2f}",
            "suggestions": "建议使用更具体的医学术语"
        }
    
    def _validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证和修正评估结果"""
        required_fields = {
            "semantic_match": 0,
            "information_coverage": 0,
            "professionalism": 0,
            "completeness": 0,
            "overall_score": 0,
            "is_match": False,
            "confidence": 0.5,
            "reasoning": "无详细评估",
            "suggestions": ""
        }
        
        for field, default_value in required_fields.items():
            if field not in result:
                result[field] = default_value
        
        # 确保分数在合理范围内
        for score_field in ["semantic_match", "information_coverage", "professionalism", "completeness", "overall_score"]:
            if score_field in result:
                result[score_field] = max(0, min(100, float(result[score_field])))
        
        # 确保置信度在0-1之间
        result["confidence"] = max(0, min(1, float(result["confidence"])))
        
        return result


class IntelligentQuestionItem:
    """智能问题项目，使用AI进行匹配判断"""
    
    def __init__(self, question: str, answer: str = "", weight: float = 1.0, 
                 category: str = "general", keywords: List[str] = None, 
                 description: str = "", threshold: float = 60.0, engine=None):
        self.question = question
        self.answer = answer
        self.weight = weight
        self.category = category
        self.keywords = keywords or []
        self.description = description
        self.threshold = threshold  # 匹配阈值，超过此分数才算匹配
        
        # 评估相关
        self.evaluations: List[Dict[str, Any]] = []  # 存储所有评估结果
        self.best_match_score = 0
        self.is_asked = False
        self.asked_messages = []
        
        # AI Agent - 使用传入的engine
        self.scoring_agent = IntelligentScoringAgent(engine)
    
    def evaluate_message(self, message: str, context: str = "") -> Dict[str, Any]:
        """评估消息是否匹配此问题点"""
        evaluation = self.scoring_agent.evaluate_question_match(
            doctor_question=message,
            target_question=self.question,
            target_answer=self.answer,
            context=context
        )
        
        # 记录评估结果
        evaluation["timestamp"] = datetime.now().isoformat()
        evaluation["message"] = message
        self.evaluations.append(evaluation)
        
        # 更新最佳匹配分数
        if evaluation["overall_score"] > self.best_match_score:
            self.best_match_score = evaluation["overall_score"]
        
        # 判断是否匹配
        if evaluation["overall_score"] >= self.threshold and evaluation["is_match"]:
            if not self.is_asked:
                self.is_asked = True
                self.asked_messages.append(message)
            return evaluation
        
        return evaluation
    
    def get_match_score(self) -> float:
        """获取最佳匹配分数"""
        return self.best_match_score
    
    def get_partial_score(self) -> float:
        """获取部分得分（基于最佳匹配分数）"""
        if self.best_match_score >= self.threshold:
            return self.weight  # 完全得分
        elif self.best_match_score >= 30:  # 部分匹配
            return self.weight * (self.best_match_score / 100)
        else:
            return 0  # 无匹配
    
    def reset_evaluation_state(self):
        """重置评估状态（用于延迟计算）"""
        self.evaluations = []
        self.best_match_score = 0
        self.is_asked = False
        self.asked_messages = []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "question": self.question,
            "answer": self.answer,
            "weight": self.weight,
            "category": self.category,
            "keywords": self.keywords,
            "description": self.description,
            "threshold": self.threshold,
            "is_asked": self.is_asked,
            "best_match_score": self.best_match_score,
            "partial_score": self.get_partial_score(),
            "asked_messages": self.asked_messages,
            "evaluations": self.evaluations[-3:]  # 只保留最近3次评估
        }


class IntelligentScoringSystem:
    """智能评分系统"""
    
    def __init__(self, case_data: Dict[str, Any], threshold: float = 60.0, engine=None):
        self.case_data = case_data
        self.threshold = threshold
        self.engine = engine  # 保存engine引用
        self.question_items: List[IntelligentQuestionItem] = []
        self.total_weight = 0
        self.conversation_history = []
        self._initialize_questions()
    
    def _initialize_questions(self):
        """初始化隐藏问题"""
        hidden_questions = self.case_data.get("hidden_questions", [])
        
        # 如果没有hidden_questions，尝试从hiddens字段生成
        if not hidden_questions:
            hiddens = self.case_data.get("hiddens", [])
            for hidden_item in hiddens:
                if isinstance(hidden_item, dict):
                    for key, value in hidden_item.items():
                        question = f"请问{key}是什么？"
                        answer = str(value)
                        question_item = IntelligentQuestionItem(
                            question=question,
                            answer=answer,
                            weight=1.0,
                            category="hidden_info",
                            threshold=self.threshold,
                            engine=self.engine
                        )
                        self.question_items.append(question_item)
                        self.total_weight += question_item.weight
        else:
            # 处理标准的hidden_questions格式
            for item in hidden_questions:
                if isinstance(item, str):
                    question_item = IntelligentQuestionItem(
                        question=item,
                        weight=1.0,
                        category="general",
                        threshold=self.threshold,
                        engine=self.engine
                    )
                elif isinstance(item, dict):
                    question_item = IntelligentQuestionItem(
                        question=item.get("question", ""),
                        answer=item.get("answer", ""),
                        weight=item.get("weight", 1.0),
                        category=item.get("category", "general"),
                        keywords=item.get("keywords", []),
                        description=item.get("description", ""),
                        threshold=item.get("threshold", self.threshold),
                        engine=self.engine
                    )
                else:
                    continue
                
                self.question_items.append(question_item)
                self.total_weight += question_item.weight
    
    def record_message(self, message: str, role: str = "user"):
        """仅记录对话消息，不进行评分计算（用于性能优化）"""
        # 只记录对话历史
        self.conversation_history.append({
            "role": role,
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

    def process_message(self, message: str, role: str = "user"):
        """处理对话消息（实时评分版本，已弃用）"""
        # 记录对话历史
        self.conversation_history.append({
            "role": role,
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # 只处理用户（医生）的消息
        if role == "user":
            # 构建上下文（最近5条对话）
            context = self._build_context()
            
            # 评估每个问题点
            for question_item in self.question_items:
                question_item.evaluate_message(message, context)
    
    def calculate_scores_from_history(self):
        """从对话历史中批量计算评分（延迟计算优化）"""
        print("🔄 开始从对话历史计算评分...")
        start_time = time.time()
        
        # 重置所有问题项的状态
        for question_item in self.question_items:
            question_item.reset_evaluation_state()
        
        # 获取所有用户（医生）的消息
        user_messages = [msg for msg in self.conversation_history if msg["role"] == "user"]
        
        if not user_messages:
            print("⚠️ 没有找到用户消息，跳过评分计算")
            return
        
        print(f"📊 分析 {len(user_messages)} 条用户消息中...")
        
        # 为每条用户消息构建上下文并评估
        for i, user_msg in enumerate(user_messages):
            # 构建该消息的上下文（包括之前的对话）
            context = self._build_context_for_message(i, max_context=5)
            
            # 评估每个问题点
            for question_item in self.question_items:
                question_item.evaluate_message(user_msg["content"], context)
        
        end_time = time.time()
        calculation_time = end_time - start_time
        
        # 统计评分结果
        asked_count = sum(1 for item in self.question_items if item.is_asked)
        total_count = len(self.question_items)
        
        print(f"✅ 评分计算完成!")
        print(f"   ⏱️ 计算耗时: {calculation_time:.2f}秒")
        print(f"   📈 已询问问题: {asked_count}/{total_count}")
        if total_count > 0:
            print(f"   🎯 完成率: {(asked_count/total_count*100):.1f}%")
        else:
            print(f"   ⚠️ 没有找到评分问题，请检查病例数据中的hidden_questions字段")

    def _build_context_for_message(self, message_index: int, max_context: int = 5) -> str:
        """为指定消息构建上下文"""
        # 获取该消息及之前的对话记录
        context_messages = self.conversation_history[:message_index + 1]
        
        # 取最近的max_context条消息
        recent_messages = context_messages[-max_context:]
        context_parts = []
        
        for msg in recent_messages:
            role_name = "医生" if msg["role"] == "user" else "病人"
            context_parts.append(f"{role_name}: {msg['content']}")
        
        return "\n".join(context_parts)

    def _build_context(self, max_messages: int = 5) -> str:
        """构建对话上下文"""
        recent_messages = self.conversation_history[-max_messages:]
        context_parts = []
        
        for msg in recent_messages:
            role_name = "医生" if msg["role"] == "user" else "病人"
            context_parts.append(f"{role_name}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def calculate_score(self) -> Dict[str, Any]:
        """计算智能评分结果"""
        if self.total_weight == 0:
            return {
                "total_score": 100,
                "percentage": 100,
                "message": "没有隐藏问题，满分"
            }
        
        # 计算完全匹配分数
        perfect_score = sum(item.weight for item in self.question_items if item.is_asked)
        perfect_percentage = (perfect_score / self.total_weight) * 100
        
        # 计算部分匹配分数（新增）
        partial_score = sum(item.get_partial_score() for item in self.question_items)
        partial_percentage = (partial_score / self.total_weight) * 100
        
        # 按分类统计
        category_stats = {}
        for item in self.question_items:
            if item.category not in category_stats:
                category_stats[item.category] = {
                    "total_questions": 0,
                    "asked_questions": 0,
                    "total_weight": 0,
                    "asked_weight": 0,
                    "partial_weight": 0,
                    "avg_match_score": 0
                }
            
            stats = category_stats[item.category]
            stats["total_questions"] += 1
            stats["total_weight"] += item.weight
            stats["partial_weight"] += item.get_partial_score()
            
            if item.is_asked:
                stats["asked_questions"] += 1
                stats["asked_weight"] += item.weight
        
        # 计算各分类的完成率
        for category, stats in category_stats.items():
            if stats["total_weight"] > 0:
                stats["perfect_completion_rate"] = (stats["asked_weight"] / stats["total_weight"]) * 100
                stats["partial_completion_rate"] = (stats["partial_weight"] / stats["total_weight"]) * 100
            else:
                stats["perfect_completion_rate"] = 100
                stats["partial_completion_rate"] = 100
            
            # 计算平均匹配分数
            category_items = [item for item in self.question_items if item.category == category]
            if category_items:
                stats["avg_match_score"] = sum(item.best_match_score for item in category_items) / len(category_items)
        
        return {
            "perfect_score": round(perfect_percentage, 2),
            "partial_score": round(partial_percentage, 2),
            "recommended_score": round(partial_percentage, 2),  # 推荐使用部分分数
            "asked_questions": len([item for item in self.question_items if item.is_asked]),
            "total_questions": len(self.question_items),
            "perfect_weight": perfect_score,
            "partial_weight": partial_score,
            "total_weight": self.total_weight,
            "category_stats": category_stats,
            "evaluation": self._get_evaluation(partial_percentage),
            "scoring_method": "intelligent_partial_matching"
        }
    
    def _get_evaluation(self, percentage: float) -> Dict[str, str]:
        """根据得分给出评价"""
        if percentage >= 90:
            level = "优秀"
            comment = "问诊非常全面，几乎涵盖了所有重要问题，表达专业准确"
        elif percentage >= 80:
            level = "良好" 
            comment = "问诊较为全面，涵盖了大部分重要问题，专业性良好"
        elif percentage >= 70:
            level = "中等"
            comment = "问诊基本合格，但还有一些重要问题遗漏或询问不够深入"
        elif percentage >= 60:
            level = "及格"
            comment = "问诊不够全面，遗漏了较多重要问题，需要改进"
        else:
            level = "不及格"
            comment = "问诊严重不足，大部分关键信息未获取，需要大幅改进"
        
        return {
            "level": level,
            "comment": comment
        }
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """获取详细评分报告"""
        score_result = self.calculate_score()
        
        # 分类问题
        fully_matched = []  # 完全匹配
        partially_matched = []  # 部分匹配
        missed_questions = []  # 未匹配
        
        for item in self.question_items:
            item_dict = item.to_dict()
            if item.is_asked:
                fully_matched.append(item_dict)
            elif item.best_match_score >= 30:  # 有一定匹配度但未达到阈值
                partially_matched.append(item_dict)
            else:
                missed_questions.append(item_dict)
        
        return {
            "score_summary": score_result,
            "fully_matched_questions": fully_matched,
            "partially_matched_questions": partially_matched,
            "missed_questions": missed_questions,
            "conversation_count": len([msg for msg in self.conversation_history if msg["role"] == "user"]),
            "report_time": datetime.now().isoformat(),
            "case_info": {
                "patient_name": self.case_data.get("basics", {}).get("name", "Unknown"),
                "disease": self.case_data.get("disease", "Unknown"),
                "chief_complaint": self.case_data.get("chief_complaint", ""),
                "diagnosis": self.case_data.get("diagnosis", {})
            },
            "system_info": {
                "scoring_method": "AI智能评分",
                "threshold": self.threshold,
                "ai_model": "gpt-3.5-turbo"
            }
        }
    
    def get_intelligent_suggestions(self) -> List[str]:
        """获取智能改进建议"""
        suggestions = []
        
        # 分析未匹配和部分匹配的问题
        missed_questions = [item for item in self.question_items if not item.is_asked]
        partial_questions = [item for item in self.question_items 
                           if not item.is_asked and item.best_match_score >= 30]
        
        if not missed_questions:
            suggestions.append("🎉 问诊非常全面，所有重要问题都已涉及！")
            return suggestions
        
        # 针对部分匹配的问题给出具体建议
        if partial_questions:
            suggestions.append("💡 以下问题已部分涉及，建议更深入询问：")
            for item in partial_questions[:3]:
                if item.evaluations:
                    latest_eval = item.evaluations[-1]
                    if latest_eval.get("suggestions"):
                        suggestions.append(f"   • {item.question}: {latest_eval['suggestions']}")
        
        # 针对完全未涉及的问题
        completely_missed = [item for item in missed_questions if item.best_match_score < 30]
        if completely_missed:
            suggestions.append("📋 建议补充询问以下重要问题：")
            
            # 按分类分组
            category_missed = {}
            for item in completely_missed:
                if item.category not in category_missed:
                    category_missed[item.category] = []
                category_missed[item.category].append(item.question)
            
            for category, questions in category_missed.items():
                if len(questions) <= 2:
                    for q in questions:
                        suggestions.append(f"   • {q}")
                else:
                    suggestions.append(f"   • {category}相关：{questions[0]} 等{len(questions)}个问题")
        
        return suggestions

    def get_suggestions(self) -> List[str]:
        """获取改进建议（兼容接口）"""
        return self.get_intelligent_suggestions()


class IntelligentScoringManager:
    """智能评分管理器"""
    
    def __init__(self, default_threshold: float = 60.0):
        self.default_threshold = default_threshold
        self.active_sessions = {}  # session_id -> IntelligentScoringSystem
    
    def create_session(self, session_id: str, case_data: Dict[str, Any], 
                      threshold: float = None, engine=None) -> IntelligentScoringSystem:
        """创建智能评分会话"""
        if threshold is None:
            threshold = self.default_threshold
            
        scoring_system = IntelligentScoringSystem(case_data, threshold, engine)
        self.active_sessions[session_id] = scoring_system
        return scoring_system
    
    def get_session(self, session_id: str) -> Optional[IntelligentScoringSystem]:
        """获取评分会话"""
        return self.active_sessions.get(session_id)
    
    def process_message(self, session_id: str, message: str, role: str = "user"):
        """处理消息"""
        scoring_system = self.get_session(session_id)
        if scoring_system:
            scoring_system.process_message(message, role)
    
    def get_score_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取智能评分报告"""
        scoring_system = self.get_session(session_id)
        if scoring_system:
            return scoring_system.get_detailed_report()
        return None
    
    def delete_session(self, session_id: str):
        """删除评分会话"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]


# 全局智能评分管理器实例
intelligent_scoring_manager = IntelligentScoringManager()
