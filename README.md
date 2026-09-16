# 📚 智能文档问答系统 v1.0（语义检索版）

&gt; 基于 Embedding + ChromaDB 向量数据库的本地文档语义问答系统

## ✨ 功能特性

- 📄 **多格式支持**：TXT / PDF / DOCX
- 🧠 **语义检索**：基于通义千问 Embedding，理解问题意图而非关键词匹配
- 🗄️ **向量数据库**：ChromaDB 持久化存储，支持增量加载
- 🤖 **AI 问答**：DeepSeek LLM 生成精准答案，严格基于文档内容
- 📎 **来源可追溯**：答案标注 [来源X]，显示相似度分数
- 📂 **多文档管理**：自动扫描 docs/ 文件夹，新文档自动入库

## 🏗️ 技术架构

用户提问
    ↓
Embedding（通义千问 qwen3.7-text-embedding）
    ↓
向量检索（ChromaDB cosine 相似度，Top-K）
    ↓
构造 RAG Prompt（上下文 + 约束 + 问题）
    ↓
DeepSeek LLM 生成答案
    ↓
输出答案 + 参考来源 + 相似度分数

## 🚀 快速开始

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
$env:DASHSCOPE_API_KEY="sk-你的Key"

# Mac/Linux
export DEEPSEEK_API_KEY="sk-你的Key"
export DASHSCOPE_API_KEY="sk-你的Key"

### 4. 放入文档

把要查询的文档放入 docs/ 文件夹（支持 .txt / .pdf / .docx）

### 5. 运行

python app.py