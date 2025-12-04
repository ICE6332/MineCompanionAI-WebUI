"""LLM 服务集成测试脚本。

用于验证 LLM 服务配置加载和 API 调用功能。
"""

import asyncio
import pytest
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from core.llm.service import LLMService

@pytest.mark.asyncio
async def test_llm_service():
    print("=" * 60)
    print("LLM 服务测试")
    print("=" * 60)
    
    # 1. 检查配置
    llm_service = LLMService()

    print(f"[配置检查]")
    print(f"Provider: {llm_service.config['provider']}")
    print(f"Model: {llm_service.config['model']}")
    print(f"Base URL: {llm_service.config['base_url']}")
    print(f"API Key: {'*' * 6 if llm_service.config['api_key'] else '未设置'}")
    
    if not llm_service.config['api_key'] or llm_service.config['api_key'] == "YOUR_API_KEY_HERE":
        print("\n[警告] 未设置有效的 API Key，跳过真实调用测试。")
        print("请在 config/settings.json 或环境变量中配置 API Key。")
        return

    # 2. 发起测试调用
    print(f"\n[API 调用测试]")
    messages = [
        {"role": "user", "content": "你好，请用一句话介绍你自己。"}
    ]
    
    try:
        print("正在发送请求...")
        response = await llm_service.chat_completion(messages=messages)
        content = response["choices"][0]["message"]["content"]
        print(f"\n[响应成功]")
        print(f"回复内容: {content}")
        print(f"消耗 Token: {response.get('usage', {})}")
    except Exception as e:
        print(f"\n[调用失败]")
        print(f"错误信息: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_service())
