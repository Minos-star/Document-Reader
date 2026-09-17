"""
inspect_chunks.py - 观察固定分块是否切断句子
"""
import os
from core.chunker import chunk_text
from core.document_reader import read_document

DOCS_DIR = "./docs"

# 标点符号集合（用于判断句子是否在块边界被截断）
END_PUNCT = "。！？；.!?;：:"

def main():
    # 找一份真实文档来实验
    filepath = None
    for filename in sorted(os.listdir(DOCS_DIR)):
        if filename.endswith(".txt"):
            filepath = os.path.join(DOCS_DIR, filename)
            break
    
    if not filepath:
        print("docs/ 里没找到 txt 文档，改一下代码挑一份 pdf/docx")
        return
    
    print(f"📄 实验文档：{filepath}\n")
    text = read_document(filepath)
    
    # 用你现有的固定分块函数
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    print(f"共切出 {len(chunks)} 个 chunk\n")
    print("=" * 60)
    
    broken = 0  # 统计被截断的块
    for chunk_text_content, chunk_id in chunks:
        if chunk_id >= 5:   # 只看前 5 个块就够了
            break
        
        tail = chunk_text_content[-30:]   # 块的结尾 30 字
        last_char = chunk_text_content[-1]  # 结尾最后一个字符
        
        is_broken = last_char not in END_PUNCT
        
        print(f"\n【Chunk {chunk_id}】 长度: {len(chunk_text_content)} 字")
        print(f"  结尾: ...{tail}")
        if is_broken:
            broken += 1
            print(f"  ⚠️  句子在结尾被切断！(最后字符是 '{last_char}')")
        else:
            print(f"  ✅ 结尾是完整句子")
    
    print("\n" + "=" * 60)
    print(f"前 5 个块中，被截断的有 {broken} 个")

if __name__ == "__main__":
    main()