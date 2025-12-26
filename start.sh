#!/bin/bash
# -*- coding: utf-8 -*-
# Easy-BabelDOC 项目启动脚本 - 同时启动前端和后端服务

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
    BACKEND_LOG_FILE="/tmp/easy_babeldoc_backend.log"
    FRONTEND_LOG_FILE="/tmp/easy_babeldoc_frontend.log"
else
    BACKEND_PID_FILE="$SCRIPT_DIR/.backend.pid"
    FRONTEND_PID_FILE="$SCRIPT_DIR/.frontend.pid"
    BACKEND_LOG_FILE="$SCRIPT_DIR/.backend.log"
    FRONTEND_LOG_FILE="$SCRIPT_DIR/.frontend.log"
fi

# 显示使用说明
show_usage() {
    echo -e "${BLUE}使用方法:${NC}"
    echo -e "  $0                  # 启动前端和后端服务(自动重新构建前端)"
    echo -e "  $0 backend          # 仅启动后端服务"
    echo -e "  $0 frontend         # 仅启动前端服务(自动重新构建)"
    echo -e "  $0 dev              # 开发模式(前台运行前端,支持热重载)"
    echo -e ""
    echo -e "${BLUE}说明:${NC}"
    echo -e "  - 默认启动会自动重新构建前端,确保使用最新代码"
    echo -e "  - 开发模式推荐用于本地开发,支持热重载"
}

# 检查服务是否已运行
check_running() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${YELLOW}$service_name 已经在运行中 (PID: $pid)${NC}"
            return 0
        else
            rm -f "$pid_file"
        fi
    fi
    return 1
}

# 启动后端服务
start_backend() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}启动后端服务...${NC}"
    echo -e "${GREEN}========================================${NC}"
    
    if check_running "$BACKEND_PID_FILE" "后端服务"; then
        return 0
    fi
    
    # 检查 backend 目录
    if [ ! -d "$SCRIPT_DIR/backend" ]; then
        echo -e "${RED}错误: backend 目录不存在${NC}"
        return 1
    fi
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到 python3 命令${NC}"
        return 1
    fi
    
    # 检查 main.py
    if [ ! -f "$SCRIPT_DIR/backend/main.py" ]; then
        echo -e "${RED}错误: backend/main.py 不存在${NC}"
        return 1
    fi
    
    # 设置 LD_LIBRARY_PATH 使用 conda 环境的库
    if [ -n "$CONDA_PREFIX" ]; then
        export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"
    fi
    
    # 启动后端
    cd "$SCRIPT_DIR/backend"
    nohup python3 main.py > "$BACKEND_LOG_FILE" 2>&1 &
    echo $! > "$BACKEND_PID_FILE"
    cd "$SCRIPT_DIR"
    
    sleep 2
    
    if ps -p $(cat "$BACKEND_PID_FILE") > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务启动成功 (PID: $(cat "$BACKEND_PID_FILE"))${NC}"
        echo -e "${GREEN}  API地址: http://localhost:58273${NC}"
        echo -e "${GREEN}  API文档: http://localhost:58273/docs${NC}"
        echo -e "${GREEN}  日志文件: $BACKEND_LOG_FILE${NC}"
        return 0
    else
        echo -e "${RED}✗ 后端服务启动失败，请查看日志: $BACKEND_LOG_FILE${NC}"
        rm -f "$BACKEND_PID_FILE"
        return 1
    fi
}

# 启动前端服务
start_frontend() {
    local force_rebuild=${1:-false}
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}启动前端服务...${NC}"
    echo -e "${GREEN}========================================${NC}"
    
    if check_running "$FRONTEND_PID_FILE" "前端服务"; then
        return 0
    fi
    
    # 检查 node_modules
    if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
        echo -e "${YELLOW}警告: node_modules 不存在，建议先运行: npm install${NC}"
    fi
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}错误: 未找到 npm 命令${NC}"
        return 1
    fi
    
    # 默认总是重新构建前端(服务器部署场景)
    cd "$SCRIPT_DIR"
    
    if [ "$force_rebuild" = false ]; then
        echo -e "${YELLOW}正在构建前端...${NC}"
    else
        echo -e "${YELLOW}强制重新构建前端...${NC}"
    fi
    
    npm run build
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ 前端构建失败${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ 前端构建完成${NC}"
    
    # 启动前端预览服务
    nohup npm run preview > "$FRONTEND_LOG_FILE" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"
    
    sleep 3
    
    if ps -p $(cat "$FRONTEND_PID_FILE") > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 前端服务启动成功 (PID: $(cat "$FRONTEND_PID_FILE"))${NC}"
        echo -e "${GREEN}  访问地址: http://localhost:4173${NC}"
        echo -e "${GREEN}  日志文件: $FRONTEND_LOG_FILE${NC}"
        return 0
    else
        echo -e "${RED}✗ 前端服务启动失败，请查看日志: $FRONTEND_LOG_FILE${NC}"
        rm -f "$FRONTEND_PID_FILE"
        return 1
    fi
}

# 开发模式 - 前台运行前端
start_dev() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}开发模式启动${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # 先启动后端
    start_backend
    if [ $? -ne 0 ]; then
        echo -e "${RED}后端启动失败，退出${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${BLUE}前端将在前台运行，按 Ctrl+C 停止${NC}"
    echo -e "${BLUE}========================================${NC}"
    sleep 1
    
    # 前台运行前端开发服务器
    npm run dev
}

# 解析参数
FORCE_REBUILD=false
COMMAND="${1:-all}"

# 检查是否有 --rebuild 参数
for arg in "$@"; do
    if [ "$arg" = "--rebuild" ]; then
        FORCE_REBUILD=true
    fi
done

# 主逻辑
case "$COMMAND" in
    backend)
        start_backend
        exit $?
        ;;
    frontend)
        start_frontend $FORCE_REBUILD
        exit $?
        ;;
    dev)
        start_dev
        exit $?
        ;;
    all|"")
        start_backend
        BACKEND_STATUS=$?
        echo ""
        start_frontend $FORCE_REBUILD
        FRONTEND_STATUS=$?
        
        echo ""
        echo -e "${GREEN}========================================${NC}"
        if [ $BACKEND_STATUS -eq 0 ] && [ $FRONTEND_STATUS -eq 0 ]; then
            echo -e "${GREEN}✓ Easy-BabelDOC 所有服务启动成功${NC}"
            echo -e "${GREEN}========================================${NC}"
            echo -e "${GREEN}后端日志: tail -f $BACKEND_LOG_FILE${NC}"
            echo -e "${GREEN}前端日志: tail -f $FRONTEND_LOG_FILE${NC}"
            exit 0
        else
            echo -e "${RED}✗ 部分服务启动失败${NC}"
            echo -e "${RED}========================================${NC}"
            exit 1
        fi
        ;;
    -h|--help|help|--rebuild)
        if [ "$COMMAND" = "--rebuild" ]; then
            # --rebuild 作为第一个参数时，启动所有服务并重新构建
            start_backend
            BACKEND_STATUS=$?
            echo ""
            start_frontend true
            FRONTEND_STATUS=$?
            
            echo ""
            echo -e "${GREEN}========================================${NC}"
            if [ $BACKEND_STATUS -eq 0 ] && [ $FRONTEND_STATUS -eq 0 ]; then
                echo -e "${GREEN}✓ Easy-BabelDOC 所有服务启动成功${NC}"
                echo -e "${GREEN}========================================${NC}"
                echo -e "${GREEN}后端日志: tail -f $BACKEND_LOG_FILE${NC}"
                echo -e "${GREEN}前端日志: tail -f $FRONTEND_LOG_FILE${NC}"
                exit 0
            else
                echo -e "${RED}✗ 部分服务启动失败${NC}"
                echo -e "${RED}========================================${NC}"
                exit 1
            fi
        else
            show_usage
            exit 0
        fi
        ;;
    *)
        echo -e "${RED}错误: 未知参数 '$1'${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
