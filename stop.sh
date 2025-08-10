#!/bin/bash

# Vue FastAPI Admin 停止脚本
# 作者: AI Assistant
# 功能: 停止前后端服务

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BACKEND_PORT=9999
FRONTEND_PORT=3100
PID_FILE=".pids"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 杀死指定PID的进程
kill_pid() {
    local pid=$1
    local name=$2
    
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        log_info "停止 $name 服务 (PID: $pid)..."
        kill -TERM "$pid" 2>/dev/null || true
        sleep 2
        
        # 如果进程仍然存在，强制杀死
        if kill -0 "$pid" 2>/dev/null; then
            log_warning "强制停止 $name 服务..."
            kill -9 "$pid" 2>/dev/null || true
        fi
        
        log_success "$name 服务已停止"
    else
        log_info "$name 服务未运行或PID无效"
    fi
}

# 杀死占用指定端口的进程
kill_port() {
    local port=$1
    local name=$2
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        log_warning "发现端口 $port 被占用，清理 $name 相关进程..."
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
        log_success "端口 $port 已清理"
    else
        log_info "端口 $port 未被占用"
    fi
}

# 从PID文件读取并停止服务
stop_from_pid_file() {
    if [ -f "$PID_FILE" ]; then
        log_info "从 $PID_FILE 读取进程信息..."
        
        # 读取PID
        source "$PID_FILE"
        
        # 停止后端
        if [ -n "$BACKEND_PID" ]; then
            kill_pid "$BACKEND_PID" "后端"
        fi
        
        # 停止前端
        if [ -n "$FRONTEND_PID" ]; then
            kill_pid "$FRONTEND_PID" "前端"
        fi
        
        # 删除PID文件
        rm -f "$PID_FILE"
        log_success "PID文件已清理"
    else
        log_warning "PID文件不存在，尝试通过端口清理进程..."
    fi
}

# 通过端口强制清理
force_cleanup() {
    log_info "执行强制清理..."
    kill_port $BACKEND_PORT "后端"
    kill_port $FRONTEND_PORT "前端"
}

# 清理日志文件
cleanup_logs() {
    if [ "$1" = "--clean-logs" ]; then
        log_info "清理日志文件..."
        rm -f backend.log frontend.log
        log_success "日志文件已清理"
    fi
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --clean-logs    同时清理日志文件"
    echo "  --force         强制清理所有相关进程"
    echo "  --help          显示此帮助信息"
    echo ""
}

# 主函数
main() {
    local force_mode=false
    local clean_logs=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force_mode=true
                shift
                ;;
            --clean-logs)
                clean_logs=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log_info "开始停止 Vue FastAPI Admin 服务..."
    
    if [ "$force_mode" = true ]; then
        force_cleanup
    else
        stop_from_pid_file
        # 如果PID方式失败，尝试端口清理
        force_cleanup
    fi
    
    # 清理日志
    if [ "$clean_logs" = true ]; then
        cleanup_logs --clean-logs
    fi
    
    echo ""
    echo "=========================================="
    log_success "Vue FastAPI Admin 已停止！"
    echo "=========================================="
    
    if [ "$clean_logs" = false ]; then
        echo -e "${YELLOW}提示:${NC} 使用 --clean-logs 参数可同时清理日志文件"
    fi
}

# 执行主函数
main "$@"
