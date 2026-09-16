"""
chroma_demo.py - Day 2: ChromaDB 向量数据库演示（修复版）
"""

import os
import requests
import chromadb

# ========== 配置区 ==========
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    raise ValueError("请先设置环境变量 DASHSCOPE_API_KEY")

CHROMA_PATH = "./chroma_db"
EMBEDDING_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
EMBEDDING_MODEL = "qwen3.7-text-embedding"


# ========== 1. Embedding 函数（修复：按 index 排序） ==========
def get_embeddings(texts: list) -> list:
    """
    调用通义千问 Embedding API
    关键修复：按返回的 index 字段排序，确保向量和文本严格对应
    """
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": EMBEDDING_MODEL,
        "input": texts
    }
    
    response = requests.post(EMBEDDING_URL, headers=headers, json=payload)
    response.raise_for_status()
    
    data = response.json()
    
    # 🔧 修复点1：按 index 排序，确保顺序和输入一致
    sorted_data = sorted(data["data"], key=lambda x: x["index"])
    embeddings = [item["embedding"] for item in sorted_data]
    return embeddings


# ========== 2. 初始化 ChromaDB（修复：指定 cosine 距离） ==========
print("🚀 正在初始化 ChromaDB...")
client = chromadb.PersistentClient(path=CHROMA_PATH)

# 清理旧数据
try:
    client.delete_collection(name="warranty_docs")
    print("🗑️  已清除旧数据")
except:
    pass

# 🔧 修复点2：明确指定使用 cosine 距离，这样 1-distance = 相似度
collection = client.get_or_create_collection(
    name="warranty_docs",
    metadata={"hnsw:space": "cosine"}
)
print(f"✅ Collection 'warranty_docs' 创建成功（距离度量：cosine）\n")


# ========== 3. 准备测试文本 ==========
documents = [
    "本产品整机保修期为1年，自购买之日起计算。",
    "主要部件包括主板、显示屏、电池，保修期为3年。",
    "人为损坏、进水、摔落导致的故障不在保修范围内。",
    "申请保修请拨打客服热线：400-123-4567，工作日 9:00-18:00。",
    "退换货政策：7天内无理由退货，15天内质量问题换货。",
    "产品出现非人为故障，请携带发票到指定维修点免费维修。",
    "软件问题可通过官网下载补丁自行解决，不涉及硬件保修。",
    "保修期内维修不收取任何费用，包括配件费和人工费。",
    "超过保修期的维修需先报价，经用户同意后方可进行。",
    "境外购买的产品不享受国内保修服务，请联系购买地客服。"
]

metadatas = [
    {"source": "保修政策.txt", "chunk_id": 0},
    {"source": "保修政策.txt", "chunk_id": 1},
    {"source": "保修政策.txt", "chunk_id": 2},
    {"source": "客服手册.docx", "chunk_id": 3},
    {"source": "售后政策.txt", "chunk_id": 4},
    {"source": "保修政策.txt", "chunk_id": 5},
    {"source": "技术文档.pdf", "chunk_id": 6},
    {"source": "保修政策.txt", "chunk_id": 7},
    {"source": "售后政策.txt", "chunk_id": 8},
    {"source": "保修政策.txt", "chunk_id": 9},
]

ids = [f"chunk_{i}" for i in range(len(documents))]

print(f"📄 准备添加 {len(documents)} 段文本...")
print("⏳ 正在调用通义千问 Embedding API...")
embeddings = get_embeddings(documents)
print(f"✅ 成功生成 {len(embeddings)} 个向量，维度：{len(embeddings[0])}\n")


# ========== 4. 存入 ChromaDB ==========
collection.add(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas
)
print("✅ 数据已存入 ChromaDB\n")


# ========== 5. 查询测试 ==========
test_questions = [
    "电脑坏了怎么保修",
    "保修期多久",
    "人为损坏能保修吗"
]

for question in test_questions:
    print(f"\n{'='*60}")
    print(f"🔍 查询问题：{question}")
    
    question_embedding = get_embeddings([question])
    results = collection.query(
        query_embeddings=question_embedding,
        n_results=3,
        include=["documents", "metadatas", "distances"]
    )
    
    print("-" * 60)
    for i in range(3):
        doc = results["documents"][0][i]
        meta = results["metadatas"][0][i]
        distance = results["distances"][0][i]
        similarity = 1 - distance  # cosine 距离下，1-distance = 相似度
        
        print(f"\n[{i+1}] 相似度: {similarity:.4f} | 来源: {meta['source']} (chunk_{meta['chunk_id']})")
        print(f"    文本：{doc}")

print(f"\n{'='*60}")
print("🎉 全部测试完成！")