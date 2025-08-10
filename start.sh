#!/bin/bash

# Vue FastAPI Admin 一键启动脚本
# 作者: AI Assistant
# 功能: 清除端口占用，启动前后端服务

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
PROJECT_ROOT=$(pwd)
WEB_DIR="$PROJECT_ROOT/web"

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

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 命令未找到，请先安装 $1"
        exit 1
    fi
}

# 杀死占用指定端口的进程
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        log_warning "端口 $port 被占用，正在清理进程..."
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 2
        log_success "端口 $port 已清理"
    else
        log_info "端口 $port 未被占用"
    fi
}

# 检查Python虚拟环境
check_python_env() {
    log_info "检查Python环境..."
    
    # 检查是否在虚拟环境中
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        log_success "已在虚拟环境中: $VIRTUAL_ENV"
    else
        # 尝试激活虚拟环境
        if [ -d ".venv" ]; then
            log_info "发现虚拟环境，正在激活..."
            source .venv/bin/activate
            log_success "虚拟环境已激活"
        elif [ -d "venv" ]; then
            log_info "发现虚拟环境，正在激活..."
            source venv/bin/activate
            log_success "虚拟环境已激活"
        else
            log_warning "未发现虚拟环境，使用系统Python"
        fi
    fi
    
    # 检查Python版本
    python_version=$(python --version 2>&1 | cut -d' ' -f2)
    log_info "Python版本: $python_version"
}

# 安装Python依赖
install_python_deps() {
    log_info "检查Python依赖..."
    
    if [ -f "requirements.txt" ]; then
        log_info "使用pip安装依赖..."
        pip install -r requirements.txt -q
    elif [ -f "pyproject.toml" ]; then
        if command -v uv &> /dev/null; then
            log_info "使用uv安装依赖..."
            uv sync
        else
            log_info "使用pip安装依赖..."
            pip install -e . -q
        fi
    fi
    
    log_success "Python依赖检查完成"
}

# 检查Node.js环境
check_node_env() {
    log_info "检查Node.js环境..."
    
    if ! command -v node &> /dev/null; then
        log_error "Node.js未安装，请先安装Node.js"
        exit 1
    fi
    
    node_version=$(node --version)
    log_info "Node.js版本: $node_version"
    
    # 检查包管理器
    if command -v pnpm &> /dev/null; then
        PACKAGE_MANAGER="pnpm"
    elif command -v yarn &> /dev/null; then
        PACKAGE_MANAGER="yarn"
    else
        PACKAGE_MANAGER="npm"
    fi
    
    log_info "使用包管理器: $PACKAGE_MANAGER"
}

# 安装前端依赖
install_frontend_deps() {
    log_info "检查前端依赖..."
    
    cd "$WEB_DIR"
    
    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        $PACKAGE_MANAGER install
        log_success "前端依赖安装完成"
    else
        log_info "前端依赖已存在"
    fi
    
    cd "$PROJECT_ROOT"
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    
    # 检查run.py是否存在
    if [ ! -f "run.py" ]; then
        log_error "run.py文件不存在"
        exit 1
    fi
    
    # 后台启动后端
    nohup python run.py > backend.log 2>&1 &
    BACKEND_PID=$!
    
    # 等待后端启动
    log_info "等待后端服务启动..."
    sleep 5
    
    # 检查后端是否启动成功
    if curl -s "http://localhost:$BACKEND_PORT/docs" > /dev/null; then
        log_success "后端服务启动成功 (PID: $BACKEND_PID)"
        log_info "API文档地址: http://localhost:$BACKEND_PORT/docs"
    else
        log_error "后端服务启动失败，请检查 backend.log"
        exit 1
    fi
}

# 启动前端服务
start_frontend() {
    log_info "启动前端服务..."

    cd "$WEB_DIR"

    # 根据包管理器选择正确的命令
    if [ "$PACKAGE_MANAGER" = "pnpm" ]; then
        FRONTEND_CMD="pnpm dev"
    elif [ "$PACKAGE_MANAGER" = "yarn" ]; then
        FRONTEND_CMD="yarn dev"
    else
        FRONTEND_CMD="npm run dev"
    fi

    log_info "使用命令: $FRONTEND_CMD"

    # 后台启动前端
    nohup $FRONTEND_CMD > ../frontend.log 2>&1 &
    FRONTEND_PID=$!

    # 等待前端启动
    log_info "等待前端服务启动..."
    sleep 10

    # 检查前端是否启动成功
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null; then
        log_success "前端服务启动成功 (PID: $FRONTEND_PID)"
        log_info "前端地址: http://localhost:$FRONTEND_PORT"
    else
        log_warning "前端服务可能仍在启动中，请稍后访问 http://localhost:$FRONTEND_PORT"
    fi

    cd "$PROJECT_ROOT"
}

# 保存PID到文件
save_pids() {
    echo "BACKEND_PID=$BACKEND_PID" > .pids
    echo "FRONTEND_PID=$FRONTEND_PID" >> .pids
    log_info "进程ID已保存到 .pids 文件"
}

# 显示启动信息
show_info() {
    echo ""
    echo "=========================================="
    log_success "Vue FastAPI Admin 启动完成！"
    echo "=========================================="
    echo -e "${BLUE}前端地址:${NC} http://localhost:$FRONTEND_PORT"
    echo -e "${BLUE}后端API:${NC} http://localhost:$BACKEND_PORT/docs"
    echo -e "${BLUE}默认账号:${NC} admin"
    echo -e "${BLUE}默认密码:${NC} 123456"
    echo ""
    echo -e "${YELLOW}日志文件:${NC}"
    echo -e "  后端日志: backend.log"
    echo -e "  前端日志: frontend.log"
    echo ""
    echo -e "${YELLOW}停止服务:${NC} ./stop.sh"
    echo "=========================================="
}

# 主函数
main() {
    log_info "开始启动 Vue FastAPI Admin..."
    
    # 检查基础命令
    check_command "python"
    check_command "curl"
    check_command "lsof"
    
    # 清理端口
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    
    # 检查环境
    check_python_env
    check_node_env
    
    # 安装依赖
    install_python_deps
    install_frontend_deps
    
    # 启动服务
    start_backend
    start_frontend
    
    # 保存进程ID
    save_pids
    
    # 显示启动信息
    show_info
}

# 捕获中断信号
trap 'log_error "启动被中断"; exit 1' INT TERM

# 执行主函数
main "$@"
