# yt-dlp API 服务

> **快速开始：** `docker run -p 8000:8000 hipc/yt-dlp` 立即开始使用！

[English](README.md) | [中文](README_CN.md)

这是一个基于 FastAPI 和 yt-dlp 构建的 RESTful API 服务，提供视频下载和任务管理功能。

## 功能特点

- 异步下载处理
- 支持多种视频格式
- 任务状态持久化存储（支持 SQLite 和 MySQL）
- 结构化日志系统
- 配置化管理
- RESTful API 设计

## 技术栈

- **FastAPI** - 现代化的 Web 框架
- **yt-dlp** - 视频下载核心库
- **SQLAlchemy** - ORM 框架
- **MySQL/SQLite** - 数据库支持
- **Loguru** - 结构化日志
- **Pydantic Settings** - 配置管理

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

复制配置文件模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件配置数据库连接：

```env
# 使用 SQLite（默认）
DATABASE_TYPE=sqlite

# 或使用 MySQL
DATABASE_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=yt_dlp_api
```

如果使用 MySQL，需要先创建数据库：

```bash
mysql -u root -p < init_mysql.sql
```

### 3. 启动服务器

```bash
python main.py
```

服务器将在 http://localhost:8000 启动

## API 接口文档

### 1. 提交下载任务

**请求：**
```http
POST /download
```

**请求体：**
```json
{
    "url": "视频URL",
    "output_path": "./downloads",  // 可选，默认从配置读取
    "format": "bestvideo+bestaudio/best",  // 可选，默认为最佳质量
    "quiet": false  // 可选，是否静默下载
}
```

**返回：**
```json
{
    "status": "success",
    "task_id": "任务ID"
}
```

### 2. 批量提交下载任务

**请求：**
```http
POST /batch_download
```

**请求体：**
```json
{
    "tasks": [
        {
            "url": "视频URL1",
            "output_path": "./downloads",
            "format": "best"
        },
        {
            "url": "视频URL2",
            "output_path": "./downloads",
            "format": "best"
        }
    ]
}
```

**返回：**
```json
{
    "status": "success",
    "task_ids": ["任务ID1", "任务ID2"]
}
```

### 3. 获取任务状态

**请求：**
```http
GET /task/{task_id}
```

**返回：**
```json
{
    "status": "success",
    "data": {
        "id": "任务ID",
        "url": "视频URL",
        "status": "pending/completed/failed",
        "result": {},  // 当任务完成时包含下载信息
        "error": "错误信息"  // 当任务失败时包含
    }
}
```

### 4. 获取所有任务列表

**请求：**
```http
GET /tasks
```

**返回：**
```json
{
    "status": "success",
    "data": [
        {
            "id": "任务ID",
            "url": "视频URL",
            "status": "任务状态",
            "output_path": "输出路径",
            "format": "格式"
        }
    ]
}
```

## 配置说明

所有配置通过 `.env` 文件管理：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_TYPE` | 数据库类型（sqlite/mysql） | sqlite |
| `MYSQL_HOST` | MySQL 主机地址 | localhost |
| `MYSQL_PORT` | MySQL 端口 | 3306 |
| `MYSQL_USER` | MySQL 用户名 | root |
| `MYSQL_PASSWORD` | MySQL 密码 | - |
| `MYSQL_DATABASE` | MySQL 数据库名 | yt_dlp_api |
| `APP_HOST` | 应用监听地址 | 0.0.0.0 |
| `APP_PORT` | 应用监听端口 | 8000 |
| `DEFAULT_DOWNLOAD_PATH` | 默认下载路径 | ./downloads |
| `THREAD_POOL_SIZE` | 线程池大小 | 10 |
| `LOG_LEVEL` | 日志级别 | INFO |
| `LOG_FORMAT` | 日志格式（json/text） | json |
| `LOG_FILE` | 日志文件路径 | logs/app.log |

## 日志系统

项目使用 Loguru 实现结构化日志：

- **控制台输出**：彩色文本格式，便于开发调试
- **文件输出**：JSON 格式，便于日志分析
- **自动轮转**：日志文件达到 100MB 自动切分
- **自动清理**：保留最近 30 天的日志
- **错误日志**：ERROR 级别单独记录到 `*_error.log`

日志文件位置：`logs/app.log`

## 错误处理

所有 API 接口在发生错误时会返回适当的 HTTP 状态码和详细的错误信息：

- **404**: 资源未找到
- **400**: 请求参数错误
- **500**: 服务器内部错误

## 数据持久化

服务支持两种数据库：

### SQLite（默认）
- 无需额外配置
- 适合小规模部署
- 数据库文件：`tasks.db`

### MySQL
- 适合生产环境
- 支持高并发
- 需要预先创建数据库

任务信息包括：
- 任务 ID（UUID）
- 视频 URL
- 输出路径
- 下载格式
- 任务状态（pending/completed/failed）
- 下载结果（JSON）
- 错误信息
- 时间戳

## Docker 支持

项目提供了 Dockerfile，可以通过以下命令构建和运行容器：

```bash
# 构建镜像
docker build -t yt-dlp-api .

# 运行容器（使用 SQLite）
docker run -p 8000:8000 -v $(pwd)/downloads:/app/downloads yt-dlp-api

# 运行容器（使用 MySQL）
docker run -p 8000:8000 \
  -e DATABASE_TYPE=mysql \
  -e MYSQL_HOST=host.docker.internal \
  -e MYSQL_PASSWORD=your_password \
  -v $(pwd)/downloads:/app/downloads \
  yt-dlp-api
```

## 在线文档

启动服务后，可以访问自动生成的 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 项目结构

```
.
├── config.py           # 配置管理
├── logger.py           # 日志系统
├── database.py         # 数据库模型
├── task_manager.py     # 任务管理
├── downloader.py       # 下载器
├── api_router.py       # API 路由
├── main.py            # 应用入口
├── requirements.txt   # 依赖列表
├── .env.example       # 配置模板
├── init_mysql.sql     # MySQL 初始化脚本
└── Dockerfile         # Docker 配置
```

## 注意事项

1. 请确保有足够的磁盘空间存储下载的视频
2. 建议在生产环境中配置适当的安全措施（认证、HTTPS 等）
3. 遵守视频平台的使用条款和版权规定
4. MySQL 数据库建议使用 utf8mb4 字符集
5. 日志文件会自动轮转和压缩，注意定期清理

## 开发指南

查看 [CLAUDE.md](CLAUDE.md) 了解项目架构和开发指南。

查看 [TODO.md](TODO.md) 了解待优化项和改进计划。

## 许可证

本项目采用 MIT 许可证。
