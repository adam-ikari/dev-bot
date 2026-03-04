#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知模块 - 邮件和通知功能
"""

import os
import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class Notifier:
    """通知管理器"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化通知管理器
        
        Args:
            config_path: 配置文件路径（默认：项目目录下的 .notifyrc）
        """
        self.config_path = config_path or Path.cwd() / ".notifyrc"
        self.config = self._load_config()
        self.enabled = self.config.get('enabled', False)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config = {
            'enabled': False,
            'email': {
                'enabled': False,
                'smtp_server': '',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_addr': '',
                'to_addr': '',
                'use_tls': True
            },
            'slack': {
                'enabled': False,
                'webhook_url': '',
                'channel': ''
            },
            'discord': {
                'enabled': False,
                'webhook_url': ''
            },
            'desktop': {
                'enabled': True
            }
        }
        
        if self.config_path.exists():
            try:
                import json
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 深度合并配置
                    for key, value in user_config.items():
                        if isinstance(value, dict) and key in config:
                            config[key].update(value)
                        else:
                            config[key] = value
            except Exception as e:
                print(f"  ! 加载通知配置失败: {e}")
        
        return config
    
    def notify(self, title: str, message: str, level: str = "info"):
        """
        发送通知
        
        Args:
            title: 通知标题
            message: 通知内容
            level: 通知级别 (info, warning, error, critical)
        """
        if not self.enabled:
            return
        
        print(f"\n📢 [{level.upper()}] {title}")
        print(f"   {message}\n")
        
        # 桌面通知
        if self.config.get('desktop', {}).get('enabled', True):
            self._send_desktop_notification(title, message, level)
        
        # 邮件通知
        if self.config.get('email', {}).get('enabled', False):
            self._send_email_notification(title, message, level)
        
        # Slack 通知
        if self.config.get('slack', {}).get('enabled', False):
            self._send_slack_notification(title, message, level)
        
        # Discord 通知
        if self.config.get('discord', {}).get('enabled', False):
            self._send_discord_notification(title, message, level)
    
    def _send_desktop_notification(self, title: str, message: str, level: str):
        """发送桌面通知"""
        try:
            # 根据系统选择通知方式
            if os.name == 'nt':  # Windows
                import win10toast
                toaster = win10toast.ToastNotifier()
                toaster.show_toast(title, message, duration=10)
            elif os.name == 'posix':
                # Linux/macOS
                if os.path.exists('/usr/bin/notify-send'):
                    subprocess.run([
                        'notify-send',
                        f'Dev-Bot: {title}',
                        message,
                        '-u', level
                    ], check=False)
        except Exception as e:
            print(f"  ! 桌面通知失败: {e}")
    
    def _send_email_notification(self, title: str, message: str, level: str):
        """发送邮件通知"""
        try:
            email_config = self.config['email']
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = email_config['from_addr']
            msg['To'] = email_config['to_addr']
            msg['Subject'] = f"[Dev-Bot] {title}"
            
            # 邮件正文
            body = f"""
级别: {level.upper()}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message}

---
此邮件由 Dev-Bot 自动发送
"""
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(
                email_config['smtp_server'],
                email_config['smtp_port']
            ) as server:
                if email_config.get('use_tls', True):
                    server.starttls()
                server.login(
                    email_config['username'],
                    email_config['password']
                )
                server.send_message(msg)
            
            print(f"  ✓ 邮件通知已发送: {email_config['to_addr']}")
            
        except Exception as e:
            print(f"  ! 邮件通知失败: {e}")
    
    def _send_slack_notification(self, title: str, message: str, level: str):
        """发送 Slack 通知"""
        try:
            import requests
            
            slack_config = self.config['slack']
            
            # 设置颜色
            colors = {
                'info': '#36a64f',
                'warning': '#ff9900',
                'error': '#ff0000',
                'critical': '#ff0000'
            }
            
            payload = {
                'channel': slack_config.get('channel', '#general'),
                'username': 'Dev-Bot',
                'icon_emoji': ':robot_face:',
                'attachments': [{
                    'color': colors.get(level, '#36a64f'),
                    'title': title,
                    'text': message,
                    'ts': int(datetime.now().timestamp())
                }]
            }
            
            response = requests.post(
                slack_config['webhook_url'],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"  ✓ Slack 通知已发送")
            else:
                print(f"  ! Slack 通知失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ! Slack 通知失败: {e}")
    
    def _send_discord_notification(self, title: str, message: str, level: str):
        """发送 Discord 通知"""
        try:
            import requests
            
            discord_config = self.config['discord']
            
            # 设置颜色
            colors = {
                'info': 0x36a64f,
                'warning': 0xff9900,
                'error': 0xff0000,
                'critical': 0xff0000
            }
            
            payload = {
                'username': 'Dev-Bot',
                'avatar_url': 'https://cdn.icon-icons.com/icons2/2107/PNG/512/extension_robot_icon_130739.png',
                'embeds': [{
                    'title': title,
                    'description': message,
                    'color': colors.get(level, 0x36a64f),
                    'timestamp': datetime.now().isoformat()
                }]
            }
            
            response = requests.post(
                discord_config['webhook_url'],
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                print(f"  ✓ Discord 通知已发送")
            else:
                print(f"  ! Discord 通知失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ! Discord 通知失败: {e}")
    
    def check_critical_patterns(self, output: str) -> bool:
        """
        检查输出中是否包含关键错误模式
        
        Args:
            output: 输出文本
            
        Returns:
            如果发现关键错误返回 True
        """
        critical_patterns = [
            'iflow需要重新登录',
            'please log in',
            'authentication failed',
            'unauthorized',
            '401 unauthorized',
            'session expired',
            'token expired',
            'login required',
            '重新登录',
            '请登录',
            '认证失败',
            '未授权'
        ]
        
        output_lower = output.lower()
        for pattern in critical_patterns:
            if pattern.lower() in output_lower:
                self.notify(
                    title='工作中断 - 需要用户干预',
                    message=f'检测到关键错误: "{pattern}"\n\n输出内容:\n{output[:500]}',
                    level='critical'
                )
                return True
        
        return False


def create_sample_config():
    """创建示例配置文件"""
    config = {
        "enabled": True,
        "email": {
            "enabled": False,
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "username": "your-email@example.com",
            "password": "your-password",
            "from_addr": "dev-bot@example.com",
            "to_addr": "your-email@example.com",
            "use_tls": True
        },
        "slack": {
            "enabled": False,
            "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
            "channel": "#dev-bot"
        },
        "discord": {
            "enabled": False,
            "webhook_url": "https://discord.com/api/webhooks/YOUR/WEBHOOK/URL"
        },
        "desktop": {
            "enabled": True
        }
    }
    
    import json
    config_path = Path.cwd() / ".notifyrc"
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 示例配置文件已创建: {config_path}")
    print("  请编辑此文件以配置你的通知设置")
    return config_path
