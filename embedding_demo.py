"""
通义千问 Embedding 相似度对比脚本
=====================================

功能：
  1. 调用通义千问 Embedding API，把文本转成向量
  2. 计算两段文本的余弦相似度
  3. 对比 "产品保修期是多久" 和 "这个商品能保修多长时间" 的相似度
"""

import os                          # 用于读取环境变量
import numpy as np                 # 用于数值计算（向量、相似度）
import dashscope                   # 阿里云百炼平台的官方 Python SDK


# ---------- 第 1 步：准备待对比的两段文本 ----------
text_a = "产品保修期是多久"
text_b = "这个商品能保修多长时间"


# ---------- 第 2 步：调用 Embedding API ----------
def get_embedding(text: str) -> list[float]:
    """
    调用通义千问 Embedding 接口，把一段中文文本转成一个向量（浮点数列表）。
    """
    # 从环境变量 DASHSCOPE_API_KEY 中读取 API Key
    # 设置方法（PowerShell）：$env:DASHSCOPE_API_KEY = "你的key"
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未找到环境变量 DASHSCOPE_API_KEY，请先设置你的阿里云百炼 API Key。")

    # 调用 SDK 的 text_embeddings 接口
    # - model：使用的 embedding 模型，这里用 text-embedding-v3
    # - input：单条文本，SDK 也支持传一个列表同时处理多条
    resp = dashscope.TextEmbedding.call(
        api_key=api_key,
        model="text-embedding-v3",
        input=text,
    )

    # 检查接口是否成功
    if resp.status_code != 200:
        raise RuntimeError(f"Embedding 调用失败: {resp.code} - {resp.message}")

    # resp.output["embeddings"] 是一个列表，每个元素对应一条文本
    # 这里只传了一条，所以取第 0 个
    return resp.output["embeddings"][0]["embedding"]


# ---------- 第 3 步：计算余弦相似度 ----------
def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    余弦相似度公式：
        cosθ = (A · B) / (|A| × |B|)

    含义：两个向量夹角的余弦值。
      - 1  表示方向完全相同（语义一致）
      - 0  表示正交（语义无关）
      - -1 表示方向完全相反（语义相反）
    """
    a = np.array(vec_a)            # 把列表转成 numpy 向量，方便做数学运算
    b = np.array(vec_b)

    dot = np.dot(a, b)             # 向量点积：A · B
    norm_a = np.linalg.norm(a)     # 向量 A 的模长 |A|
    norm_b = np.linalg.norm(b)     # 向量 B 的模长 |B|

    return float(dot / (norm_a * norm_b))


# ---------- 第 4 步：主流程 ----------
def main():
    # 1) 把两段文本分别转成向量
    print("正在调用 Embedding API ...")
    vec_a = get_embedding(text_a)
    vec_b = get_embedding(text_b)
    print(f"向量维度：{len(vec_a)}")                # text-embedding-v3 默认 1024 维
    print(f"向量 a 前 5 维：{vec_a[:5]}")

    # 2) 计算余弦相似度
    score = cosine_similarity(vec_a, vec_b)
    print(f"\n句子 A：{text_a}")
    print(f"句子 B：{text_b}")
    print(f"余弦相似度：{score:.4f}")

    # 3) 直观判断
    if score > 0.8:
        comment = "语义高度一致"
    elif score > 0.5:
        comment = "语义比较接近"
    else:
        comment = "语义差异较大"
    print(f"结论：{comment}")


if __name__ == "__main__":
    main()
