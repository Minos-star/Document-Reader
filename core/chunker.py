"""
core/chunker.py - 文档分块模块
"""
import re


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


def chunk_text_recursive(text: str, max_size: int = 500, overlap: int = 50) -> list:
    """
    按自然边界递归分块，最后贪心合并，相邻块保留 overlap 字符的重叠。

    处理流程：
      1. _split_recursive 内部先生成"自然单元"（段落 → 句子 → 硬切），
         然后贪心合并相邻单元，直到装不下 max_size 为止
      2. 对合并后的相邻块加上 overlap（前一块尾巴拼到后一块前面）

    Args:
        text: 原始文本字符串
        max_size: 每块最大字符数（默认500）
        overlap: 相邻块之间的重叠字符数（默认50）

    Returns:
        list: [(chunk_text, chunk_id), ...]  分块结果列表
    """
    # 边界处理：空文本或非法参数直接返回空列表
    if not text or max_size <= 0:
        return []
    if overlap < 0:
        overlap = 0

    # 第一步：递归生成 + 贪心合并，每块 <= max_size
    units = _split_recursive(text, max_size)
    if not units:
        return []

    # 第二步：在合并后的块之间加上 overlap（前一块尾巴拼到后一块前面）
    chunks = []
    chunk_id = 0
    for i, unit in enumerate(units):
        if i == 0 or overlap == 0:
            # 第一块或不要求 overlap 时，原样输出
            effective = unit
        else:
            prev = units[i - 1]
            # 取上一块末尾 overlap 个字符作为重叠区
            # 如果上一块本身不够 overlap 长，就整块都拼过去
            tail = prev[-overlap:] if len(prev) >= overlap else prev
            effective = tail + unit

        effective = effective.strip()
        if effective:
            chunks.append((effective, chunk_id))
            chunk_id += 1

    return chunks


def _split_recursive(text: str, max_size: int) -> list:
    """
    两步切分：
      1. 生成"自然单元"：段落 ≤ max_size 保持原样；
         段落超长 → 降级到句子级切分；
         单句超长 → 降级到字符硬切。
         结束时每个单元都满足 len(unit) <= max_size。
      2. 贪心合并：从左到右把相邻单元拼进 buffer，
         只要 len(buffer) + len(下一个单元) <= max_size 就继续拼；
         装不下就把 buffer 作为一个块输出，从下一个单元开始新 buffer。
    """
    text = text.strip()
    if not text:
        return []

    # === 第一步：生成自然单元（段落 → 句子 → 硬切）===
    units = []
    # 优先级 1：按空行（≥1 个空行）切段落，\s* 兼容行间空白行
    for para in re.split(r'\n\s*\n+', text):
        para = para.strip()
        if not para:
            continue
        if len(para) <= max_size:
            # 段落长度在限制内 → 直接作为一个单元（不降级）
            units.append(para)
        else:
            # 段落超长 → 降级到句子级切分
            units.extend(_split_by_sentences(para, max_size))

    if not units:
        return []

    # === 第二步：贪心合并相邻单元 ===
    # 用 "\n\n" 连接 buf 和 unit，保留段落边界可见；
    # 初始 buf 不加 "\n\n"；分隔符本身算进长度判断，保证合并后单块仍 <= max_size
    SEP = "\n\n"
    chunks = []
    buf = units[0]
    for unit in units[1:]:
        if len(buf) + len(SEP) + len(unit) <= max_size:
            # 还能装下，继续往 buffer 里拼（用 "\n\n" 隔开）
            buf = buf + SEP + unit
        else:
            # 装不下了，把 buffer 输出成块，从当前 unit 开始新 buffer
            chunks.append(buf)
            buf = unit
    chunks.append(buf)   # 别忘了最后一段 buffer

    return chunks


def _split_by_sentences(text: str, max_size: int) -> list:
    """按句子终止符（。！？!?）切分；单句过长再降级到字符硬切。"""
    # 用捕获组拆分，保留分隔符；返回 [text, delim, text, delim, ...]
    parts = re.split(r'([。！？!?\.]+)', text)

    # 把终止符拼回到它前面的文本，组成完整句子
    sentences = []
    buf = ''
    for p in parts:
        if p and re.fullmatch(r'[。！？!?\.]+', p):
            buf += p   # 把终止符接回去
            sentences.append(buf)
            buf = ''
        else:
            buf += p
    if buf.strip():
        sentences.append(buf)

    # 对每个句子再判断长度
    units = []
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        if len(sent) <= max_size:
            units.append(sent)
        else:
            # 单句超长 → 最后一级降级，按字符硬切
            units.extend(_hard_cut(sent, max_size))

    return units


def _hard_cut(text: str, max_size: int) -> list:
    """按字符硬切（最后保底方案，不保证语义）。"""
    return [text[i:i + max_size] for i in range(0, len(text), max_size)]


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
    # 🔧 修复：以脚本自身所在目录为基准定位 docs/，不再受 CWD 影响
    # "../docs" 实际是相对 CWD 的，从项目根跑会指向 W6/docs 而不是本项目的 docs/
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.normpath(os.path.join(_SCRIPT_DIR, "..", "docs"))
    
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