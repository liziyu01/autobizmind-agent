# AutoBizMind - 自适应业务决策 Agent
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
---
> 基于 MCP 协议的 AI Agent 核心版 MVP

## 🎯 项目简介

AutoBizMind 是一个基于 LangGraph 构建的自适应业务决策 Agent，支持：
- 多轮对话记忆（Redis 滑动窗口）
- 知识库检索增强生成（RAG + ChromaDB）
- MCP 风格工具调用（7 个内置工具）
- 热加载（动态注册新工具）
- 电商场景业务决策（客户等级、报价核算）

## 🏗️ 项目架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AutoBizMind v0.1.0                                 │
│                         完整技术栈                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    前端层 (Streamlit)                                │   │
│  │         对话界面 · 模式切换 · 文档上传 · 工具可视化                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    API 层 (FastAPI)                                  │   │
│  │  /chat · /chat/rag · /chat/tool · /upload_doc · /tools/*            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   Agent 层 (LangGraph)                               │   │
│  │  普通 Agent · RAG Agent · 工具调用 Agent · 多轮循环                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│          ┌─────────────┬───────────┼───────────┬─────────────┐            │
│          ▼             ▼           ▼           ▼             ▼            │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────┐ │
│  │   Redis    │ │  ChromaDB  │ │   SQLite   │ │  工具注册   │ │  LLM    │ │
│  │  会话记忆   │ │  知识库    │ │  电商数据   │ │  热加载    │ │   API   │ │
│  │  滑动窗口   │ │  向量检索  │ │  关联查询   │ │  异常降级  │ │  智谱   │ │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └─────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       工具池 (7 个)                                  │   │
│  │  query_orders · http_request · calculator · text_stats              │   │
│  │  get_customer_tier · get_product_price · calculate_quote            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Redis 7.0+
- Docker（可选）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/liziyu01/autobizmind-agent.git
cd autobizmind

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Key

# 5. 启动 Redis
docker run -d --name redis-autobiz -p 6379:6379 redis:7.4-alpine

# 6. 初始化数据库
python data/init_db.py

# 7. 启动服务
python -m app.main

# 8. 启动前端（另一个终端）
streamlit run app_frontend.py

# 1. 克隆项目
git clone <your-repo-url>
cd autobizmind

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Key

# 5. 启动 Redis
docker run -d --name redis-autobiz -p 6379:6379 redis:7.4-alpine

# 6. 初始化数据库
python data/init_db.py

# 7. 启动服务
python -m app.main

# 8. 启动前端（另一个终端）
streamlit run app_frontend.py
```

### 访问地址
- 后端 API: http://localhost:8000/docs
- 前端界面: http://localhost:8501

## 🔌 API 接口

### 对话接口

| 方法 | 路径         | 说明               |
| :--- | :----------- | :----------------- |
| POST | `/chat`      | 普通对话（带记忆） |
| POST | `/chat/rag`  | RAG 增强对话       |
| POST | `/chat/tool` | 工具调用对话       |

### 工具管理接口

| 方法 | 路径              | 说明         |
| :--- | :---------------- | :----------- |
| GET  | `/tools`          | 列出所有工具 |
| GET  | `/tools/{name}`   | 获取工具详情 |
| POST | `/tools/call`     | 调用工具     |
| POST | `/tools/register` | 注册工具     |
| POST | `/tools/refresh`  | 刷新工具列表 |
| GET  | `/tools/version`  | 获取版本号   |
| GET  | `/tools/logs`     | 获取调用日志 |
| GET  | `/tools/stats`    | 获取统计信息 |

### 知识库接口

| 方法 | 路径          | 说明       |
| :--- | :------------ | :--------- |
| POST | `/upload_doc` | 上传文档   |
| GET  | `/kb/stats`   | 知识库统计 |
| POST | `/kb/search`  | 检索测试   |

### 会话接口

| 方法   | 路径                  | 说明     |
| :----- | :-------------------- | :------- |
| GET    | `/session/{id}/stats` | 会话统计 |
| DELETE | `/session/{id}`       | 清空会话 |

## 🛠️ 内置工具

| 工具名              | 类别 | 用途           |
| :------------------ | :--- | :------------- |
| `query_orders`      | 查询 | 订单列表查询   |
| `http_request`      | 网络 | HTTP 请求      |
| `calculator`        | 计算 | 数学表达式求值 |
| `text_stats`        | 分析 | 文本统计       |
| `get_customer_tier` | 电商 | 客户等级查询   |
| `get_product_price` | 电商 | 商品价格查询   |
| `calculate_quote`   | 电商 | 报价核算       |

## 🧪 测试

```bash
# Redis 测试
python test_redis.py

# Agent 测试
python test_agent.py

# 向量数据库测试
python test_vectordb.py

# 工具系统测试
python test_tools.py

# 工具调用 Agent 测试
python test_tool_agent.py

# 异常降级测试
python test_fallback.py

# 滑动窗口测试
python test_sliding_window.py

# 电商工具测试
python test_ecommerce_tools.py

# 报价工具测试
python test_quote.py

# 系统联调测试
python test_integration.py

# 端到端测试
python test_full_e2e.py
```

## 📁 项目结构
```
autobizmind/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口（所有接口）
│   ├── config.py            # 配置中心
│   ├── agent.py             # 普通 Agent（Week 1）
│   ├── tool_agent.py        # 工具调用 Agent（Week 2）
│   ├── schemas.py           # Pydantic 数据模型
│   ├── redis_client.py      # Redis 客户端
│   ├── session_manager.py   # 会话管理（滑动窗口）
│   ├── vectordb.py          # 向量数据库（ChromaDB）
│   ├── tool_registry.py     # 工具注册中心（含热加载）
│   ├── tool_logger.py       # 工具日志
│   └── tools/               # 工具包（7 个工具）
├── data/                    # 数据
│   ├── init_db.py           # 数据库初始化
│   └── ecommerce.db         # SQLite 数据库
├── chroma_db/               # ChromaDB 持久化
├── uploads/                 # 上传临时目录
├── .env / .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── app_frontend.py          # Streamlit 前端
├── test_*.py                # 测试脚本
└── .streamlit/              # Streamlit 配置
```
## 许可
MIT License

## 作者
[Li Hong] - [https://github.com/liziyu01]