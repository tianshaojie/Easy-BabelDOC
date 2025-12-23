# 数据库模块说明

## 概述

本模块使用 SQLite 数据库存储翻译历史记录，替代原有的 JSON 文件存储方式。

## 目录结构

```
db/
├── __init__.py          # 模块导出
├── database.py          # 数据库连接和管理
├── models.py            # 数据模型（TranslationHistory）
└── README.md            # 本文档
```

## 数据库位置

- **开发环境**: `~/.easy-babeldoc/babeldoc.db`
- **Windows**: `%APPDATA%/Easy-BabelDOC/babeldoc.db`
- **自定义**: 通过环境变量 `EASY_BABELDOC_DATA_DIR` 指定

## 表结构

### translation_history

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | TEXT PRIMARY KEY | 任务唯一标识 |
| status | TEXT NOT NULL | 任务状态 (running/completed/error) |
| filename | TEXT NOT NULL | 原始文件名 |
| source_lang | TEXT NOT NULL | 源语言 |
| target_lang | TEXT NOT NULL | 目标语言 |
| model | TEXT NOT NULL | 使用的模型 |
| start_time | TEXT NOT NULL | 开始时间 (ISO格式) |
| end_time | TEXT | 结束时间 |
| progress | INTEGER | 进度 (0-100) |
| stage | TEXT | 当前阶段 |
| message | TEXT | 状态消息 |
| error | TEXT | 错误信息 |
| config | TEXT | 配置信息 (JSON) |
| result | TEXT | 翻译结果 (JSON) |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**索引**:
- `idx_status`: 按状态查询
- `idx_created_at`: 按创建时间倒序查询

## 使用方法

### 基本操作

```python
from db import Database, TranslationHistory
from config.settings import DB_FILE

# 初始化数据库
db = Database(DB_FILE)
history = TranslationHistory(db)

# 创建记录
task_data = {
    "task_id": "xxx",
    "status": "running",
    "filename": "test.pdf",
    # ... 其他字段
}
history.create(task_data)

# 更新记录
history.update("task_id", {"status": "completed", "progress": 100})

# 查询记录
task = history.get_by_id("task_id")
all_tasks = history.get_all(limit=10)

# 删除记录
history.delete("task_id")

# 插入或更新（推荐）
history.upsert(task_data)
```

### 在接口中使用

```python
from utils.history import add_to_history, get_task, delete_task, load_history

# 添加/更新历史记录
add_to_history(task_data)

# 获取任务（优先从内存，其次从数据库）
task = get_task(task_id, active_translations)

# 删除任务
success = delete_task(task_id)

# 加载所有历史
history = load_history()
```

## 数据迁移

如果你有旧的 `translation_history.json` 文件，运行迁移脚本：

```bash
cd backend
python utils/migrate_to_db.py
```

迁移完成后，原 JSON 文件会被重命名为 `translation_history.backup.json`。

## 注意事项

1. **线程安全**: 每次操作都会创建新的数据库连接，适合多线程环境
2. **敏感信息**: API Key 等敏感信息会在存储前自动过滤
3. **JSON 字段**: `config` 和 `result` 字段自动序列化/反序列化
4. **备份**: 建议定期备份 `babeldoc.db` 文件

## 性能优化

- 已创建索引优化常见查询
- 使用上下文管理器自动管理连接
- 批量操作时使用事务

## 故障排查

### 数据库锁定
如果遇到 "database is locked" 错误，检查是否有其他进程正在访问数据库。

### 迁移失败
检查 JSON 文件格式是否正确，查看迁移脚本输出的错误信息。

### 数据丢失
检查 `~/.easy-babeldoc/` 目录下是否有 `.backup.json` 文件。
