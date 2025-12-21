#!/bin/bash
# -*- coding: utf-8 -*-
# Easy-BabelDOC 停止脚本

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# PID 文件路径（与 start.sh 保持一致）
if [ -d "/tmp" ]; then
    PID_FILE="/tmp/easy_babeldoc.pid"
else
    PID_FILE="$SCRIPT_DIR/.main.pid"
fi

# 检查PID文件是否存在
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}Easy-BabelDOC 未运行或PID文件不存在${NC}"
    
    # 尝试通过进程名查找
    PIDS=$(ps aux | grep "python3 main.py" | grep -v grep | awk '{print $2}')
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}发现运行中的进程，尝试停止...${NC}"
        for PID in $PIDS; do
            echo -e "${YELLOW}正在停止进程 $PID...${NC}"
            kill "$PID" 2>/dev/null
            sleep 1
            if ps -p "$PID" > /dev/null 2>&1; then
                echo -e "${YELLOW}正常停止失败，尝试强制停止...${NC}"
                kill -9 "$PID" 2>/dev/null
            fi
        done
        echo -e "${GREEN}✓ 已停止所有相关进程${NC}"
    fi
    exit 0
fi

# 读取PID
PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}进程已停止 (PID: $PID)${NC}"
    rm -f "$PID_FILE"
    exit 0
fi

# 尝试优雅地停止进程
echo -e "${GREEN}正在停止 Easy-BabelDOC 服务 (PID: $PID)...${NC}"
kill "$PID"

# 等待进程结束（最多等待10秒）
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Easy-BabelDOC 服务已成功停止${NC}"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# 如果进程仍在运行，强制停止
if ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}正常停止超时，正在强制停止...${NC}"
    kill -9 "$PID"
    sleep 1
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${RED}✗ 无法停止进程 (PID: $PID)${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ Easy-BabelDOC 服务已强制停止${NC}"
        rm -f "$PID_FILE"
        exit 0
    fi
fi
