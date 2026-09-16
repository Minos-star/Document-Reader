"""
core/chunker.py - 文档分块模块
"""

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    将长文本按固定长度分块，相邻块之间保留重叠区域
    
    Args:
        text: 原始文本字符串
        chunk_size: 每块最大字符数（默认500）
        overlap: 相邻块之间的重叠字符数（默认50）
    
    Returns:
        list: [(chunk_text, chunk_id), ...]  分块结果列表
    """
    if not text or chunk_size <= 0:
        return []
    
    chunks = []
    chunk_id = 0
    start = 0
    text_length = len(text)
    
    while start < text_length:
        # 计算当前块的结束位置
        end = start + chunk_size
        
        # 截取文本块
        chunk = text[start:end]
        
        # 清理：去掉首尾空白，但保留中间的空行（段落分隔）
        chunk = chunk.strip()
        
        if chunk:  # 只保留非空块
            chunks.append((chunk, chunk_id))
            chunk_id += 1
        
        # 下一块的起始位置 = 当前结束位置 - 重叠区
        # 如果剩余文本不足一个完整块，直接结束
        if end >= text_length:
            break
            
        start = end - overlap
    
    return chunks


def chunk_document(file_path: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    读取文档并自动分块（配合 document_reader.py 使用）
    """
    # 🔧 修复：同级目录直接导入
    from document_reader import read_document
    
    text = read_document(file_path)
    
    if text.startswith("错误"):
        print(f"⚠️ 读取失败: {file_path} - {text}")
        return []
    
    chunks = chunk_text(text, chunk_size, overlap)
    
    source_name = file_path.split("/")[-1].split("\\")[-1]
    result = []
    for chunk_text_content, chunk_id in chunks:
        result.append({
            "text": chunk_text_content,
            "chunk_id": chunk_id,
            "source": source_name
        })
    
    return result


# ========== 测试代码 ==========
if __name__ == "__main__":
    # 测试1和测试2保持原样...
    
    # 测试3：真实文档分块
    print("\n" + "=" * 60)
    print("测试3：真实文档分块")
    print("=" * 60)
    
    import os
    # 🔧 修复：从 core/ 的父目录（项目根目录）找 docs/
    docs_dir = "../docs"  # 相对 core/ 目录，docs 在上一级
    
    if os.path.exists(docs_dir):
        for filename in os.listdir(docs_dir):
            if filename.endswith((".txt", ".pdf", ".docx")):
                filepath = os.path.join(docs_dir, filename)
                doc_chunks = chunk_document(filepath, chunk_size=500, overlap=50)
                print(f"\n📄 {filename}: {len(doc_chunks)} 个 chunk")
                for c in doc_chunks[:2]:
                    print(f"   [Chunk {c['chunk_id']}] {len(c['text'])} 字 | {c['text'][:40]}...")
    else:
        print("docs/ 文件夹不存在，跳过真实文档测试")
        print("提示：在项目根目录创建 docs/ 文件夹，放入测试文档")