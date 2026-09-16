"""
core/vector_store.py - ChromaDB 向量数据库封装
"""

import chromadb


class VectorStore:
    """ChromaDB 向量存储封装"""
    
    def __init__(self, persist_path="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_chunks(self, chunks_data: list, embeddings: list):
        """
        批量添加文本块到向量库
        
        Args:
            chunks_data: [{"id": str, "text": str, "metadata": dict}, ...]
            embeddings: [[float, ...], ...]
        """
        if not chunks_data or not embeddings:
            return
        
        ids = [c["id"] for c in chunks_data]
        documents = [c["text"] for c in chunks_data]
        metadatas = [c["metadata"] for c in chunks_data]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
    
    def query(self, embedding: list, n_results: int = 3):
        """
        向量相似度检索
        """
        return self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
    
    def get_existing_ids(self) -> set:
        """获取已入库的所有 chunk ID"""
        try:
            result = self.collection.get()
            return set(result["ids"]) if result["ids"] else set()
        except Exception:
            return set()
    
    def count(self) -> int:
        """返回向量库中的 chunk 总数"""
        return self.collection.count()
    
    def reset(self):
        """清空向量库"""
        try:
            self.client.delete_collection("documents")
        except Exception:
            pass
        
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )