# PM Copilot 服务器部署完整步骤

面向「从 GitHub 拉取代码，在一台 Windows 机器上跑起来，让其他设备通过公网访问」的完整部署指南。

## 目录

1. [环境准备（Python / Node.js / VC++）](#一环境准备)
2. [拉取代码](#二拉取代码)
3. [后端部署（依赖 + .env + 建索引 + 启动）](#三后端部署)
4. [前端部署（依赖 + 启动）](#四前端部署)
5. [公网访问](#五公网访问)
6. [验证](#六验证)
7. [常见坑](#七常见坑)

---

## 一、环境准备

### 1. 安装 Python 3.12（⚠️ 必须 3.12，不要 3.13）

- 打开 <https://www.python.org/downloads/>，下载 Python 3.12（Windows 64 位安装包 `Windows installer (64-bit)`）。
- 双击安装，**务必勾选**底部「Add python.exe to PATH」。
- 装完重新开一个 cmd，验证：

```bash
py -3.12 --version
```

> ⚠️ **为什么不用 3.13**：chromadb 底层的原生扩展（hnswlib）在 Python 3.13 上会崩溃（内存访问冲突）。

### 2. 安装 Node.js（LTS 版）

- 打开 <https://nodejs.org>，下载 **LTS 版** `.msi` 安装包，双击安装（默认下一步即可）。
- 装完重新开一个 cmd，验证：

```bash
node -v
npm -v
```

### 3. 安装 Visual C++ 运行库（⚠️ 不装会崩溃）

- 下载微软官方 x64 版：<https://aka.ms/vs/17/release/vc_redist.x64.exe>
- 双击安装，一路下一步。
- 顺手也装 x86 版：<https://aka.ms/vs/17/release/vc_redist.x86.exe>

> ⚠️ **不装的话**，chromadb 调向量库时会报「python 已停止工作」（崩溃模块 `MSVCP140.dll`，异常 `c0000005`）。

---

## 二、拉取代码

```bash
git clone https://github.com/Chenchangge/PM-copilot-AIagent-.git pm-copilot
cd pm-copilot
```

> 说明：仓库里**只包含代码 + `knowledge/` 数据**。以下目录已被 `.gitignore` 忽略、不在仓库里，本地运行时自动生成，无需手动清理：
>
> - `frontend/node_modules/`
> - `backend/.venv/`
> - 所有 `__pycache__/`
> - `backend/data/chroma/`（向量库，运行时重新构建）

---

## 三、后端部署

### 1. 创建虚拟环境

```bash
cd pm-copilot\backend
py -3.12 -m venv .venv
.venv\Scripts\activate
```

### 2. 安装依赖（用清华源，否则可能超时）

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> `requirements.txt` 里 chromadb 已锁定 `>=0.5,<1.0`，会自动装 0.5.x（1.x 在 Windows 上查询向量会崩溃）。

### 3. 配置 `.env`（⚠️ 在项目根目录，不是 backend 里）

在 `pm-copilot/` 根目录新建 `.env`，内容如下。**⚠️ 必须把两个 API Key 填成真实、可用的 Key**（这是服务器默认模型，访客直接用，不用自己配 Key）：

```env
ENVIRONMENT=production

# 服务器默认文本生成模型（模拟面试 / 知识问答 / 面试评价都用它）
DEFAULT_LLM_PROVIDER=deepseek
DEFAULT_LLM_BASE_URL=https://api.deepseek.com
DEFAULT_LLM_MODEL=deepseek-flash
DEFAULT_LLM_API_KEY=sk-你的DeepSeek-Key

# 服务器默认 Embedding 模型（知识问答的向量检索）
DEFAULT_EMBEDDING_PROVIDER=custom
DEFAULT_EMBEDDING_BASE_URL=https://你的embedding端点
DEFAULT_EMBEDDING_MODEL=text-embedding-v4
DEFAULT_EMBEDDING_API_KEY=sk-你的embedding-Key
```

字段说明：

| 字段 | 作用 | 示例 |
| --- | --- | --- |
| `DEFAULT_LLM_*` | 文本生成模型（面试 / 问答 / 评价都用它） | deepseek |
| `DEFAULT_LLM_MODEL` | DeepSeek 模型名，`deepseek-flash` 或 `deepseek-v4-pro` | deepseek-flash |
| `DEFAULT_LLM_API_KEY` | **必填**：文本生成模型的真实 Key | sk-你的DeepSeek-Key |
| `DEFAULT_EMBEDDING_*` | 知识问答的向量检索模型 | custom / text-embedding-v4 |
| `DEFAULT_EMBEDDING_BASE_URL` | OpenAI 兼容 `/embeddings` 端点 | 如 `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `DEFAULT_EMBEDDING_API_KEY` | **必填**：Embedding 模型的真实 Key | sk-你的embedding-Key |

> ⚠️ **两个 API Key 必须填真实值**：`DEFAULT_LLM_API_KEY` 和 `DEFAULT_EMBEDDING_API_KEY` 是「服务器默认模型」，留空 = 不启用，访客进「模拟面试 / 知识问答 / 面试评价」会因为没有可用模型而报错。
>
> ⚠️ **`.env` 一定要纯英文**（或用记事本「另存为 → 编码选 UTF-8」），否则后端读它时报 `UnicodeDecodeError`。

### 4. 构建知识库向量索引

```bash
cd pm-copilot\backend
.venv\Scripts\activate
python -m app.scripts.build_knowledge_index
```

看到 `失败: 0` 就是成功（约 50 秒，会联网调 Embedding API 给 226 篇文档嵌入向量）。

> ⚠️ 这一步**必须**在配好 `DEFAULT_EMBEDDING_*` 之后做。

### 5. 启动后端

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8010
```

看到 `Uvicorn running on http://0.0.0.0:8010` 即成功。

---

## 四、前端部署

另开一个命令行窗口：

```bash
cd pm-copilot\frontend
npm install
npm run dev
```

看到 `Network: http://你的IP:5173` 即成功。

> `vite.config.js` 里已经配好了 `host: true`（监听 0.0.0.0）和 `allowedHosts: true`（允许内网穿透域名），所以**不用带 `--host`**，直接 `npm run dev` 就行。

---

## 五、公网访问（别人能访问）

这台机器如果是内网（家庭宽带 / 联通 NAT，`ipconfig` 显示 `10.x / 172.x / 192.168.x`），公网 IP 是运营商 NAT，别人无法直接 IP 访问，要用内网穿透：

- **cpolar**（免费、随机域名）：注册 cpolar.com → 下载客户端 → `cpolar authtoken 你的token` → `cpolar http 5173`，得到 `http://xxxx.cpolar.cn`。
- **花生壳**（免费、固定域名）：注册 oray.com → 实名 → 客户端「内网穿透 → 新增映射」，HTTP 映射，内网 `127.0.0.1:5173`。

如果是真正的云服务器（阿里云 / 腾讯云），直接放行安全组 5173 端口 + Windows 防火墙，访问 `http://公网IP:5173`。

---

## 六、验证

用无痕浏览器 / 另一台手机访问公网地址：

1. 页面能打开 ✅
2. 直接进「模拟面试」→ 能出题（用的是服务器默认 DeepSeek 模型）✅
3. 「知识问答」随便问一句 → 能检索 + 回答（用的是默认 Embedding + DeepSeek）✅

三个都能用，就说明服务器配置完成，任何设备访问都能直接用，**不需要访客再配 API**。

---

## 七、常见坑

| 症状 | 原因 | 解决 |
| --- | --- | --- |
| 装 Python 3.13 后 chromadb 崩溃 | hnswlib 不兼容 3.13 | 用 Python 3.12 |
| chromadb 报「python 已停止工作」（`MSVCP140.dll` / `c0000005`） | 没装 VC++ 运行库 | 装 x64 + x86 的 vc_redist |
| 后端读 `.env` 报 `UnicodeDecodeError` | `.env` 里有中文 / 非 UTF-8 编码 | 纯英文，或另存为 UTF-8 |
| chromadb 1.x 在 Windows 查向量崩溃 | 1.x 兼容性问题 | 锁定 0.5.x（`requirements.txt` 已锁 `>=0.5,<1.0`） |
| `pip install` 超时 | 默认源连不上 | 用清华源 `-i https://pypi.tuna.tsinghua.edu.cn/simple` |
| 建索引报 `embedding_model_not_found` | 没配 `DEFAULT_EMBEDDING_*` | 先配好 Embedding 模型再建索引 |
| 访客进「模拟面试」报无可用模型 | `DEFAULT_LLM_API_KEY` 留空 | 填真实 DeepSeek Key |
