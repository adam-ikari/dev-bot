#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
开发循环中集成非阻塞 Spec 询问器
"""

from pathlib import Path
from dev_bot.nonblocking_inquirer import NonBlockingSpecInquirer


class DevelopmentSession:
    """开发会话 - 集成非阻塞 spec 询问"""
    
    def __init__(self, spec_file: Path, ai_tool: str = "iflow"):
        self.spec_file = spec_file
        self.inquirer = NonBlockingSpecInquirer(spec_file, ai_tool)
        self.inquirer.start_analysis()
    
    def check_spec_questions(self):
        """检查 spec 问题（在开发循环中定期调用）"""
        questions = self.inquirer.get_pending_questions()
        
        if questions:
            print("\n" + "=" * 60)
            print("📋 Spec 问题和建议")
            print("=" * 60)
            
            for i, q in enumerate(questions, 1):
                priority_mark = "🔴" if q.priority >= 4 else "🟡" if q.priority >= 2 else "🟢"
                print(f"\n{priority_mark} [{i}] {q.question}")
                print(f"   ID: {q.question_id}")
            
            print("\n💡 提示:这些问题不会阻塞开发，可以在方便时处理")
            print("=" * 60 + "\n")
    
    def get_question_detail(self, question_id: str):
        """获取问题详情和 AI 建议"""
        # 先在待处理队列中查找
        questions = self.inquirer.get_pending_questions()
        for q in questions:
            if q.question_id == question_id:
                detail = {
                    "question": q.question,
                    "context": q.context,
                    "priority": q.priority,
                    "timestamp": q.timestamp
                }
                
                # 获取 AI 建议
                suggestion = self.inquirer.ask_ai_for_suggestion(q.question)
                detail["suggestion"] = suggestion
                
                return detail
        
        return None
    
    def handle_question(self, question_id: str, action: str):
        """处理问题"""
        if action == "acknowledge":
            self.inquirer.acknowledge_question(question_id)
            print(f"✓ 已确认问题: {question_id}")
        elif action == "dismiss":
            self.inquirer.dismiss_question(question_id)
            print(f"✗ 已忽略问题: {question_id}")
    
    def cleanup(self):
        """清理资源"""
        self.inquirer.stop_analysis()


# 使用示例
def example_usage():
    """使用示例"""
    from pathlib import Path
    
    # 创建开发会话
    session = DevelopmentSession(Path("specs/feature.json"))
    
    try:
        # 在开发循环中定期检查问题
        import time
        for i in range(5):
            print(f"\n--- 开发循环 #{i + 1} ---")
            
            # 检查 spec 问题（非阻塞）
            session.check_spec_questions()
            
            # 继续开发工作...
            print("正在开发...")
            time.sleep(2)
        
        # 查看统计
        stats = session.inquirer.get_stats()
        print(f"\n📊 统计信息: {stats}")
        
    finally:
        session.cleanup()


if __name__ == "__main__":
    example_usage()