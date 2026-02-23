# MySQL数据库初始化脚本

# 创建数据库
CREATE DATABASE IF NOT EXISTS yt_dlp_api CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 使用数据库
USE yt_dlp_api;

# 创建用户（可选）
# CREATE USER IF NOT EXISTS 'yt_dlp_user'@'%' IDENTIFIED BY 'your_password';
# GRANT ALL PRIVILEGES ON yt_dlp_api.* TO 'yt_dlp_user'@'%';
# FLUSH PRIVILEGES;

# 注意：表结构会由SQLAlchemy自动创建，无需手动创建
