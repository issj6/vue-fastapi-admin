#!/bin/bash

# Vue FastAPI Admin MySQL切换脚本
# 作者: AI Assistant
# 功能: 切换到MySQL数据库并初始化

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_ROOT=$(pwd)
MYSQL_HOST="rm-uf642s70r4qde8iemio.mysql.rds.aliyuncs.com"
MYSQL_PORT="3306"
MYSQL_USER="root"
MYSQL_PASSWORD="Yyy443556"
MYSQL_DATABASE="paper"

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

# 检查MySQL连接
check_mysql_connection() {
    log_info "检查MySQL连接..."
    
    if command -v mysql &> /dev/null; then
        if mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "USE $MYSQL_DATABASE;" 2>/dev/null; then
            log_success "MySQL连接成功"
            return 0
        else
            log_error "MySQL连接失败，请检查数据库配置"
            return 1
        fi
    else
        log_warning "mysql客户端未安装，跳过连接测试"
        return 0
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

# 安装MySQL依赖
install_mysql_deps() {
    log_info "安装MySQL依赖..."

    # 安装asyncmy
    if python -c "import asyncmy" 2>/dev/null; then
        log_info "asyncmy已安装"
    else
        log_info "安装asyncmy..."
        # 使用官方源安装
        pip install -i https://pypi.org/simple/ asyncmy==0.2.9
        log_success "asyncmy安装完成"
    fi

    # 重新安装所有依赖以确保兼容性
    if [ -f "requirements.txt" ]; then
        log_info "更新所有依赖..."
        pip install -i https://pypi.org/simple/ -r requirements.txt -q
    elif [ -f "pyproject.toml" ]; then
        if command -v uv &> /dev/null; then
            log_info "使用uv更新依赖..."
            uv sync
        else
            log_info "使用pip更新依赖..."
            pip install -i https://pypi.org/simple/ -e . -q
        fi
    fi

    log_success "依赖安装完成"
}

# 备份SQLite数据库
backup_sqlite() {
    if [ -f "db.sqlite3" ]; then
        log_info "备份SQLite数据库..."
        cp db.sqlite3 "db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)"
        log_success "SQLite数据库已备份"
    fi
}

# 清理旧的迁移文件
clean_migrations() {
    log_info "清理旧的迁移文件..."
    
    if [ -d "migrations" ]; then
        log_warning "删除旧的迁移文件..."
        rm -rf migrations
        log_success "迁移文件已清理"
    fi
}

# 初始化MySQL数据库
init_mysql_db() {
    log_info "初始化MySQL数据库..."
    
    # 初始化Aerich
    log_info "初始化Aerich配置..."
    aerich init-db
    
    # 生成初始迁移
    log_info "生成数据库迁移..."
    aerich migrate --name init
    
    # 应用迁移
    log_info "应用数据库迁移..."
    aerich upgrade
    
    log_success "MySQL数据库初始化完成"
}

# 停止当前服务
stop_services() {
    log_info "停止当前服务..."
    
    if [ -f "stop.sh" ]; then
        ./stop.sh --force
    else
        # 手动停止端口占用
        local pids=$(lsof -ti:9999 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null || true
        fi
    fi
    
    log_success "服务已停止"
}

# 测试MySQL连接和启动
test_mysql_startup() {
    log_info "测试MySQL配置..."

    # 启动应用测试
    log_info "启动应用进行测试..."
    python run.py &
    APP_PID=$!

    # 等待应用启动
    log_info "等待应用启动..."
    sleep 15

    # 检查应用是否正常启动
    if curl -s "http://localhost:9999/docs" > /dev/null; then
        log_success "应用启动成功，MySQL配置正确"
        kill $APP_PID 2>/dev/null || true
        return 0
    else
        log_error "应用启动失败，请检查配置"
        kill $APP_PID 2>/dev/null || true
        return 1
    fi
}

# 显示切换结果
show_result() {
    echo ""
    echo "=========================================="
    log_success "MySQL切换完成！"
    echo "=========================================="
    echo -e "${BLUE}数据库信息:${NC}"
    echo -e "  主机: $MYSQL_HOST"
    echo -e "  端口: $MYSQL_PORT"
    echo -e "  用户: $MYSQL_USER"
    echo -e "  数据库: $MYSQL_DATABASE"
    echo ""
    echo -e "${BLUE}默认账号:${NC}"
    echo -e "  用户名: admin"
    echo -e "  密码: 123456"
    echo ""
    echo -e "${YELLOW}启动应用:${NC} ./start.sh"
    echo -e "${YELLOW}查看日志:${NC} tail -f backend.log"
    echo "=========================================="
}

# 主函数
main() {
    log_info "开始切换到MySQL数据库..."
    
    # 检查基础环境
    check_command "python"
    check_command "pip"
    
    # 停止当前服务
    stop_services
    
    # 检查环境
    check_python_env
    
    # 检查MySQL连接
    if ! check_mysql_connection; then
        log_error "MySQL连接失败，请检查网络和数据库配置"
        exit 1
    fi
    
    # 备份SQLite数据库
    backup_sqlite
    
    # 安装MySQL依赖
    install_mysql_deps
    
    # 清理旧迁移
    clean_migrations
    
    # 初始化MySQL数据库
    init_mysql_db
    
    # 测试MySQL配置
    if test_mysql_startup; then
        show_result
    else
        log_error "MySQL配置测试失败，请检查日志"
        exit 1
    fi
}

# 捕获中断信号
trap 'log_error "切换被中断"; exit 1' INT TERM

# 执行主函数
main "$@"
