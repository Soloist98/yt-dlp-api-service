# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RESTful API service built with FastAPI that wraps yt-dlp for video downloading and task management. The service provides asynchronous download processing with persistent task tracking using SQLAlchemy ORM, supporting both SQLite and MySQL databases, with structured logging via Loguru.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Configure database (copy and edit .env file)
cp .env.example .env
vi .env  # Edit configuration

# Run the development server
python main.py
# Server starts at http://localhost:8000 (configurable via .env)

# Package for deployment
./package.sh
# Creates dist/yt-dlp-api_TIMESTAMP/ directory

# Deploy to production (Linux)
./scripts/start.sh      # Start service
./scripts/stop.sh       # Stop service
./scripts/restart.sh    # Restart service

# Install as systemd service
sudo ./scripts/install-service.sh
sudo systemctl status yt-dlp-api
```

## Configuration

All configuration is managed through `.env` file using pydantic-settings:

**Database:**
- `DATABASE_TYPE`: sqlite or mysql
- `MYSQL_*`: MySQL connection parameters
- `SITE_PATH_MAPPING`: JSON mapping for site-specific subdirectories (e.g., `{"pornhub": "adult"}`)

**Application:**
- `APP_HOST`, `APP_PORT`: Server binding
- `DEFAULT_DOWNLOAD_PATH`: Base download directory
- `THREAD_POOL_SIZE`: Global thread pool size for downloads

**Logging:**
- `LOG_LEVEL`: INFO, DEBUG, WARNING, ERROR
- `LOG_FORMAT`: json or text
- `LOG_FILE`, `LOG_ROTATION`, `LOG_RETENTION`: Log management

## Architecture

### Layered Structure

1. **Configuration Layer** (`config.py`)
   - Centralized settings using pydantic-settings
   - Environment variable and .env file support
   - `get_output_path_for_url()`: Dynamic path mapping based on URL

2. **Logging Layer** (`logger.py`)
   - Structured logging with Loguru
   - Dual output: console (colored text) + file (JSON)
   - Automatic rotation and compression

3. **Database Layer** (`database.py`)
   - SQLAlchemy ORM models
   - Connection pooling with health checks
   - Supports SQLite and MySQL

4. **Data Layer** (`task_manager.py`)
   - Task CRUD operations
   - `task_exists(url)`: Checks for duplicate tasks by URL only
   - Automatic video title extraction from download results

5. **Business Logic** (`downloader.py`)
   - Thin wrapper around yt-dlp
   - File naming: `%(title)s.%(ext)s` (no format prefix)

6. **API Layer** (`api_router.py`)
   - FastAPI router with 4 core endpoints
   - Global ThreadPoolExecutor for async downloads
   - Automatic retry logic for failed tasks

### Key Behaviors

**Task Deduplication:**
- Tasks are deduplicated by URL only (not by output_path or format)
- Completed tasks: Return existing task_id
- Failed tasks: Automatically reset to pending and retry
- Pending tasks: Return existing task_id (avoid duplicate downloads)

**Site-Specific Paths:**
- Configured via `SITE_PATH_MAPPING` in .env
- Example: URLs containing "pornhub" → downloadsub/
- Prevents hardcoded special cases

**Video Title Storage:**
- `video_title` field added to database
- Automatically extracted from yt-dlp results on completion
- Returned in API responses

**Structured Logging:**
- All operations logged with context (task_id, url, status)
- JSON format for production analysis
- Separate error log file

### Database Schema

```sql
tasks (
    id VARCHAR(36) PRIMARY KEY,
    url TEXT NOT NULL,              -- Indexed for deduplication (prefix index)
    video_title VARCHAR(500),       -- Extracted on completion
    output_path VARCHAR(500),
    format VARCHAR(100),
    status VARCHAR(20) NOT NULL,    -- Indexed: pending/completed/failed
    result TEXT,                    -- JSON metadata
    error TEXT,
    timestamp DATETIME NOT NULL     -- Indexed
)
```

## API Endpoints

- `POST /download` - Submit single download task
- `POST /batch_download` - Submit multiple download tasks
- `GET /task/{task_id}` - Get task status (includes video_title)
- `GET /tasks` - List all tasks

## Deployment

### Manual Deployment

```bash
# Package
./package.sh

# Copy to server
scp -r dist/yt-dlp-api_* user@server:/opt/

# On server
cd /opt/yt-dlp-api_*
cp .env.example .env
vi .env
./scripts/start.sh
```

### systemd Service (Production)

```bash
# Deploy to /opt/yt-dlp-api
sudo mv yt-dlp-api_* /opt/yt-dlp-api

# Install service
cd /opt/yt-dlp-api/scripts
sudo ./install-service.sh

# Manage
sudo systemctl start/stop/restart yt-dlp-api
sudo journalctl -u yt-dlp-api -f
```

See `SYSTEMD.md` for detailed systemd deployment guide.

## Important Implementation Details

1. **No format prefix in filenames**: Files are saved as `title.ext` not `format-title.ext`

2. **URL-based deduplication**: Same URL = same task, regardless of output_path or format

3. **Automatic retry**: Failed tasks automatically retry when the same URL is submitted again

4. **Site path mapping**: Use `SITE_PATH_MAPPING` in .env, not hardcoded logic

5. **Global thread pool**: Single ThreadPoolExecutor shared across all downloads (configured via `THREAD_POOL_SIZE`)

6. **Structured logs**: All print statements replaced with logger calls including context

## Dependencies

- **FastAPI**: Web framework
- **yt-dlp**: Video download library (core functionality)
- **uvicorn**: ASGI server
- **pydantic-settings**: Configuration management
- **SQLAlchemy**: ORM framework
- **pymysql**: MySQL driver
- **loguru**: Structured logging
- **ffmpeg**: System dependency for video processing

## Testing

API documentation auto-generated at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Git Commit Convention

```
[type]: <type> [description]:<description>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

Example: `[type]: feat [description]:添加视频标题字段到数据库`

## Additional Documentation

- `README_CN.md`: Chinese documentation
- `SYSTEMD.md`: systemd service deployment guide
- `TODO.md`: Planned improvements and known issues
- `INSTALL.md`: Generated in package, deployment instructions
