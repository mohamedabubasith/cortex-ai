#!/usr/bin/env python3
"""Test NVIDIA API directly"""
import asyncio
from openai import AsyncOpenAI

async def test_nvidia():
    # Replace with your actual NVIDIA API key
    api_key = "nvapi-REPLACE_WITH_YOUR_KEY"
    base_url = "https://integrate.api.nvidia.com/v1"
    model = "meta/llama3-70b-instruct"
    
    print(f"Testing NVIDIA API...")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print(f"API Key: {api_key[:15]}...")
    
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    
    try:
        # Test models list
        print("\n1. Testing models.list()...")
        models = await client.models.list()
        print(f"✅ Models list successful")
        
        # Test chat completion
        print("\n2. Testing chat completion...")
        stream = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hello"}],
            stream=True
        )
        
        response = ""
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                response += chunk.choices[0].delta.content
        
        print(f"✅ Chat completion successful")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_nvidia())
