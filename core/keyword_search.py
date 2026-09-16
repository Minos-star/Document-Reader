"""
简单的关键词检索系统（Keyword Retrieval）

思路：
    1. 把长文本切成段落（优先按空行；连续文本会按句号切）
    2. 从问题中提取"关键词"（装了 jieba 走 jieba，没装走空格+滑窗回退）
    3. 对每个段落统计其包含关键词的总次数（命中分）
    4. 按分数降序取前 top_k 个段落
"""

import re
import logging

# ---------- 中文分词（可选依赖）----------
# 用 jieba 做中文分词；没装也能跑，只是中文检索粒度会差一些。
try:
    import jieba
    HAS_JIEBA = True
    # 屏蔽 jieba 初始化时刷屏的 DEBUG 日志。
    # jieba 没有 setLogLevel，要走标准 logging。
    logging.getLogger("jieba").setLevel(logging.ERROR)
except ImportError:
    HAS_JIEBA = False


# ---------- 停用词表（简单版）----------
# 这些词太常见，对检索贡献不大，提到时把它们过滤掉。
STOPWORDS = {
    # English
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "can", "this", "that", "these",
    "those", "i", "you", "he", "she", "it", "we", "they", "what",
    "which", "who", "when", "where", "why", "how", "to", "of", "in",
    "on", "for", "with", "at", "by", "from", "as", "into", "about",
    # Chinese
    "的", "了", "是", "在", "和", "与", "或", "也", "都", "就", "要",
    "有", "没", "什么", "怎么", "为什么", "哪个", "哪", "如何", "吗",
    "呢", "吧", "啊", "哦", "这", "那", "我", "你", "他", "她", "它",
    "我们", "你们", "他们", "一个", "一些", "上", "下", "里", "外",
    "去", "来", "到", "把", "被", "让",
}


# ---------- 关键词提取（两条路径：装了 jieba / 没装 jieba）----------
# 思路：用 jieba 就只用 jieba（顺便去重，中英文都交给它处理）；
#       没装 jieba 时退回"英文按空格 + 中文滑窗 2-5 字"，避免中英文混走两套逻辑再 dedup。


def _is_good_keyword(tok: str) -> bool:
    """通用过滤：长度 >= 2 且不在停用词表里。"""
    return bool(tok) and len(tok) >= 2 and tok not in STOPWORDS


def _extract_keywords_with_jieba(question: str):
    """装有 jieba 时的关键词提取（中英文都交给 jieba，flat 流式去重）。"""
    keywords, seen = [], set()
    for tok in jieba.cut(question):
        # 只保留字母数字和中文，过滤标点和空白
        tok = re.sub(r"[^\w\u4e00-\u9fff]", "", tok).strip().lower()
        if tok and _is_good_keyword(tok) and tok not in seen:
            keywords.append(tok)
            seen.add(tok)
    return keywords


def _extract_keywords_without_jieba(question: str):
    """没装 jieba 时的回退：英文按空格，中文用 2-5 字滑窗。"""
    keywords, seen = [], set()

    # 1) 英文 / 数字：按空格拆
    cleaned = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", question)
    for tok in cleaned.split():
        tok = tok.lower()
        if _is_good_keyword(tok) and tok not in seen:
            keywords.append(tok)
            seen.add(tok)

    # 2) 中文：从原文里滑窗切 2-5 字子串
    #    （jieba 不可用时这是最朴素的可用的办法。
    #    显然会抓到 "的的"/"国首" 这种假词，所以靠停用词 + dedup 过滤一下。）
    n = len(question)
    for i in range(n):
        for j in range(i + 2, min(i + 6, n + 1)):
            sub = question[i:j]
            if not re.fullmatch(r"[\u4e00-\u9fff]{2,5}", sub):
                continue
            if sub in STOPWORDS or sub in seen:
                continue
            keywords.append(sub)
            seen.add(sub)

    return keywords


def extract_keywords(question: str):
    """从问题里挑出关键词（去停用词 / 去标点 / 去单字）。"""
    if HAS_JIEBA:
        return _extract_keywords_with_jieba(question)
    return _extract_keywords_without_jieba(question)


# ---------- 段落切分（带"连续文本"回退）----------
# 优先按空行切（最贴近手工排版）；
# 若整篇没有空行、且单段过长，则按句末标点切分，
# 用来兜底 PDF 抽取 / 复制粘贴后"全文一坨"的情况。


def split_paragraphs(text: str, min_len: int = 200) -> list:
    """
    切分段落。

    Args:
        text:     待切分的长文本
        min_len:  触发回退切分的段落长度阈值（默认 200 字符）

    Returns:
        段落列表（已 strip）。
    """
    # 1) 优先按空行切（\n\n / \r\n\r\n 都能处理）
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    # 2) 回退：只分出 1 段且长度超过阈值，按句末标点切
    if len(paras) == 1 and len(paras[0]) > min_len:
        # 在句末标点后面切（lookbehind 保留标点本身的字符）
        pieces = re.split(r"(?<=[.!?。！？])\s*", paras[0])
        paras = [p.strip() for p in pieces if p.strip()]

    return paras


def search_paragraphs(text: str, question: str, top_k: int = 3):
    """
    在长文本里找出与问题最相关的 top_k 个段落。

    Args:
        text:     长文本。优先按空行分段；无空行的连续文本会按句号切分。
        question: 提问字符串（中文/英文都行）
        top_k:    返回的段落数量，默认 3

    Returns:
        相关段落列表，按相关度从高到低排列。零命中时返回空列表。
    """
    # ---- 1) 切段（带回退） ----
    paragraphs = split_paragraphs(text)
    if not paragraphs:
        return []

    # ---- 2) 提关键词 ----
    keywords = extract_keywords(question)
    if not keywords:
        # 没有有效关键词时不做检索，返回前 top_k 段
        return paragraphs[:top_k]

    # ---- 3) 打分 ----
    # 分数 = 段落里所有关键词出现次数的总和（不区分大小写）
    scored = []
    for idx, para in enumerate(paragraphs):
        p = para.lower()
        score = sum(p.count(kw) for kw in keywords)
        scored.append((score, idx, para))

    # ---- 4) 排序：分数高的优先；同分时保留原文顺序（稳定）----
    scored.sort(key=lambda x: (-x[0], x[1]))

    # ---- 5) 取前 top_k 个真正命中的段落 ----
    return [para for score, _, para in scored if score > 0][:top_k]


# ==================== 自测 ====================
if __name__ == "__main__":
    # ---- 英文示例 ----
    en_text = """\
Paris is the capital and most populous city of France, with an estimated population of 2.16 million. Since the 17th century, Paris has been one of the world's major centres of finance, diplomacy, fashion, and science.

Tokyo is the capital of Japan and the largest metropolitan area in the world. It sits at the head of Tokyo Bay. After the Meiji Restoration, Tokyo rapidly became a major Asian hub for finance and culture.

New York City comprises five boroughs where the Hudson River meets the Atlantic Ocean. The Empire State Building defines its iconic skyline.

London, capital of England and the United Kingdom, is a 21st-century city with history stretching back to Roman times."""

    for q in ["What is the capital of Japan?",
              "Which city is the capital of France?"]:
        print(f"\n问题: {q}")
        for i, p in enumerate(search_paragraphs(en_text, q, top_k=3), 1):
            print(f"  [{i}] {p[:60]}...")

    # ---- 中文示例（依赖 jieba）----
    if HAS_JIEBA:
        cn_text = """\
巴黎是法国的首都和最大城市，常住人口约 220 万。
自 17 世纪以来，巴黎一直是全球金融、外交、时尚和科学中心之一。

东京是日本的首都，也是全球最大的都市圈。东京湾畔是这座城市的核心区域。
明治维新之后，东京迅速发展成为亚洲重要的文化与经济中心。

纽约由五个区组成，地处哈德逊河汇入大西洋之处。帝国大厦是它的地标。

伦敦是英国的首都，拥有从罗马时代延续至今的悠久历史。"""

        cn_q = "日本的首都叫什么？"
        print(f"\n问题: {cn_q}")
        for i, p in enumerate(search_paragraphs(cn_text, cn_q, top_k=3), 1):
            print(f"  [{i}] {p[:60]}...")
    else:
        print("\n(未安装 jieba，跳过中文示例。可运行: pip install jieba)")

    # ---- 回退测试：连续无空行（模拟 PDF 抽取）----
    no_blanks = (
        "Paris is the capital of France and its largest city. "
        "It has been a global center for art, fashion, and science for centuries. "
        "Tokyo is the capital of Japan and the world's largest metropolitan area. "
        "It sits on Tokyo Bay and grew rapidly after the Meiji Restoration. "
        "New York City sits where the Hudson River meets the Atlantic Ocean. "
        "London is the capital of England and has Roman-era roots."
    )
    print("\n问题 (no-blanks 回退): What is the capital of Japan?")
    for i, p in enumerate(
        search_paragraphs(no_blanks, "What is the capital of Japan?", top_k=3), 1
    ):
        print(f"  [{i}] {p}")
