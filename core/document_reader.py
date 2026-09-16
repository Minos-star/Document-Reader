from PyPDF2 import PdfReader
from docx import Document
import os


# ============================================================
# 内部实现（私有函数，供 read_document 调用）
# 对外请使用 read_document()
# ============================================================

def _read_txt_file(file_path: str, encoding: str = "utf-8") -> str:
    """读取一个 TXT 文件并将其内容作为字符串返回。"""
    with open(file_path, "r", encoding=encoding) as f:
        return f.read()


def _read_pdf_file(file_path: str, password: str = "") -> str:
    """使用 PyPDF2 读取 PDF 文件（文本型），返回所有页面的纯文本。"""
    reader = PdfReader(file_path)

    if reader.is_encrypted:
        if not password:
            raise PermissionError("PDF 已加密，请提供 password 参数。")
        result = reader.decrypt(password)
        if result == 0:
            raise PermissionError("密码错误，无法解密 PDF。")

    text_parts = []
    for page_num, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text()
        except Exception as e:
            page_text = f"[第 {page_num} 页解析失败：{e}]"
        # 关键修复：extract_text() 可能返回 None（例如空白页或图片页），
        # 直接 join(None) 会抛 TypeError，统一转为空字符串。
        text_parts.append(page_text or "")

    return "\n\n".join(text_parts)


def _read_docx_file(file_path: str) -> str:
    """使用 python-docx 读取 Word 文档（.docx），返回所有段落纯文本。"""
    doc = Document(file_path)
    paragraphs = [para.text for para in doc.paragraphs]
    return "\n".join(paragraphs)


# ============================================================
# 公共入口
# ============================================================

def read_document(file_path: str, password: str = "") -> str:
    """
    统一的文档读取入口。自动根据文件后缀名判断类型，
    调用对应的内部函数，返回纯文本字符串。

    支持的格式:
        .txt  -> _read_txt_file()
        .pdf  -> _read_pdf_file()
        .docx -> _read_docx_file()

    参数:
        file_path (str): 文件路径。
        password (str): 仅 PDF 可能用到，默认空字符串。

    返回:
        str: 成功时为文档内容；失败时为 "错误：..." 开头的字符串。
             调用方只需判断 text.startswith("错误") 即可区分成功/失败。
    """
    if not os.path.exists(file_path):
        return f"错误：找不到文件 '{file_path}'，请检查路径是否正确。"

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    try:
        if ext == ".txt":
            return _read_txt_file(file_path)
        elif ext == ".pdf":
            return _read_pdf_file(file_path, password=password)
        elif ext == ".docx":
            return _read_docx_file(file_path)
        else:
            return (f"错误：不支持的文件格式 '{ext}'。"
                    f"目前仅支持 .txt / .pdf / .docx。")
    except Exception as e:
        return f"错误：读取 '{file_path}' 时发生异常：{e}"


# ============================================================
# 测试入口
# ============================================================
if __name__ == "__main__":
    # ---- 准备测试文件 ----
    test_dir = os.path.dirname(os.path.abspath(__file__))
    sample_txt  = os.path.join(test_dir, "sample.txt")
    sample_pdf  = os.path.join(test_dir, "sample.pdf")    # 请手动放入同目录
    sample_docx = os.path.join(test_dir, "sample.docx")    # 请手动放入同目录

    # 自动创建测试用的 TXT（结尾带换行符用于测试边界情况）
    with open(sample_txt, "w", encoding="utf-8") as f:
        f.write("这是第一行。\n这是第二行。\n这是第三行。\n")

    # ---- 逐一测试 ----
    test_cases = [
        (sample_txt,  "TXT（自动创建）"),
        (sample_pdf,  "PDF（需手动放入同目录）"),
        (sample_docx, "DOCX（需手动放入同目录）"),
        (os.path.join(test_dir, "sample.jpg"),          "不支持的格式"),
        (os.path.join(test_dir, "not_exist.txt"),        "不存在的文件"),
    ]

    for path, label in test_cases:
        print("\n" + "=" * 55)
        print(f"[{label}] {os.path.basename(path)}")
        print("=" * 55)

        text = read_document(path)

        if text.startswith("错误"):
            print(text)
            print("^ 读取失败")
        else:
            # 成功时打印文件信息和内容预览
            basename = os.path.basename(path)
            ext = os.path.splitext(basename)[1].lower()
            if ext == ".txt":
                # 边界情况：如果文件以 \n 结尾，count('\n')+1 会多算一行
                # （因为 \n 之后还有一个"空行"），这里用 rstrip 后再计数更准确
                lines = text.rstrip("\n").count("\n") + 1 if text.strip() else 0
                print(f"✓ 共 {lines} 行")
            elif ext == ".pdf":
                print(f"✓ 读取成功，内容长度 {len(text)} 字符")
            elif ext == ".docx":
                lines = text.rstrip("\n").count("\n") + 1 if text.strip() else 0
                print(f"✓ 共 {lines} 个段落")
            print("内容预览：")
            print(text[:300] + ("..." if len(text) > 300 else ""))
