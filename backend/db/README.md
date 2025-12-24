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

## 数据库结构迁移（重要）

### 自动迁移系统

本项目使用**版本化的数据库迁移系统**，确保在不同电脑或多人开发时数据库结构保持一致。

**特性**:
- ✅ **自动执行**: 应用启动时自动检测并执行所需迁移
- ✅ **版本管理**: 使用 `schema_version` 表跟踪数据库版本
- ✅ **增量更新**: 只执行尚未应用的迁移，避免重复
- ✅ **事务安全**: 迁移失败自动回滚

### 使用方法

**正常启动（推荐）**:
```bash
python main.py  # 迁移会自动执行
```

**手动执行迁移**:
```bash
python -m db.migrate
```

### 换电脑/多人开发场景

当你在新电脑上或拉取了包含数据库结构变更的代码后：

1. **无需手动操作** - 直接启动应用即可
2. 迁移系统会自动检测数据库版本
3. 自动执行所有缺失的迁移
4. 数据库更新到最新版本

**示例输出**:
```
INFO:easy_babeldoc.migrate:检查数据库迁移: ~/.easy-babeldoc/babeldoc.db
INFO:easy_babeldoc.migrate:当前数据库版本: 0
INFO:easy_babeldoc.migrate:发现 2 个待执行的迁移
INFO:easy_babeldoc.migrate:应用迁移 v1: 添加用户支持
INFO:easy_babeldoc.migrate:✓ 迁移 v1 完成
INFO:easy_babeldoc.migrate:应用迁移 v2: 添加模型配置表
INFO:easy_babeldoc.migrate:✓ 迁移 v2 完成
INFO:easy_babeldoc.migrate:所有数据库迁移成功完成!
```

详细文档请查看: [`MIGRATION_GUIDE.md`](./MIGRATION_GUIDE.md)

## JSON 数据迁移

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
