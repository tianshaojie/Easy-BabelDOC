# 数据库迁移指南

## 概述

本项目使用版本化的数据库迁移系统,确保在不同电脑或多人开发时数据库结构保持一致。

## 工作原理

1. **自动迁移**: 应用启动时会自动检测并执行所需的数据库迁移
2. **版本管理**: 使用 `schema_version` 表记录当前数据库版本
3. **增量更新**: 只执行尚未应用的迁移,避免重复执行

## 使用方法

### 正常启动应用

直接启动应用即可,迁移会自动执行:

```bash
python main.py
```

### 手动执行迁移

如果需要单独运行迁移(例如调试):

```bash
python -m db.migrate
```

## 添加新的迁移

当需要修改数据库结构时,按以下步骤操作:

### 1. 在 `db/migrate.py` 中添加新的迁移函数

```python
def migration_v3_add_new_feature(cursor: sqlite3.Cursor):
    """版本3: 添加新功能"""
    logger.info("执行迁移 v3: 添加新功能")
    
    # 检查表是否存在
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='new_table'
    """)
    
    if not cursor.fetchone():
        logger.info("创建new_table表...")
        cursor.execute("""
            CREATE TABLE new_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        logger.info("✓ new_table表创建完成")
```

### 2. 将新迁移添加到 MIGRATIONS 列表

```python
MIGRATIONS: List[Migration] = [
    Migration(1, "添加用户支持", migration_v1_add_user_support),
    Migration(2, "添加模型配置表", migration_v2_add_models_table),
    Migration(3, "添加新功能", migration_v3_add_new_feature),  # 新增
]
```

### 3. 测试迁移

```bash
# 手动运行迁移测试
python -m db.migrate

# 或启动应用测试
python main.py
```

## 迁移最佳实践

1. **向后兼容**: 尽量使用 `ALTER TABLE ADD COLUMN` 而不是删除列
2. **幂等性**: 使用 `IF NOT EXISTS` 确保迁移可以安全重复执行
3. **事务性**: 每个迁移在一个事务中执行,失败会自动回滚
4. **版本递增**: 新迁移的版本号必须大于现有所有版本号
5. **描述清晰**: 为每个迁移提供清晰的描述信息

## 常见问题

### Q: 换了新电脑,数据库表结构不一致怎么办?

A: 直接启动应用,迁移系统会自动检测并更新数据库到最新版本。

### Q: 多人开发时如何同步数据库结构?

A: 
1. 拉取最新代码(包含新的迁移)
2. 启动应用,迁移会自动执行
3. 无需手动修改数据库

### Q: 如何查看当前数据库版本?

A: 查询 `schema_version` 表:

```sql
SELECT * FROM schema_version ORDER BY version DESC;
```

### Q: 迁移失败怎么办?

A: 
1. 查看错误日志,定位问题
2. 修复迁移代码
3. 如果数据库已损坏,可以删除数据库文件重新初始化(注意备份数据)

## 技术细节

### 迁移执行流程

```
启动应用
  ↓
Database.__init__()
  ↓
_ensure_db_exists() - 创建基础表
  ↓
_run_migrations() - 执行迁移
  ↓
检查 schema_version 表
  ↓
获取当前版本
  ↓
查找待执行的迁移
  ↓
按版本顺序执行
  ↓
更新 schema_version
  ↓
完成
```

### 数据库版本表结构

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
```

## 示例

### 添加新列

```python
def migration_v4_add_column(cursor: sqlite3.Cursor):
    """版本4: 添加新列"""
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'phone' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        logger.info("✓ 添加phone列完成")
```

### 创建新表

```python
def migration_v5_create_table(cursor: sqlite3.Cursor):
    """版本5: 创建新表"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='settings'
    """)
    
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✓ settings表创建完成")
```

### 数据迁移

```python
def migration_v6_migrate_data(cursor: sqlite3.Cursor):
    """版本6: 数据迁移"""
    # 添加新列
    cursor.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
    
    # 迁移数据
    cursor.execute("UPDATE users SET full_name = username WHERE full_name IS NULL")
    
    logger.info("✓ 数据迁移完成")
```
