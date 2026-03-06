#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IPC realtime communication tests."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.ipc_realtime import IPCServer, IPCClient, IPCMessage


async def test_basic_communication():
    """Test basic IPC communication."""
    
    print("Testing IPC communication...")
    
    socket_path = Path.cwd() / ".ipc" / "test.sock"
    
    # Start server
    server = IPCServer(socket_path)
    messages = []
    
    async def handler(client_id, msg):
        messages.append((client_id, msg))
    
    server.on("test", handler)
    await server.start()
    
    await asyncio.sleep(0.5)
    
    # Connect client
    client = IPCClient(socket_path, "test_client")
    await client.connect()
    
    # Send message
    msg = IPCMessage("test", {"hello": "world"}, "client")
    await client.send(msg)
    
    await asyncio.sleep(0.5)
    
    # Cleanup
    await client.disconnect()
    await server.stop()
    
    # Verify
    if len(messages) > 0:
        print(f"Received {len(messages)} messages - PASS")
        return True
    else:
        print("No messages received - FAIL")
        return False


async def main():
    """Run tests."""
    result = await test_basic_communication()
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))