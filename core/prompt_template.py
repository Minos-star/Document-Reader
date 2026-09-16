"""
core/prompt_template.py - RAG 系统的 Prompt 模板
"""

RAG_SYSTEM_PROMPT = """你是一位专业的企业文档问答助手。你的任务是基于提供的参考文档，准确、简洁地回答用户问题。

【回答规则】
1. 必须严格基于<context>中的参考信息回答，不要引入外部知识
2. 如果参考信息不足以回答问题，明确说："根据现有文档，无法找到相关信息。"
3. 回答要简洁专业，直接给出答案，不要重复问题
4. 在答案末尾，用 [来源X] 格式标注信息来源

【来源标注格式】
- 每条参考信息前面有 [来源1] [来源2] ... 标记
- 答案中引用了哪条信息，就标注对应的 [来源X]
- 如果综合多条信息，标注所有相关来源"""

RAG_USER_TEMPLATE = """【参考信息】
<context>
{context}
</context>

【用户问题】
{question}

请基于上述参考信息回答问题。"""


def build_rag_prompt(retrieved_chunks: list, question: str) -> dict:
    """
    构造 RAG 系统的完整 Prompt
    
    Args:
        retrieved_chunks: ChromaDB 检索返回的列表，每项包含：
            - document: 文本内容
            - metadata: {"source": "文件名", "chunk_id": 0}
            - distance: 距离值（用于计算相似度）
        question: 用户原始问题
    
    Returns:
        dict: {"system": system_prompt, "user": user_prompt}
    """
    
    # 构建上下文：给每段文本加上 [来源X] 标记
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        source = chunk["metadata"]["source"]
        text = chunk["document"]
        context_parts.append(f"[来源{i}] 《{source}》\n{text}")
    
    context = "\n\n".join(context_parts)
    
    return {
        "system": RAG_SYSTEM_PROMPT,
        "user": RAG_USER_TEMPLATE.format(context=context, question=question)
    }


# ========== 测试代码 ==========
if __name__ == "__main__":
    # 模拟检索结果（和 chroma_demo.py 的输出格式一致）
    mock_chunks = [
        {
            "document": "产品出现非人为故障，请携带发票到指定维修点免费维修。",
            "metadata": {"source": "保修政策.txt", "chunk_id": 5},
            "distance": 0.3631
        },
        {
            "document": "软件问题可通过官网下载补丁自行解决，不涉及硬件保修。",
            "metadata": {"source": "技术文档.pdf", "chunk_id": 6},
            "distance": 0.3729
        },
        {
            "document": "本产品整机保修期为1年，自购买之日起计算。",
            "metadata": {"source": "保修政策.txt", "chunk_id": 0},
            "distance": 0.3834
        }
    ]
    
    question = "电脑坏了怎么保修"
    prompt = build_rag_prompt(mock_chunks, question)
    
    print("=" * 60)
    print("【System Prompt】")
    print("=" * 60)
    print(prompt["system"])
    print("\n" + "=" * 60)
    print("【User Prompt】")
    print("=" * 60)
    print(prompt["user"])