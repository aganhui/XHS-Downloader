# XHS-Downloader 技术文档

本文档详细说明 XHS-Downloader 子项目的技术架构、实现细节和 API 接口，用于 AI 辅助代码修改和项目维护。

## 目录

1. [项目概述](#项目概述)
2. [技术栈](#技术栈)
3. [项目结构](#项目结构)
4. [核心功能模块](#核心功能模块)
5. [API 接口文档](#api-接口文档)
6. [配置说明](#配置说明)
7. [部署指南](#部署指南)
8. [与主项目的关系](#与主项目的关系)

## 项目概述

XHS-Downloader 是一个小红书作品采集工具，提供以下功能：

- **作品信息采集**：提取小红书作品的详细信息（标题、内容、作者、统计数据等）
- **作品搜索**：根据关键词搜索小红书作品
- **作品下载**：下载小红书无水印图片和视频（可选功能）
- **API 服务**：提供 HTTP API 接口供其他项目调用
- **MCP 服务**：提供 Model Context Protocol 接口（可选）

本项目作为 xhs-spread 主项目的子项目，为主项目提供小红书笔记采集服务。

## 技术栈

### 核心
- **语言**：Python 3.12
- **Web 框架**：FastAPI
- **HTTP 客户端**：httpx
- **HTML 解析**：lxml
- **异步支持**：asyncio, aiofiles

### 依赖管理
- **包管理**：uv（推荐）或 pip
- **虚拟环境**：venv 或 uv venv

### 部署
- **平台**：Vercel（通过 `api/app.py`）
- **容器化**：Docker（支持）
- **服务器模式**：FastAPI + Uvicorn

## 项目结构

```
XHS-Downloader/
├── api/                      # Vercel API 路由（用于部署到 Vercel）
│   ├── app.py                # FastAPI 应用入口（Vercel 部署）
│   ├── search.js              # 搜索接口（Vercel Serverless）
│   └── logs.js                # 日志接口（Vercel Serverless）
├── source/                    # 核心源代码
│   ├── application/          # 应用层
│   │   ├── app.py             # FastAPI 应用主文件
│   │   ├── request.py         # HTTP 请求封装
│   │   ├── download.py        # 文件下载逻辑
│   │   ├── explore.py         # 探索页面处理
│   │   ├── image.py           # 图片处理
│   │   ├── video.py           # 视频处理
│   │   └── request_logger.py  # 请求日志记录
│   ├── module/                # 核心模块
│   │   ├── model.py           # 数据模型
│   │   ├── settings.py        # 配置管理
│   │   ├── manager.py         # 管理器类
│   │   ├── tools.py           # 工具函数
│   │   └── ...
│   ├── expansion/             # 扩展功能
│   │   ├── browser.py         # 浏览器相关
│   │   ├── xhs_search.py     # 搜索功能
│   │   └── ...
│   ├── CLI/                   # 命令行接口
│   ├── TUI/                   # 终端用户界面
│   └── translation/           # 国际化
├── static/                    # 静态资源
├── locale/                     # 国际化文件
├── main.py                     # 主程序入口（CLI/TUI/API/MCP 模式）
├── example.py                  # 使用示例
├── test_search.py              # 搜索测试
├── requirements.txt           # Python 依赖（pip）
├── pyproject.toml              # 项目配置（uv）
├── Dockerfile                  # Docker 镜像构建文件
├── vercel.json                 # Vercel 部署配置
└── README.md                   # 用户文档
```

## 核心功能模块

### 1. 应用层 (`source/application/`)

#### app.py
FastAPI 应用主文件，定义 API 路由和生命周期管理。

**主要路由**：
- `POST /xhs/detail`: 获取作品详情
- `POST /xhs/search`: 搜索作品
- `GET /docs`: API 文档（Swagger UI）
- `GET /redoc`: API 文档（ReDoc）

**生命周期**：
- Startup: 初始化 XHS 实例
- Shutdown: 清理资源

#### request.py
HTTP 请求封装，处理小红书 API 调用。

**主要功能**：
- 请求头管理（User-Agent、Cookie 等）
- 请求重试机制
- 错误处理
- 响应解析

#### download.py
文件下载逻辑（可选功能）。

**主要功能**：
- 图片下载
- 视频下载
- 断点续传
- 文件完整性校验

### 2. 核心模块 (`source/module/`)

#### model.py
数据模型定义。

**主要模型**：
- `XHSNote`: 笔记数据模型
- `XHSSearchResult`: 搜索结果模型

#### settings.py
配置管理。

**配置来源**：
1. 环境变量（优先级最高）
2. `Volume/settings.json` 配置文件
3. 代码默认值

**主要配置项**：
- `cookie`: 小红书 Cookie
- `proxy`: 代理地址
- `timeout`: 请求超时时间
- `work_path`: 工作路径
- `user_agent`: User-Agent 字符串

#### manager.py
核心管理器类 `XHS`。

**主要方法**：
- `extract(url, download=False)`: 提取作品信息
- `search(keyword)`: 搜索作品
- `setup_routes(app)`: 设置 FastAPI 路由

### 3. 扩展功能 (`source/expansion/`)

#### xhs_search.py
搜索功能实现。

**主要功能**：
- 关键词搜索
- 结果解析
- 分页处理

#### browser.py
浏览器相关功能（Cookie 读取等）。

## API 接口文档

### POST /xhs/detail

获取小红书作品详细信息。

#### 请求参数

```json
{
  "url": "https://www.xiaohongshu.com/explore/xxx?xsec_token=xxx",  // 必需：作品链接
  "download": false,                                                // 可选：是否下载文件
  "index": [1, 2, 3],                                               // 可选：下载指定序号的图片（仅图文作品）
  "cookie": "xxx",                                                   // 可选：Cookie（覆盖配置）
  "proxy": "http://127.0.0.1:10808",                               // 可选：代理（覆盖配置）
  "skip": false                                                      // 可选：是否跳过已下载作品
}
```

#### 响应格式

**成功响应** (200):
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "note_id": "作品ID",
    "title": "作品标题",
    "desc": "作品描述",
    "type": "normal",  // 作品类型：normal（图文）、video（视频）
    "user": {
      "user_id": "作者ID",
      "nickname": "作者昵称"
    },
    "time": "发布时间",
    "last_update_time": "最后更新时间",
    "image_list": [  // 图片列表（图文作品）
      {
        "url": "图片URL",
        "width": 1080,
        "height": 1440
      }
    ],
    "video": {  // 视频信息（视频作品）
      "media": {
        "stream": {
          "h264": [
            {
              "master_url": "视频URL",
              "width": 1080,
              "height": 1920
            }
          ]
        }
      }
    },
    "tag_list": [  // 标签列表
      {
        "name": "标签名"
      }
    ],
    "interact_info": {  // 互动数据
      "liked_count": 1000,
      "collected_count": 500,
      "comment_count": 200,
      "share_count": 100
    }
  }
}
```

**错误响应** (400/500):
```json
{
  "code": 1,
  "msg": "错误信息",
  "data": null
}
```

#### 使用示例

```python
import requests

response = requests.post(
    "http://127.0.0.1:5556/xhs/detail",
    json={
        "url": "https://www.xiaohongshu.com/explore/xxx?xsec_token=xxx",
        "download": False
    },
    timeout=10
)
data = response.json()
```

### POST /xhs/search

搜索小红书作品。

#### 请求参数

```json
{
  "keyword": "搜索关键词",        // 必需：搜索关键词
  "page": 1,                      // 可选：页码（默认 1）
  "page_size": 20,                // 可选：每页数量（默认 20）
  "cookie": "xxx",                // 可选：Cookie（覆盖配置）
  "proxy": "http://127.0.0.1:10808"  // 可选：代理（覆盖配置）
}
```

#### 响应格式

**成功响应** (200):
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "items": [  // 作品列表
      {
        "note_id": "作品ID",
        "note_url": "作品URL",
        "title": "作品标题",
        "desc": "作品描述",
        "user": {
          "user_id": "作者ID",
          "nickname": "作者昵称"
        },
        "cover": {
          "url": "封面图URL"
        },
        "interact_info": {
          "liked_count": 1000,
          "collected_count": 500,
          "comment_count": 200,
          "share_count": 100
        }
      }
    ],
    "has_more": true,  // 是否有更多结果
    "cursor": "下一页游标"
  }
}
```

**错误响应** (400/500):
```json
{
  "code": 1,
  "msg": "错误信息",
  "data": null
}
```

#### 使用示例

```python
import requests

response = requests.post(
    "http://127.0.0.1:5556/xhs/search",
    json={
        "keyword": "探店",
        "page": 1,
        "page_size": 20
    },
    timeout=10
)
data = response.json()
```

## 配置说明

### 环境变量

#### Vercel 部署配置

- `XHS_WORK_PATH`: 工作路径（Vercel 环境默认：`/tmp/xhs_downloader`）
- `XHS_VOLUME`: Volume 路径（Vercel 环境默认：`/tmp/xhs_downloader_volume`）
- `XHS_COOKIE`: 小红书 Cookie（可选）
- `XHS_PROXY`: 代理地址（可选）

#### 运行时配置

配置文件路径：`Volume/settings.json`（首次运行自动生成）

**主要配置项**：
- `cookie`: 小红书 Cookie
- `proxy`: 代理地址
- `timeout`: 请求超时时间（秒）
- `work_path`: 工作路径
- `user_agent`: User-Agent 字符串
- `max_retry`: 最大重试次数

### Cookie 配置

Cookie 用于提高请求成功率和获取更多数据。获取方式：

1. 打开浏览器（可选无痕模式）
2. 访问 `https://www.xiaohongshu.com/explore`
3. 登录小红书账号（可选）
4. 打开开发者工具（F12）
5. 在 Network 选项卡中查找请求
6. 复制 Cookie 值

**注意**：Cookie 不是必需的，但建议配置以提高稳定性。

## 部署指南

### Vercel 部署

1. **准备代码**
   - 确保 `api/app.py` 存在
   - 确保 `vercel.json` 配置正确

2. **配置环境变量**
   - 在 Vercel 控制台设置环境变量：
     - `XHS_COOKIE`（可选）
     - `XHS_PROXY`（可选）

3. **部署**
   - 连接 GitHub 仓库
   - 自动部署或手动触发

### Docker 部署

1. **构建镜像**
   ```bash
   docker build -t xhs-downloader .
   ```

2. **运行容器（API 模式）**
   ```bash
   docker run -d \
     --name xhs-downloader \
     -p 5556:5556 \
     -v xhs_volume:/app/Volume \
     -e XHS_COOKIE="your_cookie" \
     xhs-downloader \
     python main.py api
   ```

3. **访问 API**
   - API 文档：`http://localhost:5556/docs`
   - API 接口：`http://localhost:5556/xhs/detail`

### 本地开发

1. **安装依赖**
   ```bash
   # 使用 uv（推荐）
   uv venv
   uv sync

   # 或使用 pip
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **运行 API 服务**
   ```bash
   # 使用 uv
   uv run main.py api

   # 或使用 Python
   python main.py api
   ```

3. **访问 API**
   - API 文档：`http://127.0.0.1:5556/docs`
   - API 接口：`http://127.0.0.1:5556/xhs/detail`

## 与主项目的关系

### 服务提供者

XHS-Downloader 作为 xhs-spread 主项目的子项目，为主项目提供以下服务：

1. **笔记详情采集**：主项目通过 `/xhs/detail` 接口获取小红书笔记的详细信息
2. **笔记搜索**：主项目通过 `/xhs/search` 接口搜索相关笔记作为参考

### 调用关系

```
xhs-spread 主项目
    ↓
src/lib/xhs-notes.ts
    ↓
HTTP POST 请求
    ↓
XHS-Downloader API
    ├── POST /xhs/detail  (获取笔记详情)
    └── POST /xhs/search  (搜索笔记)
```

### 数据流

1. **用户添加参考笔记**
   - 用户在主项目界面输入小红书笔记 URL
   - 主项目调用 `fetchXhsNoteByUrl(url)`
   - 主项目向 XHS-Downloader 发送 POST 请求到 `/xhs/detail`
   - XHS-Downloader 采集数据并返回
   - 主项目保存到数据库

2. **搜索参考笔记**
   - 用户在主项目界面搜索关键词
   - 主项目调用 `searchXhsNotes(keyword)`
   - 主项目向 XHS-Downloader 发送 POST 请求到 `/xhs/search`
   - XHS-Downloader 返回搜索结果
   - 主项目展示结果供用户选择

### 配置关联

主项目通过环境变量配置子项目地址：

- `XHS_SERVICE_BASE`: XHS-Downloader 服务地址
  - 默认：`https://xhs-downloader-nine.vercel.app`
  - 开发环境：`http://localhost:5556`
- `XHS_FETCH_TIMEOUT_MS`: 请求超时时间（默认：9000ms）
- `XHS_COOKIE`: 可选的小红书 Cookie（传递给子项目）
- `XHS_PROXY`: 可选的代理地址（传递给子项目）

### 独立部署

- XHS-Downloader 可以独立部署和更新，不影响主项目
- 主项目通过 HTTP API 调用，不直接依赖子项目代码
- 子项目可以服务多个主项目实例

### 版本兼容性

- 子项目 API 接口保持向后兼容
- 主项目通过环境变量指定子项目地址，可以灵活切换版本
- 建议在主项目和子项目之间建立版本管理机制

---

**最后更新**：2025-01-XX
**维护者**：项目团队
**文档版本**：1.0
