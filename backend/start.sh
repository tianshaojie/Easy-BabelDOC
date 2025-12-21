#!/bin/bash
# -*- coding: utf-8 -*-
# Easy-BabelDOC 启动脚本

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# PID 文件和日志文件路径（放在临时目录，避免污染项目）
if [ -d "/tmp" ]; then
    PID_FILE="/tmp/easy_babeldoc.pid"
    LOG_FILE="/tmp/easy_babeldoc.log"
else
    PID_FILE="$SCRIPT_DIR/.main.pid"
    LOG_FILE="$SCRIPT_DIR/.output.log"
fi

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}Easy-BabelDOC 已经在运行中 (PID: $PID)${NC}"
        exit 1
    else
        # PID文件存在但进程不存在，删除旧的PID文件
        rm -f "$PID_FILE"
    fi
fi

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3 命令${NC}"
    exit 1
fi

# 检查main.py是否存在
if [ ! -f "$SCRIPT_DIR/main.py" ]; then
    echo -e "${RED}错误: 未找到 main.py 文件${NC}"
    exit 1
fi

# 检查依赖是否安装
echo -e "${GREEN}检查Python依赖...${NC}"
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    python3 -c "import fastapi" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}警告: 依赖可能未完全安装，建议运行: pip3 install -r requirements.txt${NC}"
    fi
fi

# 启动服务
echo -e "${GREEN}正在启动 Easy-BabelDOC 服务...${NC}"

# 使用nohup在后台运行，并将输出重定向到日志文件
nohup python3 main.py > "$LOG_FILE" 2>&1 &

# 保存PID
echo $! > "$PID_FILE"

# 等待一下确保服务启动
sleep 2

# 检查进程是否仍在运行
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Easy-BabelDOC 服务启动成功 (PID: $(cat "$PID_FILE"))${NC}"
    echo -e "${GREEN}日志文件: $LOG_FILE${NC}"
    echo -e "${GREEN}可以使用 tail -f $LOG_FILE 查看运行日志${NC}"
else
    echo -e "${RED}✗ 服务启动失败，请查看日志文件: $LOG_FILE${NC}"
    rm -f "$PID_FILE"
    exit 1
fi
