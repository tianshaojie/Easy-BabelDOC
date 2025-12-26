#!/bin/bash
# -*- coding: utf-8 -*-
# Easy-BabelDOC 项目停止脚本 - 同时停止前端和后端服务

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# PID 文件路径
if [ -d "/tmp" ]; then
    BACKEND_PID_FILE="/tmp/easy_babeldoc_backend.pid"
    FRONTEND_PID_FILE="/tmp/easy_babeldoc_frontend.pid"
else
    BACKEND_PID_FILE="$SCRIPT_DIR/.backend.pid"
    FRONTEND_PID_FILE="$SCRIPT_DIR/.frontend.pid"
fi

# 显示使用说明
show_usage() {
    echo -e "${BLUE}使用方法:${NC}"
    echo -e "  $0              # 停止前端和后端服务"
    echo -e "  $0 backend      # 仅停止后端服务"
    echo -e "  $0 frontend     # 仅停止前端服务"
}

# 停止服务的通用函数
stop_service() {
    local pid_file=$1
    local service_name=$2
    local process_pattern=$3
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}停止${service_name}...${NC}"
    echo -e "${GREEN}========================================${NC}"
    
    local stopped=0
    
    # 检查PID文件是否存在
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        
        # 检查进程是否存在
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${GREEN}正在停止 $service_name (PID: $pid)...${NC}"
            kill "$pid"
            
            # 等待进程结束（最多等待10秒）
            for i in {1..10}; do
                if ! ps -p "$pid" > /dev/null 2>&1; then
                    echo -e "${GREEN}✓ $service_name 已成功停止${NC}"
                    rm -f "$pid_file"
                    stopped=1
                    break
                fi
                sleep 1
            done
            
            # 如果进程仍在运行，强制停止
            if [ $stopped -eq 0 ] && ps -p "$pid" > /dev/null 2>&1; then
                echo -e "${YELLOW}正常停止超时，正在强制停止...${NC}"
                kill -9 "$pid"
                sleep 1
                
                if ps -p "$pid" > /dev/null 2>&1; then
                    echo -e "${RED}✗ 无法停止进程 (PID: $pid)${NC}"
                    return 1
                else
                    echo -e "${GREEN}✓ $service_name 已强制停止${NC}"
                    rm -f "$pid_file"
                    stopped=1
                fi
            fi
        else
            echo -e "${YELLOW}进程已停止 (PID: $pid)${NC}"
            rm -f "$pid_file"
            stopped=1
        fi
    fi
    
    # 如果没有PID文件或进程已停止，尝试通过进程名查找
    if [ $stopped -eq 0 ]; then
        echo -e "${YELLOW}PID文件不存在，尝试通过进程名查找...${NC}"
        
        local pids=$(ps aux | grep "$process_pattern" | grep -v grep | awk '{print $2}')
        if [ -n "$pids" ]; then
            echo -e "${YELLOW}发现运行中的进程，尝试停止...${NC}"
            for pid in $pids; do
                echo -e "${YELLOW}正在停止进程 $pid...${NC}"
                kill "$pid" 2>/dev/null
                sleep 1
                if ps -p "$pid" > /dev/null 2>&1; then
                    echo -e "${YELLOW}正常停止失败，尝试强制停止...${NC}"
                    kill -9 "$pid" 2>/dev/null
                fi
            done
            echo -e "${GREEN}✓ 已停止所有相关进程${NC}"
            stopped=1
        else
            echo -e "${YELLOW}未发现运行中的 $service_name${NC}"
            stopped=1
        fi
    fi
    
    return 0
}

# 停止后端服务
stop_backend() {
    stop_service "$BACKEND_PID_FILE" "后端服务" "python3 main.py"
    return $?
}

# 停止前端服务
stop_frontend() {
    stop_service "$FRONTEND_PID_FILE" "前端服务" "npm run preview"
    return $?
}

# 主逻辑
case "${1:-all}" in
    backend)
        stop_backend
        exit $?
        ;;
    frontend)
        stop_frontend
        exit $?
        ;;
    all|"")
        stop_backend
        BACKEND_STATUS=$?
        echo ""
        stop_frontend
        FRONTEND_STATUS=$?
        
        echo ""
        echo -e "${GREEN}========================================${NC}"
        if [ $BACKEND_STATUS -eq 0 ] && [ $FRONTEND_STATUS -eq 0 ]; then
            echo -e "${GREEN}✓ Easy-BabelDOC 所有服务已停止${NC}"
            echo -e "${GREEN}========================================${NC}"
            exit 0
        else
            echo -e "${RED}✗ 部分服务停止失败${NC}"
            echo -e "${RED}========================================${NC}"
            exit 1
        fi
        ;;
    -h|--help|help)
        show_usage
        exit 0
        ;;
    *)
        echo -e "${RED}错误: 未知参数 '$1'${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
