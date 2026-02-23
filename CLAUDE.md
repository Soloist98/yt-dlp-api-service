# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RESTful API service built with FastAPI that wraps yt-dlp for video downloading and information retrieval. The service provides asynchronous download processing with persistent task tracking using SQLAlchemy ORM, supporting both SQLite and MySQL databases.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Configure database (copy and edit .env file)
cp .env.example .env

# Run the development server
python main.py
# Server starts at http://localhost:8000 (configurable via .env)

# Docker build and run
docker build -t yt-dlp-api .
docker run -p 8000:8000 -v $(pwd)/downloads:/app/downloads yt-dlp-api
```

## Configuration

The application uses environment variables for configuration. Key settings:

- **Database**: Supports SQLite (default) and MySQL
  - `DATABASE_TYPE`: sqlite or mysql
  - `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
  - `SQLITE_DB_FILE`: SQLite database file path
- **Application**: `APP_HOST`, `APP_PORT`
- **Downloads**: `DEFAULT_DOWNLOAD_PATH`, `MAX_CONCURRENT_DOWNLOADS`, `THREAD_POOL_SIZE`

See `.env.example` for all available configuration options.

## Architecture

The application follows a layered architecture with configuration management:

1. **Configuration Layer** (`config.py`): Centralized configuration using pydantic-settings
2. **Database Layer** (`database.py`): SQLAlchemy ORM models and connection management
3. **API Layer** (`api_router.py`): FastAPI router defining all REST endpoints
4. **Business Logic** (`downloader.py`): Thin wrapper around yt-dlp library
5. **Data Layer** (`task_manager.py`): Task persistence and state management

### Key Components

- **Configuration Management**: Uses pydantic-settings to load from environment variables and .env files
- **ORM Framework**: SQLAlchemy for database abstraction, supporting multiple database backends
- **Connection Pool**: Automatic database connection pooling with health checks
- **Task Management**: All download operations are tracked as tasks with unique IDs
- **Async Processing**: Downloads run asynchronously using a global ThreadPoolExecutor
- **Task Deduplication**: The system checks for existing tasks with the same URL, output path, and format before creating new ones
- **File Serving**: Completed downloads can be retrieved via the `/download/{task_id}/file` endpoint

### Database Schema

The `tasks` table stores:
- Task ID (UUID, primary key)
- Video URL
- Output path and format
- Status (pending/completed/failed) - indexed
- Result JSON (video metadata when completed)
- Error message (when failed)
- Timestamp - indexed

### Special Behaviors

- Configurable default download paths via `DEFAULT_DOWNLOAD_PATH`
- Special handling for certain video sites (e.g., pornhub URLs automatically get a subdirectory)
- Filename sanitization via `NormalizeString()` replaces special characters with underscores
- Global thread pool for efficient resource management

## API Endpoints

- `POST /download` - Submit single download task
- `POST /batch_download` - Submit multiple download tasks
- `GET /task/{task_id}` - Get task status
- `GET /tasks` - List all tasks

## Dependencies

- **FastAPI**: Web framework
- **yt-dlp**: Video download library (core functionality)
- **uvicorn**: ASGI server
- **pydantic**: Data validation
- **pydantic-settings**: Configuration management
- **SQLAlchemy**: ORM framework
- **pymysql**: MySQL database driver
- **loguru**: Structured logging
- **ffmpeg**: Required system dependency for video processing (installed in Docker image)

## Testing

The API documentation is auto-generated and available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Git Commit Convention

This project follows a specific commit message format:
```
[type]: <type> [description]:<description>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

Example: `[type]: feat [description]:添加清除表接口，去除内存缓存`

## Notes

- The project includes both English (README.md) and Chinese (README_CN.md) documentation
- A pre-built Docker image is available: `docker run -p 8000:8000 hipc/yt-dlp`
