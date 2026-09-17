"""
test_recursive.py - 对比测试：固定分块 vs 递归分块
"""
import os
from core.chunker import chunk_text, chunk_text_recursive
from core.document_reader import read_document

END_PUNCT = "。！？；.!?;：:"

def count_broken(chunks):
    """统计结尾被截断的块数量"""
    broken = 0
    for text, _ in chunks:
        if text and text[-1] not in END_PUNCT:
            broken += 1
    return broken

def main():
    filepath = "./docs/常见问题.txt"
    text = read_document(filepath)

    # 固定分块
    fixed = chunk_text(text, chunk_size=500, overlap=50)
    # 递归分块
    recur = chunk_text_recursive(text, max_size=500, overlap=50)

    print("=" * 60)
    print("对比结果")
    print("=" * 60)
    print(f"{'指标':<20}{'固定分块':<15}{'递归分块'}")
    print("-" * 60)
    print(f"{'块数量':<20}{len(fixed):<15}{len(recur)}")
    print(f"{'被截断的块':<20}{count_broken(fixed):<15}{count_broken(recur)}")
    print("-" * 60)

    # 打印递归分块前 3 个块的结尾，验证停在完整句子处
    print("\n递归分块前 3 个块的结尾：")
    for text, cid in recur[:3]:
        print(f"\n【Chunk {cid}】({len(text)} 字)")
        print(f"  ...{text[-40:]}")

if __name__ == "__main__":
    main()