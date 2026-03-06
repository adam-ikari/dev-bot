#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时 IPC 通讯模块

基于 Unix Socket 的进程间实时通讯机制
"""

import asyncio
import json
import os
import socket
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List


class IPCMessage:
    """IPC 消息"""
    
    def __init__(self, message_type: str, data: Dict[str, Any], source: str = ""):
        self.message_type = message_type
        self.data = data
        self.source = source
        self.timestamp = asyncio.get_event_loop().time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_type": self.message_type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IPCMessage':
        """从字典创建消息"""
        return cls(
            message_type=data["message_type"],
            data=data["data"],
            source=data.get("source", ""),
            timestamp=data.get("timestamp", 0)
        )
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict()) + "\n"
    
    @classmethod
    def from_json(cls, json_str: str) -> 'IPCMessage':
        """从 JSON 字符串创建消息"""
        return cls.from_dict(json.loads(json_str))


class IPCServer:
    """IPC 服务器（Unix Socket）"""
    
    def __init__(self, socket_path: Path):
        self.socket_path = socket_path
        self.server: Optional[asyncio.Server] = None
        self.clients: Dict[str, asyncio.StreamReader] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.is_running = False
        
        # 消息队列
        self.message_queue: asyncio.Queue = asyncio.Queue()
    
    async def start(self):
        """启动 IPC 服务器"""
        # 删除旧的 socket 文件
        if self.socket_path.exists():
            self.socket_path.unlink()
        
        # 创建 Unix socket 服务器
        self.server = await asyncio.start_unix_server(
            self._handle_connection,
            path=str(self.socket_path)
        )
        
        self.is_running = True
        print(f"[IPC Server] 启动在: {self.socket_path}")
        
        # 启动消息处理循环
        asyncio.create_task(self._process_messages())
    
    async def stop(self):
        """停止 IPC 服务器"""
        self.is_running = False
        
        if self.server:
            self.server.close()
        
        if self.socket_path.exists():
            self.socket_path.unlink()
        
        print(f"[IPC Server] 已停止")
    
    def on(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    async def broadcast(self, message: IPCMessage):
        """广播消息给所有客户端"""
        if not self.is_running:
            return
        
        for client_id, reader in self.clients.items():
            try:
                writer = writer = reader._transport.get_extra_info('writer')
                if writer and not writer.is_closing():
                    writer.write(message.to_json().encode())
                    await writer.drain()
            except Exception as e:
                print(f"[IPC Server] 发送给客户端 {client_id} 失败: {e}")
    
    async def send_to(self, client_id: str, message: IPCMessage):
        """发送消息给指定客户端"""
        if client_id not in self.clients:
            return False
        
        try:
            reader = self.clients[client_id]
            writer = reader._transport.get_extra_info('writer')
            if writer and not writer.is_closing():
                writer.write(message.to_json().encode())
                await writer.drain()
                return True
        except Exception as e:
            print(f"[IPC Server] 发送给客户端 {client_id} 失败: {e}")
            return False
        
        return False
    
    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """处理新的客户端连接"""
        client_id = f"client_{id(reader)}"
        self.clients[client_id] = reader
        
        print(f"[IPC Server] 客户端连接: {client_id}")
        
        # 保存 writer 到 reader
        writer._transport.set_extra_info('writer', writer)
        
        # 处理客户端消息
        try:
            await self._handle_client(client_id, reader, writer)
        finally:
            # 客户端断开
            if client_id in self.clients:
                del self.clients[client_id]
            if not writer.is_closing():
                writer.close()
            print(f"[IPC Server] 客户端断开: {client_id}")
    
    async def _handle_client(self, client_id: str, reader: asyncio.StreamReader, writer):
        """处理客户端消息"""
        try:
            while self.is_running:
                # 读取消息（以换行符分隔）
                line = await reader.readline()
                
                if not line:
                    break
                
                # 解析消息
                try:
                    message = IPCMessage.from_json(line.decode().strip())
                    await self.message_queue.put((client_id, message))
                except Exception as e:
                    print(f"[IPC Server] 解析消息失败: {e}")
        
        except Exception as e:
            print(f"[IPC Server] 处理客户端 {client_id} 出错: {e}")
        finally:
            # 客户端断开
            if client_id in self.clients:
                del self.clients[client_id]
            writer.close()
            print(f"[IPC Server] 客户端断开: {client_id}")
    
    async def _process_messages(self):
        """处理消息队列"""
        while self.is_running:
            try:
                client_id, message = await self.message_queue.get()
                
                # 调用消息处理器
                handlers = self.message_handlers.get(message.message_type, [])
                
                for handler in handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(client_id, message)
                        else:
                            handler(client_id, message)
                    except Exception as e:
                        print(f"[IPC Server] 处理消息失败: {e}")
            
            except Exception as e:
                print(f"[IPC Server] 处理消息队列出错: {e}")


class IPCClient:
    """IPC 客户端（Unix Socket）"""
    
    def __init__(self, socket_path: Path, client_id: Optional[str] = None):
        self.socket_path = socket_path
        self.client_id = client_id or f"client_{os.getpid()}"
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.is_connected = False
        self.message_handlers: Dict[str, List[Callable]] = {}
        
        # 消息队列
        self.message_queue: asyncio.Queue = asyncio.Queue()
    
    async def connect(self):
        """连接到 IPC 服务器"""
        if self.is_connected:
            return True
        
        try:
            reader, writer = await asyncio.open_unix_connection(str(self.socket_path))
            self.reader = reader
            self.writer = writer
            self.is_connected = True
            
            print(f"[IPC Client {self.client_id}] 已连接到服务器")
            
            # 启动消息接收循环
            asyncio.create_task(self._receive_messages())
            
            return True
        except Exception as e:
            print(f"[IPC Client {self.client_id}] 连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if not self.is_connected:
            return
        
        self.is_connected = False
        
        if self.writer:
            self.writer.close()
        
        if self.reader:
            self.reader.feed_eof()
        
        print(f"[IPC Client {self.client_id}] 已断开连接")
    
    def on(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    async def send(self, message: IPCMessage):
        """发送消息到服务器"""
        if not self.is_connected or not self.writer:
            return False
        
        try:
            self.writer.write(message.to_json().encode())
            await self.writer.drain()
            return True
        except Exception as e:
            print(f"[IPC Client {self.client_id}] 发送消息失败: {e}")
            return False
    
    async def _receive_messages(self):
        """接收服务器消息"""
        try:
            while self.is_connected:
                # 读取消息
                line = await self.reader.readline()
                
                if not line:
                    break
                
                # 解析消息
                try:
                    message = IPCMessage.from_json(line.decode().strip())
                    await self.message_queue.put(message)
                    
                    # 调用消息处理器
                    handlers = self.message_handlers.get(message.message_type, [])
                    
                    for handler in handlers:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(message)
                            else:
                                handler(message)
                        except Exception as e:
                            print(f"[IPC Client {self.client_id}] 处理消息失败: {e}")
                
                except Exception as e:
                    print(f"[IPC Client {self.client_id}] 解析消息失败: {e}")
        
        except Exception as e:
            print(f"[IPC Client {self.client_id}] 接收消息出错: {e}")
        finally:
            await self.disconnect()


# 全局 IPC 服务器实例
_global_ipc_server: Optional[IPCServer] = None


def get_ipc_server(socket_path: Path) -> IPCServer:
    """获取全局 IPC 服务器实例"""
    global _global_ipc_server
    
    if _global_ipc_server is None:
        _global_ipc_server = IPCServer(socket_path)
    
    return _global_ipc_server


# 预定义的消息类型
class IPCMessageType:
    """IPC 消息类型"""
    
    # 进程管理
    PROCESS_REGISTER = "process_register"      # 进程注册
    PROCESS_STATUS = "process_status"            # 进程状态更新
    PROCESS_EXIT = "process_exit"                # 进程退出
    PROCESS_RESTART = "process_restart"          # 进程重启
    
    # 系统状态
    SYSTEM_STATUS = "system_status"              # 系统状态
    SYSTEM_COMMAND = "system_command"            # 系统命令
    
    # 日志
    LOG_DEBUG = "log_debug"                      # 调试日志
    LOG_INFO = "log_info"                        # 信息日志
    LOG_WARNING = "log_warning"                  # 警告日志
    LOG_ERROR = "log_error"                      # 错误日志
    
    # AI 对话
    DIALOGUE_START = "dialogue_start"            # 对话开始
    DIALOGUE_MESSAGE = "dialogue_message"          # 对话消息
    DIALOGUE_END = "dialogue_end"                # 对话结束
    
    # 任务
    TASK_SUBMIT = "task_submit"                  # 任务提交
    TASK_UPDATE = "task_update"                  # 任务更新
    TASK_COMPLETE = "task_complete"              # 任务完成
    
    # 心跳
    HEARTBEAT = "heartbeat"                      # 心跳