"""
core/llm_client.py - DeepSeek LLM API 封装
"""

import os
import requests


class LLMClient:
    """DeepSeek LLM API 客户端"""
    
    def __init__(self, api_key=None, model="deepseek-chat"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("请先设置环境变量 DEEPSEEK_API_KEY")
        
        self.model = model
        self.url = "https://api.deepseek.com/chat/completions"
    
    def ask(self, system_prompt: str, user_prompt: str, 
            temperature: float = 0.3, max_tokens: int = 1000) -> str:
        """
        调用 LLM 生成回答
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(self.url, headers=headers, json=payload)
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]