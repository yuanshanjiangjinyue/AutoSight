#!/bin/bash
# AutoSight 公网访问 - 一键启动脚本

echo "========================================"
echo "  AutoSight 公网访问工具"
echo "========================================"
echo ""

# 检查端口
check_port() {
    if ! lsof -i :5000 >/dev/null 2>&1; then
        echo "❌ 后端服务未运行，正在启动..."
        cd /Users/lawrence/Documents/Auto-Analysis
        nohup python3 app.py > /tmp/autosight-backend.log 2>&1 &
        sleep 3
        
        if ! lsof -i :5000 >/dev/null 2>&1; then
            echo "❌ 后端服务启动失败，请检查日志"
            exit 1
        fi
        echo "✅ 后端服务已启动"
    else
        echo "✅ 后端服务运行中"
    fi
}

# 方案1: 使用 ngrok (如果有)
check_ngrok() {
    if command -v ngrok &> /dev/null; then
        echo ""
        echo "检测到 ngrok，准备启动..."
        ngrok http 5000
        return 0
    fi
    return 1
}

# 方案2: 手动安装 cloudflared
install_cloudflared() {
    echo ""
    echo "正在检查 cloudflared..."
    
    # 检查不同位置
    if [ -f "/tmp/cloudflared" ]; then
        echo "✅ 找到 cloudflared"
        return 0
    fi
    
    echo "cloudflared 未安装"
    echo ""
    echo "请选择安装方式:"
    echo ""
    echo "  1. 使用 Homebrew 安装 (推荐)"
    echo "     /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo "     brew install cloudflared"
    echo ""
    echo "  2. 手动下载"
    echo "     访问: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    echo "     下载 macOS ARM64 版本，保存为 /tmp/cloudflared"
    echo "     chmod +x /tmp/cloudflared"
    echo ""
    echo "  3. 使用 localtunnel (无需安装)"
    echo ""
    
    read -p "请选择 (1-3): " choice
    
    case $choice in
        1)
            echo "正在安装 Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            brew install cloudflared
            ;;
        2)
            echo "请手动下载后按回车继续..."
            read
            ;;
        3)
            use_localtunnel
            return $?
            ;;
        *)
            echo "无效选项"
            return 1
            ;;
    esac
}

# 方案3: 使用 localtunnel
use_localtunnel() {
    echo ""
    echo "正在安装 localtunnel..."
    
    if ! command -v npx &> /dev/null; then
        echo "❌ 需要安装 Node.js 才能使用 localtunnel"
        return 1
    fi
    
    echo "✅ Localtunnel 安装完成"
    echo ""
    echo "正在启动隧道..."
    echo "⚠️  首次使用需要访问提示的 URL 并输入密码"
    echo ""
    
    lt --port 5000
}

# 启动 cloudflared 隧道
start_cloudflared_tunnel() {
    echo ""
    echo "正在启动 Cloudflare 隧道..."
    echo "⏳ 正在连接 Cloudflare 网络..."
    echo ""
    
    cloudflared tunnel --url http://localhost:5000
}

# 主流程
main() {
    check_port
    
    if check_ngrok; then
        exit 0
    fi
    
    if [ -f "/tmp/cloudflared" ] || command -v cloudflared &> /dev/null; then
        start_cloudflared_tunnel
    else
        install_cloudflared
        
        if [ -f "/tmp/cloudflared" ] || command -v cloudflared &> /dev/null; then
            start_cloudflared_tunnel
        else
            use_localtunnel
        fi
    fi
}

main
