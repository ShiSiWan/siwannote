# 🚀 SiWan_notes (siwannote)

> **轻量级、无数据库依赖的现代 Markdown 知识库与研习平台**  
> 纯物理文件存储 · 内置多模型 AI 助手 · 精细权限隔离 · 毫秒级全文检索

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.x-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

---

## 🌟 核心特性

- 📂 **纯文件存储 (Flat-File)**：零数据库依赖（无需 MySQL / MongoDB / SQLite），所有笔记与附件均为磁盘上的原始 `.md` 文件，天然支持 Git 版本控制与多端同步。
- 🤖 **多模型 AI 研习助手**：无缝对接 DeepSeek、OpenAI、SiliconFlow 及本地 Ollama，支持 4 维度学术提炼（主旨、架构、指标、价值）与多轮上下文研讨。
- 🛡️ **精细权限与安全隔离**：支持直接多选勾选对外开放文档，未公开内容在服务端严格返回 `403 Forbidden`；内置访客 IP 监控与一键拉黑拦截。
- 🔍 **毫秒级全文检索**：内置 Whoosh 高性能引擎，支持标题匹配、正文全文模糊搜索与 `#标签` 检索，高亮命中关键词。
- 💬 **学术交流讨论区**：提供文档专属交流互动版块，支持自定义学术昵称与多重敏感词/辱骂过滤。
- 🎨 **响应式与多主题**：基于 Vue 3 + Tailwind CSS，完美适配桌面与手机端，内置「亮色」、「暗黑」与「护眼绿」三大主题。

---

## ⚡ 快速上手

### 方式一：Docker Compose 一键启动（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/ShiSiWan/siwannote.git
cd siwannote

# 2. 启动服务
docker compose up -d --build
```

启动完成后，打开浏览器访问 **`http://localhost:8080`**  
* 默认管理员账号：`admin`
* 默认管理员密码：`admin123`（登录后可在设置中即时修改）

---

### 方式二：本地开发与运行

```bash
# 1. 安装后端依赖
pip install -r pyproject.toml
# 或直接安装核心依赖: pip install fastapi uvicorn whoosh pydantic python-multipart pyjwt

# 2. 编译前端（若需修改前端代码）
npm install
npm run build

# 3. 启动服务
python3 -m uvicorn main:app --app-dir server --host 0.0.0.0 --port 8090
```

访问地址：**`http://localhost:8090`**

---

## ⚙️ 核心配置说明

通过环境变量或根目录 `.env` 文件进行快速配置：

| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `SIWAN_PATH` | `./data` | 笔记与附件在宿主机上的存储路径 |
| `SIWAN_AUTH_TYPE` | `none` | 权限模式：`none`（访客只读公开文档 + 管理员登录） / `password` |
| `SIWAN_USERNAME` | `admin` | 管理员用户名 |
| `SIWAN_PASSWORD` | `admin123` | 管理员默认密码 |
| `SIWAN_PORT` | `8080` | 生产服务监听端口 |

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 授权开源。
