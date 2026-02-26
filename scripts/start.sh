#!/bin/bash

# yt-dlp API 启动脚本

set -e

echo "================================"
echo "启动 yt-dlp API 服务"
echo "================================"
echo ""

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "警告: 未找到 .env 配置文件"
    if [ -f ".env.example" ]; then
        echo "正在从 .env.example 创建 .env..."
        cp .env.example .env
    else
        echo "错误: 未找到 .env.example 文件"
        exit 1
    fi
fi

dos2unix .env

# 读取配置（使用 set -a 自动导出变量）
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo "✓ 已加载配置文件"
fi

# 显示关键配置
echo "配置信息："
echo "  - 数据库类型: ${DATABASE_TYPE:-sqlite}"
echo "  - 应用端口: ${APP_PORT:-8000}"
echo "  - 下载路径: ${DEFAULT_DOWNLOAD_PATH:-./downloads}"
echo "  - 日志级别: ${LOG_LEVEL:-INFO}"
echo ""

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    echo "✓ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
. venv/bin/activate

# 安装/更新依赖
echo "检查依赖..."
pip install -q -r requirements.txt
echo "✓ 依赖检查完成"
echo ""

# 创建必要的目录
mkdir -p logs
mkdir -p "${DEFAULT_DOWNLOAD_PATH:-./downloads}"

# 启动应用
echo "启动服务..."
echo "访问地址: http://${APP_HOST:-0.0.0.0}:${APP_PORT:-8000}"
echo "API 文档: http://localhost:${APP_PORT:-8000}/docs"
echo ""

# 使用配置文件中的端口启动
# 3. 安装依赖（确保 uvicorn 已安装）
pip install uvicorn

# 4. 运行应用
# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "项目根目录: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# 从项目根目录运行，使用 app.main:app
uvicorn app.main:app --host ${APP_HOST:-0.0.0.0} --port ${APP_PORT:-8000}

