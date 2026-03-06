#!/usr/bin/env python3

"""
非阻塞 AI Spec 询问器
在开发过程中 AI 可以主动询问 spec 相关问题，但不阻塞工作
"""

import json
import queue
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class SpecQuestion:
    """Spec 问题"""

    def __init__(self, question_id: str, question: str, context: str, priority: int = 1):
        self.question_id = question_id
        self.question = question
        self.context = context
        self.priority = priority  # 1-5, 5 最高
        self.timestamp = time.time()
        self.answer: Optional[str] = None
        self.resolved = False
        self.acknowledged = False  # 用户是否已查看


class NonBlockingSpecInquirer:
    """非阻塞 Spec 询问器"""

    def __init__(self, spec_file: Optional[Path] = None, ai_tool: str = "iflow"):
        self.spec_file = spec_file
        self.ai_tool = ai_tool
        self.spec: Optional[Dict[str, Any]] = None
        self.question_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.answered_questions: List[SpecQuestion] = []
        self.is_running = False
        self.analysis_thread: Optional[threading.Thread] = None

        if spec_file and spec_file.exists():
            self._load_spec()

    def _load_spec(self):
        """加载 spec 文件"""
        if self.spec_file and self.spec_file.exists():
            try:
                with open(self.spec_file, encoding='utf-8') as f:
                    self.spec = json.load(f)
            except Exception:
                pass

    def start_analysis(self):
        """启动后台 AI 分析"""
        if self.is_running:
            return

        self.is_running = True
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()

    def stop_analysis(self):
        """停止后台分析"""
        self.is_running = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)

    def _analysis_loop(self):
        """后台分析循环"""
        while self.is_running:
            try:
                # 分析 spec 并生成问题
                self._analyze_spec()
                # 等待一段时间再分析
                time.sleep(30)
            except Exception as e:
                print(f"[SpecInquirer] 分析错误: {e}")
                time.sleep(10)

    def _analyze_spec(self):
        """分析 spec 并生成问题"""
        if not self.spec:
            return

        # 检查缺失的部分
        missing_parts = self._check_missing_parts()
        if missing_parts:
            self._add_question(
                "missing_parts",
                f"发现 spec 缺少以下部分: {', '.join(missing_parts)}，是否需要补充？",
                json.dumps(missing_parts, ensure_ascii=False),
                priority=4
            )

        # 检查不完整的需求
        incomplete_requirements = self._check_incomplete_requirements()
        for req in incomplete_requirements:
            self._add_question(
                f"incomplete_req_{req['id']}",
                f"需求 {req['id']} 描述可能不完整: {req['description'][:50]}...",
                json.dumps(req, ensure_ascii=False),
                priority=3
            )

        # 检查缺少用户故事的需求
        requirements_without_stories = self._check_requirements_without_stories()
        if requirements_without_stories:
            self._add_question(
                "missing_user_stories",
                f"以下需求缺少用户故事: {', '.join(requirements_without_stories)}，是否需要添加？",
                json.dumps(requirements_without_stories, ensure_ascii=False),
                priority=2
            )

        # 检查缺少验收标准的需求
        requirements_without_criteria = self._check_requirements_without_criteria()
        if requirements_without_criteria:
            self._add_question(
                "missing_acceptance_criteria",
                f"以下需求缺少验收标准: {', '.join(requirements_without_criteria)}，是否需要添加？",
                json.dumps(requirements_without_criteria, ensure_ascii=False),
                priority=2
            )

    def _check_missing_parts(self) -> List[str]:
        """检查缺失的部分"""
        missing = []

        if not self.spec:
            return missing

        spec_type = self.spec.get('metadata', {}).get('type', 'feature')

        if spec_type == 'feature':
            if not self.spec.get('requirements'):
                missing.append('requirements')
            if not self.spec.get('user_stories'):
                missing.append('user_stories')
            if not self.spec.get('acceptance_criteria'):
                missing.append('acceptance_criteria')

        elif spec_type == 'api':
            if not self.spec.get('endpoints'):
                missing.append('endpoints')
            if not self.spec.get('models'):
                missing.append('models')

        elif spec_type == 'component':
            if not self.spec.get('props'):
                missing.append('props')
            if not self.spec.get('methods'):
                missing.append('methods')

        return missing

    def _check_incomplete_requirements(self) -> List[Dict]:
        """检查不完整的需求"""
        incomplete = []

        if not self.spec:
            return incomplete

        requirements = self.spec.get('requirements', [])
        for req in requirements:
            description = req.get('description', '')
            if len(description) < 20:
                incomplete.append(req)

        return incomplete

    def _check_requirements_without_stories(self) -> List[str]:
        """检查缺少用户故事的需求"""
        missing = []

        if not self.spec:
            return missing

        requirements = self.spec.get('requirements', [])
        user_stories = self.spec.get('user_stories', [])

        req_ids = {req.get('id') for req in requirements}
        story_req_ids = set()

        for story in user_stories:
            # 假设用户故事中有 requirement_id 字段
            if 'requirement_id' in story:
                story_req_ids.add(story['requirement_id'])

        missing = list(req_ids - story_req_ids)
        return missing

    def _check_requirements_without_criteria(self) -> List[str]:
        """检查缺少验收标准的需求"""
        missing = []

        if not self.spec:
            return missing

        requirements = self.spec.get('requirements', [])
        acceptance_criteria = self.spec.get('acceptance_criteria', [])

        req_ids = {req.get('id') for req in requirements}
        criteria_req_ids = set()

        for criteria in acceptance_criteria:
            if 'requirement_id' in criteria:
                criteria_req_ids.add(criteria['requirement_id'])

        missing = list(req_ids - criteria_req_ids)
        return missing

    def _add_question(self, question_id: str, question: str, context: str, priority: int = 1):
        """添加问题到队列"""
        # 检查是否已存在相同的问题
        for q in self.answered_questions:
            if q.question_id == question_id:
                return

        # 检查队列中是否已有相同问题
        try:
            # 创建临时队列来检查
            temp_queue = queue.PriorityQueue()
            has_duplicate = False
            while not self.question_queue.empty():
                try:
                    item = self.question_queue.get_nowait()
                    if item[2].question_id == question_id:
                        has_duplicate = True
                    temp_queue.put(item)
                except queue.Empty:
                    break

            # 将项目放回队列
            while not temp_queue.empty():
                self.question_queue.put(temp_queue.get())

            if has_duplicate:
                return
        except Exception:
            pass

        # 添加新问题
        spec_question = SpecQuestion(question_id, question, context, priority)
        # 使用负优先级，因为 PriorityQueue 是最小堆
        self.question_queue.put((-priority, time.time(), spec_question))

    def get_pending_questions(self, max_count: int = 5) -> List[SpecQuestion]:
        """获取待处理的问题"""
        questions = []
        temp_queue = queue.PriorityQueue()

        count = 0
        while not self.question_queue.empty() and count < max_count:
            try:
                item = self.question_queue.get_nowait()
                questions.append(item[2])
                temp_queue.put(item)
                count += 1
            except queue.Empty:
                break

        # 将未取出的项目放回队列
        while not temp_queue.empty():
            self.question_queue.put(temp_queue.get())

        return questions

    def acknowledge_question(self, question_id: str):
        """确认问题（用户已查看）"""
        for q in self.answered_questions:
            if q.question_id == question_id:
                q.acknowledged = True
                return

        # 检查队列中的问题
        temp_queue = queue.PriorityQueue()
        while not self.question_queue.empty():
            try:
                item = self.question_queue.get_nowait()
                if item[2].question_id == question_id:
                    item[2].acknowledged = True
                    self.answered_questions.append(item[2])
                else:
                    temp_queue.put(item)
            except queue.Empty:
                break

        while not temp_queue.empty():
            self.question_queue.put(temp_queue.get())

    def dismiss_question(self, question_id: str):
        """忽略问题"""
        temp_queue = queue.PriorityQueue()
        while not self.question_queue.empty():
            try:
                item = self.question_queue.get_nowait()
                if item[2].question_id != question_id:
                    temp_queue.put(item)
            except queue.Empty:
                break

        while not temp_queue.empty():
            self.question_queue.put(temp_queue.get())

    def ask_ai_for_suggestion(self, question: str) -> str:
        """向 AI 询问建议"""
        prompt = f"""基于以下 spec，回答问题：

Spec 内容：
```json
{json.dumps(self.spec, indent=2, ensure_ascii=False) if self.spec else '{}'}
```

问题：{question}

请提供详细的建议。
"""

        try:
            result = subprocess.run(
                [self.ai_tool],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return result.stdout
            else:
                return f"AI 调用失败: {result.stderr}"
        except Exception as e:
            return f"错误: {e}"

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "pending_questions": self.question_queue.qsize(),
            "answered_questions": len(self.answered_questions),
            "acknowledged_questions": sum(1 for q in self.answered_questions if q.acknowledged),
            "is_running": self.is_running
        }

    def print_pending_questions(self):
        """打印待处理问题"""
        questions = self.get_pending_questions()

        if not questions:
            print("✓ 没有待处理的 spec 问题")
            return

        print(f"\n📋 待处理的 Spec 问题 ({len(questions)}):")
        print("=" * 60)

        for i, q in enumerate(questions, 1):
            priority_mark = "🔴" if q.priority >= 4 else "🟡" if q.priority >= 2 else "🟢"
            print(f"\n{priority_mark} [{i}] {q.question}")
            print(f"   ID: {q.question_id}")
            print(f"   时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(q.timestamp))}")

        print("\n提示: 使用 acknowledge_question() 确认已查看，dismiss_question() 忽略问题")


def create_spec_inquirer(spec_file: Path, ai_tool: str = "iflow") -> NonBlockingSpecInquirer:
    """创建 spec 询问器实例"""
    return NonBlockingSpecInquirer(spec_file, ai_tool)
