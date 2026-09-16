# 📚 智能文档问答系统 v0.2
  
> 一个基于关键词检索 + LLM 的本地文档问答系统

---

## ✨ 功能特性

- 📄 **多格式支持**：TXT / PDF / DOCX
- 🔍 **关键词检索**：自动提取问题关键词，匹配相关段落
- 🤖 **AI 问答**：基于 DeepSeek LLM 生成精准答案
- 📎 **来源可追溯**：答案下方标注参考段落，确保信息可靠
- 💬 **交互式 CLI**：加载一次文档，持续提问

---

## 📅 学习日志

### Day 1: 完成多格式文档读取器封装
- ✅ 封装 `read_document()` 统一接口，自动根据后缀名分发读取逻辑
- ✅ 支持 TXT / PDF / DOCX 三种格式
- ✅ 底层函数（`_read_txt_file`, `_read_pdf_file`, `_read_docx_file`）返回纯净内容，无成功提示混入
- ✅ 统一异常处理：`read_document()` 返回 `"错误：..."` 字符串，调用方只需判断 `startswith("错误")`
- ✅ 修复 PDF `extract_text()` 返回 `None` 导致的 `TypeError`
- 🛠️ 工具：Python 3.11 + PyPDF2 + python-docx

### Day 2: 字符串处理与正则表达式
- ✅ 封装 `extract_phones()` / `extract_emails()` / `extract_contacts()`
- ✅ 支持提取手机号（13812345678、138-1234-5678 等格式）
- ✅ 支持提取邮箱（含多级域名如 xxx@team.org.cn）
- ✅ 与 Day 1 文档读取器联动，实现"读取→提取"完整流程
- 🛠️ 工具：Python re 模块

### Day 3: 关键词检索 + LLM 文档问答
- ✅ 封装 `search_paragraphs()` 实现 Top-K 关键词检索
- ✅ 支持 jieba 中文分词 / 无 jieba 滑窗回退
- ✅ 实现 `doc_qa()` 完整流程：读取 → 检索 → 构造 Prompt → LLM 生成答案
- ✅ 测试覆盖：保修期、退换货、人为损坏判定、客服联系方式
- 🛠️ 工具：jieba + requests + DeepSeek API

### Day 4: 交互式命令行 + 模块化重构
- ✅ 封装 `core/` 模块：document_reader / keyword_search / llm_client
- ✅ 实现 `app.py` 交互式 CLI：加载文档 → 循环提问 → 标注来源 → 优雅退出
- ✅ LLM 答案末尾要求标注 `[来源X]`，确保信息可追溯
- ✅ 支持相对路径、支持 q/quit/exit 多种退出方式
- 🛠️ 架构：读取 → 检索 → Prompt 构造 → LLM 生成 → 来源标注

## ⚠️ 已知限制（v0.2）
- 使用关键词检索，可能召回语义相关但字面不完全匹配的段落
- Week 5 将升级 Embedding 语义检索，解决此问题

---

## 🚀 快速开始

**环境要求**：Python 3.9+

### 1. 克隆仓库

```bash
git clone https://github.com/Minos-star/Document-Reader.git
cd Document-Reader
```

### 2. 安装依赖

```bash
pip install PyPDF2 python-docx
pip install requests jieba
pip install -r requirements.txt
```

### 3. 配置 API Key

# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-你的Key"

# Mac/Linux
export DEEPSEEK_API_KEY="sk-你的Key"

### 4. 放入文档

把要查询的文档放入 docs/ 文件夹（支持 .txt / .pdf / .docx）

### 5. 运行

python app.py
```

---

## 📸 使用示例

📚 智能文档问答系统 v0.2（多文档版）
==================================================
⏳ 正在扫描 docs/ ...
   📄 保修政策.txt ... ✅ 6 段
   📄 产品手册.pdf ... ✅ 12 段
✅ 共加载 18 个段落，可以开始提问

💬 输入问题开始问答（q 退出）
--------------------------------------------------

❓ 你的问题：保修期多久？
🤖 正在思考...

💡 答案：
根据文档内容，整机保修期为1年，主要部件保修期为3年。

📎 参考来源：
   [1] 《保修政策.txt》 第一条 保修期限 本产品整机保修期为1年...
   [2] 《保修政策.txt》 第二条 主要部件保修 主板、显示屏、电池等主要部件...
--------------------------------------------------

---

## 🏗️ 技术架构

用户提问
    ↓
关键词提取（jieba / 停用词过滤）
    ↓
段落匹配（Top-K 关键词命中）
    ↓
构造 RAG Prompt（上下文 + 问题）
    ↓
DeepSeek LLM 生成答案
    ↓
输出答案 + 参考来源