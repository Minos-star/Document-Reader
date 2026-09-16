"""
core/embedding_client.py - 通义千问 Embedding API 封装
"""

import os
import requests


class EmbeddingClient:
    """通义千问 Embedding API 客户端"""
    
    def __init__(self, api_key=None, model="qwen3.7-text-embedding"):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("请先设置环境变量 DASHSCOPE_API_KEY")
        
        self.model = model
        self.url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
    
    def embed(self, texts: list) -> list:
        """
        批量获取文本的 Embedding 向量
        返回: [[float, ...], ...] 按输入顺序
        """
        if not texts:
            return []
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": texts
        }
        
        response = requests.post(self.url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        # 按 index 排序，确保和输入顺序一致
        sorted_data = sorted(data["data"], key=lambda x: x["index"])
        embeddings = [item["embedding"] for item in sorted_data]
        
        return embeddings
    
    def embed_single(self, text: str) -> list:
        """单条文本的 Embedding"""
        return self.embed([text])[0]