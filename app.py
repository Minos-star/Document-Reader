"""
app.py - 智能文档问答系统 v1.0（语义检索版）
支持：多文档自动加载、增量入库、语义检索、来源追溯
"""

import os
import sys
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.document_reader import read_document
from core.chunker import chunk_text
from core.embedding_client import EmbeddingClient
from core.vector_store import VectorStore
from core.llm_client import LLMClient
from core.prompt_template import build_rag_prompt

DOCS_DIR = "./docs"
CHROMA_PATH = "./chroma_db_v1"


def get_file_hash(filepath: str) -> str:
    """计算文件 MD5 哈希，用于检测文档是否变更"""
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def scan_documents():
    """扫描 docs/ 目录，返回文档列表"""
    if not os.path.exists(DOCS_DIR):
        return []
    
    files = []
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith((".txt", ".pdf", ".docx")):
            files.append(filename)
    
    return sorted(files)


def load_documents(vector_store: VectorStore, embed_client: EmbeddingClient, 
                   force_reload: bool = False):
    """
    加载文档到向量库（支持增量加载）
    """
    if force_reload:
        print("🗑️  清空向量库...")
        vector_store.reset()
    
    existing_ids = vector_store.get_existing_ids()
    files = scan_documents()
    
    if not files:
        print("⚠️  docs/ 文件夹中没有文档")
        return
    
    print(f"📂 发现 {len(files)} 个文档")
    
    new_chunks = []
    
    for filename in files:
        filepath = os.path.join(DOCS_DIR, filename)
        file_hash = get_file_hash(filepath)
        
        # 用文件名+哈希前缀作为 chunk_id 前缀
        # 如果文件内容变了，哈希会变，会自动重新加载
        doc_prefix = f"{filename}_{file_hash[:8]}"
        test_id = f"{doc_prefix}_chunk_0"
        
        if test_id in existing_ids:
            print(f"   ⏭️  {filename} （已加载）")
            continue
        
        print(f"   📄 {filename} （新文档）")
        text = read_document(filepath)
        
        if text.startswith("错误"):
            print(f"      ❌ 读取失败: {text}")
            continue
        
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        
        for chunk_text_content, chunk_id in chunks:
            cid = f"{doc_prefix}_chunk_{chunk_id}"
            new_chunks.append({
                "id": cid,
                "text": chunk_text_content,
                "metadata": {
                    "source": filename,
                    "chunk_id": chunk_id,
                    "file_hash": file_hash
                }
            })
    
    if not new_chunks:
        print("✅ 所有文档已是最新")
        return
    
    print(f"\n⏳ 正在为 {len(new_chunks)} 个文本块生成 Embedding...")
    
    # 批量生成，每批 10 条（避免 API 限制）
    batch_size = 10
    all_embeddings = []
    total_batches = (len(new_chunks) + batch_size - 1) // batch_size
    
    for i in range(0, len(new_chunks), batch_size):
        batch = new_chunks[i:i + batch_size]
        texts = [c["text"] for c in batch]
        embs = embed_client.embed(texts)
        all_embeddings.extend(embs)
        print(f"   批次 {i // batch_size + 1}/{total_batches} ✅")
    
    vector_store.add_chunks(new_chunks, all_embeddings)
    print(f"✅ 成功入库 {len(new_chunks)} 个文本块")


def answer_question(vector_store: VectorStore, embed_client: EmbeddingClient,
                    llm_client: LLMClient, question: str):
    """
    完整的问答流程：检索 → 构造 Prompt → LLM 生成
    """
    print("🔍 语义检索中...")
    q_emb = embed_client.embed_single(question)
    results = vector_store.query(q_emb, n_results=3)
    
    # 构造检索结果（兼容 build_rag_prompt 格式）
    retrieved = []
    num_results = len(results["documents"][0])
    
    for i in range(num_results):
        retrieved.append({
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })
    
    # 构造 Prompt
    prompt = build_rag_prompt(retrieved, question)
    
    # 调用 LLM
    print("🤖 生成答案...")
    answer = llm_client.ask(prompt["system"], prompt["user"])
    
    # 输出结果
    print(f"\n💡 答案：\n{answer}")
    
    print(f"\n📎 参考来源：")
    for i, r in enumerate(retrieved, 1):
        sim = 1 - r["distance"]
        src = r["metadata"]["source"]
        cid = r["metadata"]["chunk_id"]
        print(f"   [{i}] 《{src}》第 {cid} 块 (相似度: {sim:.4f})")


def main():
    print("=" * 60)
    print("📚 智能文档问答系统 v1.0（语义检索版）")
    print("=" * 60)
    print()
    
    # 确保 docs/ 目录存在
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        print(f"📁 已创建 {DOCS_DIR}/ 文件夹")
        print("   请放入文档后重新运行程序")
        return
    
    # 初始化组件
    embed_client = EmbeddingClient()
    vector_store = VectorStore(persist_path=CHROMA_PATH)
    llm_client = LLMClient()
    
    # 询问是否强制重建
    if vector_store.count() > 0:
        print(f"📊 向量库已有 {vector_store.count()} 个文本块")
        choice = input("   是否强制重建向量库？(y/N): ").strip().lower()
        force_reload = (choice == "y")
    else:
        force_reload = False
    
    # 加载文档
    load_documents(vector_store, embed_client, force_reload=force_reload)
    
    total = vector_store.count()
    if total == 0:
        print("\n⚠️ 向量库为空，请先放入文档")
        return
    
    print(f"\n📊 向量库总计: {total} 个文本块")
    print("\n💬 可以开始提问了（输入 q 退出）\n")
    
    # 问答循环
    while True:
        try:
            question = input("❓ 你的问题: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 再见")
            break
        
        if question.lower() in ("q", "quit", "exit"):
            print("👋 再见")
            break
        
        if not question:
            continue
        
        try:
            answer_question(vector_store, embed_client, llm_client, question)
        except Exception as e:
            print(f"\n❌ 出错了: {e}")
        
        print()


if __name__ == "__main__":
    main()