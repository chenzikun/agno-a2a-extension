#!/usr/bin/env python3
"""
A2A协议兼容性测试脚本

基于a2a-python的test_client.py标准测试模式，
专注于验证A2A协议的标准实现，而不是数据处理。
"""

import asyncio
import sys
import argparse
from uuid import uuid4
from typing import Dict
import httpx
from a2a.client import A2AClient
from a2a.types import (
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Role,
    Message,
    TextPart,
)
from a2a.client.errors import A2AClientHTTPError, A2AClientJSONError

# 默认超时设置
DEFAULT_TIMEOUT = 30.0

class A2AProtocolTester:
    """A2A协议标准测试器"""
    
    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = timeout
        
    async def test_agent_card_retrieval(self, agent_url: str) -> bool:
        """
        测试Agent Card获取功能
        
        Args:
            agent_url: 代理服务URL
            
        Returns:
            bool: 测试是否成功
        """
        print(f"\n=== 测试Agent Card获取: {agent_url} ===")
        
        try:
            limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)
            async with httpx.AsyncClient(timeout=self.timeout, limits=limits) as httpx_client:
                # 获取Agent Card
                client = await A2AClient.get_client_from_agent_card_url(
                    httpx_client, agent_url
                )
                
                print(f"✓ 成功获取Agent Card")
                print(f"  代理名称: {client.agent_card.name}")
                print(f"  代理描述: {client.agent_card.description}")
                print(f"  协议版本: {client.agent_card.version}")
                print(f"  输入模式: {client.agent_card.default_input_modes}")
                print(f"  输出模式: {client.agent_card.default_output_modes}")
                
                if client.agent_card.capabilities:
                    print(f"  能力支持: {client.agent_card.capabilities}")
                
                if client.agent_card.skills:
                    print(f"  技能数量: {len(client.agent_card.skills)}")
                    for skill in client.agent_card.skills:
                        print(f"    - {skill.name}: {skill.description}")
                
                return True
                
        except A2AClientHTTPError as e:
            print(f"❌ HTTP错误: {e}")
            if hasattr(e, '__cause__') and e.__cause__:
                print(f"   原始错误: {e.__cause__}")
            return False
        except A2AClientJSONError as e:
            print(f"❌ JSON解析错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            return False
    
    async def test_message_send(self, agent_url: str, message: str = "Hello") -> bool:
        """
        测试标准消息发送功能
        
        Args:
            agent_url: 代理服务URL
            message: 发送的消息内容
            
        Returns:
            bool: 测试是否成功
        """
        print(f"\n=== 测试标准消息发送: {agent_url} ===")
        
        try:
            limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)
            async with httpx.AsyncClient(timeout=self.timeout, limits=limits) as httpx_client:
                client = await A2AClient.get_client_from_agent_card_url(
                    httpx_client, agent_url
                )
                
                # 创建标准A2A消息请求
                request_id = uuid4().hex
                message_obj = Message(
                    role=Role.user,
                    parts=[TextPart(text=message)],
                    messageId=uuid4().hex
                )
                
                request = SendMessageRequest(
                    id=request_id,
                    params=MessageSendParams(message=message_obj)
                )
                
                print(f"发送消息: '{message}'")
                print(f"请求ID: {request_id}")
                
                # 发送请求
                response = await client.send_message(request)
                
                print(f"✓ 成功接收响应")
                print(f"  响应ID: {response.root.id}")
                print(f"  响应角色: {response.root.result.role}")
                
                # 检查响应结构
                if hasattr(response.root.result, 'parts') and response.root.result.parts:
                    response_text = ""
                    for part in response.root.result.parts:
                        if hasattr(part.root, 'text'):
                            response_text += part.root.text
                    
                    print(f"  响应内容: {response_text[:100]}{'...' if len(response_text) > 100 else ''}")
                
                return True
                
        except A2AClientHTTPError as e:
            print(f"❌ HTTP错误: {e}")
            if hasattr(e, '__cause__') and e.__cause__:
                print(f"   原始错误: {e.__cause__}")
            return False
        except A2AClientJSONError as e:
            print(f"❌ JSON解析错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            return False
    
    async def test_streaming_message_send(self, agent_url: str, message: str = "Hello streaming") -> bool:
        """
        测试流式消息发送功能
        
        Args:
            agent_url: 代理服务URL
            message: 发送的消息内容
            
        Returns:
            bool: 测试是否成功
        """
        print(f"\n=== 测试流式消息发送: {agent_url} ===")
        
        try:
            limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)
            async with httpx.AsyncClient(timeout=self.timeout, limits=limits) as httpx_client:
                client = await A2AClient.get_client_from_agent_card_url(
                    httpx_client, agent_url
                )
                
                # 检查是否支持流式传输
                if not client.agent_card.capabilities.streaming:
                    print("⚠️  该代理不支持流式传输，跳过流式测试")
                    return True
                
                # 创建标准A2A流式消息请求
                request_id = uuid4().hex
                message_obj = Message(
                    role=Role.user,
                    parts=[TextPart(text=message)],
                    messageId=uuid4().hex
                )
                
                request = SendStreamingMessageRequest(
                    id=request_id,
                    params=MessageSendParams(message=message_obj)
                )
                
                print(f"发送流式消息: '{message}'")
                print(f"请求ID: {request_id}")
                
                # 发送流式请求
                response_count = 0
                full_response = ""
                
                async for response in client.send_message_streaming(request):
                    response_count += 1
                    print(f"  接收流式响应 #{response_count}")
                    
                    if hasattr(response.root.result, 'parts') and response.root.result.parts:
                        for part in response.root.result.parts:
                            if hasattr(part.root, 'text'):
                                chunk_text = part.root.text
                                full_response += chunk_text
                                print(f"    块内容: {chunk_text}")
                
                print(f"✓ 流式传输完成")
                print(f"  总响应块数: {response_count}")
                print(f"  完整响应长度: {len(full_response)} 字符")
                
                return True
                
        except A2AClientHTTPError as e:
            print(f"❌ HTTP错误: {e}")
            if hasattr(e, '__cause__') and e.__cause__:
                print(f"   原始错误: {e.__cause__}")
            return False
        except A2AClientJSONError as e:
            print(f"❌ JSON解析错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            return False
    
    async def test_protocol_compliance(self, agent_url: str) -> Dict[str, bool]:
        """
        测试A2A协议合规性
        
        Args:
            agent_url: 代理服务URL
            
        Returns:
            Dict[str, bool]: 各项测试结果
        """
        print(f"\n=== A2A协议合规性测试: {agent_url} ===")
        
        results = {}
        
        # 1. 测试Agent Card获取
        results['agent_card'] = await self.test_agent_card_retrieval(agent_url)
        
        # 2. 测试标准消息发送
        results['message_send'] = await self.test_message_send(agent_url)
        
        # 3. 测试流式消息发送
        results['streaming'] = await self.test_streaming_message_send(agent_url)
        
        return results

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="A2A协议标准合规性测试")
    parser.add_argument('--agent-url', default="http://localhost:8000", help="代理服务URL")
    parser.add_argument('--team-url', default="http://localhost:9000", help="团队服务URL")
    parser.add_argument('--timeout', type=float, default=DEFAULT_TIMEOUT, help="HTTP请求超时时间（秒）")
    parser.add_argument('--skip-team', action='store_true', help="跳过团队测试")
    parser.add_argument('--skip-streaming', action='store_true', help="跳过流式测试")
    return parser.parse_args()

async def main():
    """主函数"""
    args = parse_args()
    
    print("=" * 60)
    print("A2A协议标准合规性测试")
    print("=" * 60)
    print(f"代理URL: {args.agent_url}")
    if not args.skip_team:
        print(f"团队URL: {args.team_url}")
    print(f"超时设置: {args.timeout}秒")
    print(f"流式测试: {'禁用' if args.skip_streaming else '启用'}")
    print("=" * 60)
    
    tester = A2AProtocolTester(timeout=args.timeout)
    
    # 测试代理服务
    print("\n" + "=" * 40)
    print("测试代理服务")
    print("=" * 40)
    
    agent_results = await tester.test_protocol_compliance(args.agent_url)
    
    # 测试团队服务（如果未跳过）
    team_results = None
    if not args.skip_team:
        print("\n" + "=" * 40)
        print("测试团队服务")
        print("=" * 40)
        
        team_results = await tester.test_protocol_compliance(args.team_url)
    
    # 测试结果总结
    print("\n" + "=" * 60)
    print("A2A协议合规性测试结果")
    print("=" * 60)
    
    # 代理测试结果
    print("\n代理服务测试结果:")
    for test_name, result in agent_results.items():
        status = "✓ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    # 团队测试结果
    if team_results:
        print("\n团队服务测试结果:")
        for test_name, result in team_results.items():
            status = "✓ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
    
    # 总体评估
    all_agent_tests_passed = all(agent_results.values())
    all_team_tests_passed = all(team_results.values()) if team_results else True
    
    if all_agent_tests_passed and all_team_tests_passed:
        print("\n🎉 所有A2A协议测试通过！")
        print("该服务完全符合A2A协议标准。")
        return 0
    else:
        print("\n⚠️  部分A2A协议测试失败")
        print("该服务不完全符合A2A协议标准，需要进一步检查。")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
