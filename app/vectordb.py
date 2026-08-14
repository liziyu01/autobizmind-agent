"""
向量数据库模块

基于 ChromaDB 实现文档的向量化存储和检索
"""
import os
import logging
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_core.documents import Document

from app.config import config

logger = logging.getLogger(__name__)

# 持久化目录
PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

# ============================================================
# 1. 初始化 Embedding 模型
# ============================================================
embeddings = OpenAIEmbeddings(
    model="embedding-3",
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL
)

# ============================================================
# 2. 获取/创建向量数据库实例
# ============================================================
def get_vector_store(collection_name: str = "knowledge_base") -> Chroma:
    """
        获取或创建 Chroma 向量数据库实例。
    """
    # 确认持久化目录
    os.makedirs(PERSIST_DIR, exist_ok=True)

    # 创建 Chroma 实例
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR
    )

# ============================================================
# 3. 文档加载（支持 PDF / Word / TXT）
# ============================================================
def load_document(file_path: str) -> List[Document]:
    """
        根据文件扩展名加载文档。
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在：{file_path}")

    # 获取文件后缀
    ext = os.path.splitext(file_path)[1].lower()

    # 文件类型匹配 Loader
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
    elif ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError(f"不支持的文件格式：{ext}")

    docs = loader.load()

    logger.info(f"✅ 加载文档: {file_path}, {len(docs)} 页/段")

    return docs

# ============================================================
# 4. 文档切片
# ============================================================
def split_documents(
documents: List[Document],
        chunk_size: int =500,
        chunk_overlap: int = 50
) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )

    chunks = text_splitter.split_documents(documents)
    logger.info(f"✂️ 共切分为 {len(chunks)} 个片段")
    return chunks

# ============================================================
# 5. 添加文档到知识库
# ============================================================
def add_document(file_path: str, collection_name: str = "knowledge_base") -> int:
    """
        加载文档 → 切片 → 向量化 → 存入 Chroma。
    """
    docs = load_document(file_path)
    chunks = split_documents(docs)

    if not chunks:
        logger.warning("文档切片为空，跳过存储")
        return 0

    vector_store = get_vector_store(collection_name)
    vector_store.add_documents(chunks)

    logger.info(f"💾 已存入 {len(chunks)} 个片段到知识库")
    return len(chunks)

# ============================================================
# 6. 检索相关文档
# ============================================================
def search_documents(
        query: str,
        collection_name: str = "knowledge_base",
        top_k: int = 3
) -> List[Document]:
    """
        根据用户问题，从知识库中检索最相关的文档片段。
    """
    vector_store = get_vector_store(collection_name)
    results = vector_store.similarity_search(query, k=top_k)

    logger.info(f"🔍 检索到 {len(results)} 个相关片段")

    return results

# ============================================================
# 7. 清空知识库
# ============================================================
def clear_knowledge_base(collection_name: str = "knowledge_base") -> None:
    """清空指定的知识库集合"""
    vector_store = get_vector_store(collection_name)

    vector_store.delete_collection()
    logger.info(f"🗑️ 已清空知识库: {collection_name}")

# ============================================================
# 8. 获取知识库统计信息
# ============================================================
def get_kb_stats(collection_name: str = "knowledge_base") -> dict:
    """获取知识库的统计信息"""
    vector_store = get_vector_store(collection_name)
    try:
        count = vector_store._collection.count()
    except Exception:
        count = 0

    return {
        "collection_name": collection_name,
        "document_count": count,
        "persist_dir": PERSIST_DIR,
    }