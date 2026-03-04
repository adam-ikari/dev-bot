#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Git 管理器 - 自动创建和管理 Git 仓库
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


class GitManager:
    """Git 管理器"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.git_dir = self.project_path / '.git'
        self.is_repo = self.git_dir.exists()
    
    def init_repo(self, initial_commit: bool = True, commit_message: str = "Initial commit") -> bool:
        """初始化 Git 仓库"""
        if self.is_repo:
            print("  ! Git 仓库已存在")
            return True
        
        try:
            # 初始化仓库
            result = subprocess.run(
                ['git', 'init'],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"  ! Git 初始化失败: {result.stderr}")
                return False
            
            print("  ✓ Git 仓库初始化成功")
            
            # 创建 .gitignore
            self._create_gitignore()
            
            # 创建初始提交
            if initial_commit:
                self._create_initial_commit(commit_message)
            
            return True
            
        except Exception as e:
            print(f"  ! Git 初始化出错: {e}")
            return False
    
    def _create_gitignore(self):
        """创建 .gitignore 文件"""
        gitignore_path = self.project_path / '.gitignore'
        
        if gitignore_path.exists():
            return
        
        default_ignore = [
            '# Python',
            '__pycache__/',
            '*.py[cod]',
            '*$py.class',
            '*.so',
            '.Python',
            'build/',
            'develop-eggs/',
            'dist/',
            'downloads/',
            'eggs/',
            '.eggs/',
            'lib/',
            'lib64/',
            'parts/',
            'sdist/',
            'var/',
            'wheels/',
            '*.egg-info/',
            '.installed.cfg',
            '*.egg',
            '',
            '# Virtual Environment',
            'venv/',
            'env/',
            'ENV/',
            '.venv/',
            '',
            '# IDE',
            '.idea/',
            '.vscode/',
            '*.swp',
            '*.swo',
            '*~',
            '',
            '# Dev-Bot',
            '.dev-bot-cache/',
            '.error-logs/',
            '.ai-logs/',
            '',
            '# OS',
            '.DS_Store',
            'Thumbs.db',
            '',
            '# Logs',
            '*.log',
        ]
        
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(default_ignore))
        
        print("  ✓ .gitignore 文件已创建")
    
    def _create_initial_commit(self, commit_message: str):
        """创建初始提交"""
        try:
            # 添加所有文件
            subprocess.run(
                ['git', 'add', '.'],
                cwd=self.project_path,
                capture_output=True,
                check=True
            )
            
            # 创建提交
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.project_path,
                capture_output=True,
                check=True
            )
            
            print(f"  ✓ 初始提交创建成功: {commit_message}")
            
        except subprocess.CalledProcessError as e:
            print(f"  ! 创建初始提交失败: {e}")
    
    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> bool:
        """提交更改"""
        if not self.is_repo:
            print("  ! 不是 Git 仓库")
            return False
        
        try:
            # 检查是否有更改
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                print("  ! 没有需要提交的更改")
                return False
            
            # 添加文件
            if files:
                subprocess.run(
                    ['git', 'add'] + files,
                    cwd=self.project_path,
                    capture_output=True,
                    check=True
                )
            else:
                subprocess.run(
                    ['git', 'add', '.'],
                    cwd=self.project_path,
                    capture_output=True,
                    check=True
                )
            
            # 提交
            subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.project_path,
                capture_output=True,
                check=True
            )
            
            print(f"  ✓ 提交成功: {message}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ! 提交失败: {e}")
            return False
    
    def create_branch(self, branch_name: str, from_branch: Optional[str] = None) -> bool:
        """创建分支"""
        if not self.is_repo:
            print("  ! 不是 Git 仓库")
            return False
        
        try:
            cmd = ['git', 'branch', branch_name]
            if from_branch:
                cmd.append(from_branch)
            
            subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                check=True
            )
            
            print(f"  ✓ 分支创建成功: {branch_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ! 创建分支失败: {e}")
            return False
    
    def switch_branch(self, branch_name: str) -> bool:
        """切换分支"""
        if not self.is_repo:
            print("  ! 不是 Git 仓库")
            return False
        
        try:
            subprocess.run(
                ['git', 'checkout', branch_name],
                cwd=self.project_path,
                capture_output=True,
                check=True
            )
            
            print(f"  ✓ 切换到分支: {branch_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ! 切换分支失败: {e}")
            return False
    
    def merge_branch(self, branch_name: str, message: Optional[str] = None) -> bool:
        """合并分支"""
        if not self.is_repo:
            print("  ! 不是 Git 仓库")
            return False
        
        try:
            # 合并分支
            subprocess.run(
                ['git', 'merge', branch_name],
                cwd=self.project_path,
                capture_output=True,
                check=True
            )
            
            print(f"  ✓ 分支合并成功: {branch_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ! 合并分支失败: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取仓库状态"""
        if not self.is_repo:
            return {"is_repo": False}
        
        try:
            # 获取当前分支
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = result.stdout.strip()
            
            # 获取状态
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # 统计更改
            modified = sum(1 for line in status_lines if line and line[0] in ['M', 'MM'])
            added = sum(1 for line in status_lines if line and line[0] in ['A', 'AA'])
            deleted = sum(1 for line in status_lines if line and line[0] in ['D', 'DD'])
            untracked = sum(1 for line in status_lines if line and line[0] == '??')
            
            # 获取最近提交
            result = subprocess.run(
                ['git', 'log', '-1', '--oneline'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=True
            )
            last_commit = result.stdout.strip()
            
            return {
                "is_repo": True,
                "current_branch": current_branch,
                "modified": modified,
                "added": added,
                "deleted": deleted,
                "untracked": untracked,
                "last_commit": last_commit
            }
            
        except Exception as e:
            return {"is_repo": False, "error": str(e)}
    
    def display_status(self):
        """显示仓库状态"""
        status = self.get_status()
        
        if not status.get('is_repo'):
            print("  ! 不是 Git 仓库")
            return
        
        print(f"\n📊 Git 仓库状态:")
        print(f"  当前分支: {status.get('current_branch', 'N/A')}")
        print(f"  最后提交: {status.get('last_commit', 'N/A')}")
        print(f"  已修改: {status.get('modified', 0)}")
        print(f"  已添加: {status.get('added', 0)}")
        print(f"  已删除: {status.get('deleted', 0)}")
        print(f"  未跟踪: {status.get('untracked', 0)}")
    
    def create_tag(self, tag_name: str, message: Optional[str] = None) -> bool:
        """创建标签"""
        if not self.is_repo:
            print("  ! 不是 Git 仓库")
            return False
        
        try:
            cmd = ['git', 'tag', '-a', tag_name]
            if message:
                cmd.extend(['-m', message])
            
            subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                check=True
            )
            
            print(f"  ✓ 标签创建成功: {tag_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ! 创建标签失败: {e}")
            return False
    
    def get_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """获取提交历史"""
        if not self.is_repo:
            return []
        
        try:
            result = subprocess.run(
                ['git', 'log', f'-{limit}', '--pretty=format:%H|%an|%ai|%s'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            history = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        history.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'message': parts[3]
                        })
            
            return history
            
        except Exception as e:
            print(f"  ! 获取历史失败: {e}")
            return []


def auto_setup_git(project_path: Path, initial_commit: bool = True) -> GitManager:
    """自动设置 Git 仓库"""
    print(f"\n🔧 设置 Git 仓库...")
    
    git_manager = GitManager(project_path)
    
    if not git_manager.is_repo:
        # 初始化仓库
        if git_manager.init_repo(initial_commit=initial_commit):
            print("  ✓ Git 仓库设置完成")
        else:
            print("  ! Git 仓库设置失败")
    else:
        print("  ✓ Git 仓库已存在")
        git_manager.display_status()
    
    return git_manager