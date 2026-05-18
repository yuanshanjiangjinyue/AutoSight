#!/bin/bash
# AutoSight 服务器 + 公网访问一键启动

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AutoSight 服务器管理工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 启动后端服务
start_backend() {
    echo -e "${YELLOW}启动后端服务...${NC}"
    
    if lsof -i :5000 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务已在运行${NC}"
    else
        cd /Users/lawrence/Documents/Auto-Analysis
        nohup python3 app.py > /tmp/autosight-backend.log 2>&1 &
        sleep 3
        
        if lsof -i :5000 >/dev/null 2>&1; then
            echo -e "${GREEN}✓ 后端服务启动成功${NC}"
        else
            echo -e "${RED}✗ 后端服务启动失败${NC}"
            return 1
        fi
    fi
}

# 检查公网工具
check_public_tools() {
    echo ""
    echo -e "${BLUE}检查公网访问工具...${NC}"
    
    if command -v cloudflared &> /dev/null; then
        echo -e "${GREEN}✓ cloudflared 已安装${NC}"
        return 0
    elif [ -f "/tmp/cloudflared" ]; then
        echo -e "${GREEN}✓ cloudflared 已下载${NC}"
        return 0
    elif command -v ngrok &> /dev/null; then
        echo -e "${GREEN}✓ ngrok 已安装${NC}"
        return 0
    else
        echo -e "${YELLOW}✗ 未检测到公网访问工具${NC}"
        return 1
    fi
}

# 启动公网访问
start_public_access() {
    echo ""
    echo -e "${BLUE}启动公网访问...${NC}"
    
    if command -v cloudflared &> /dev/null || [ -f "/tmp/cloudflared" ]; then
        CLOUDFLARED_CMD="/tmp/cloudflared"
        if command -v cloudflared &> /dev/null; then
            CLOUDFLARED_CMD="cloudflared"
        fi
        
        echo -e "${GREEN}使用 Cloudflare Tunnel 启动公网访问...${NC}"
        echo ""
        $CLOUDFLARED_CMD tunnel --url http://localhost:5000
        
    elif command -v ngrok &> /dev/null; then
        echo -e "${GREEN}使用 ngrok 启动公网访问...${NC}"
        echo ""
        ngrok http 5000
        
    else
        echo ""
        echo -e "${RED}没有可用的公网访问工具！${NC}"
        echo ""
        echo -e "${YELLOW}请选择安装方式：${NC}"
        echo ""
        echo "  方案 A: 安装 Homebrew + cloudflared (推荐)"
        echo "    1. 安装 Homebrew:"
        echo "       /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo ""
        echo "    2. 安装 cloudflared:"
        echo "       brew install cloudflared"
        echo ""
        echo "  方案 B: 手动下载 cloudflared"
        echo "    1. 浏览器访问: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
        echo "    2. 下载 macOS ARM64 版本"
        echo "    3. 保存到: /tmp/cloudflared"
        echo "    4. 执行: chmod +x /tmp/cloudflared"
        echo ""
        echo "  方案 C: 使用内网穿透服务"
        echo "    1. 注册 ngrok: https://ngrok.com/"
        echo "    2. 安装 ngrok: brew install ngrok"
        echo "    3. 配置 token 并启动"
        echo ""
        echo "安装完成后，重新运行此脚本"
    fi
}

# 主流程
main() {
    start_backend
    
    if check_public_tools; then
        start_public_access
    else
        echo ""
        echo -e "${YELLOW}按回车键查看安装指南，或 Ctrl+C 退出...${NC}"
        read
        
        echo ""
        echo -e "${BLUE}========================================${NC}"
        echo -e "${BLUE}  安装指南${NC}"
        echo -e "${BLUE}========================================${NC}"
        echo ""
        cat << 'EOF'
需要先安装公网访问工具才能让其他人访问你的网站。

推荐方案：使用 Homebrew 安装 cloudflared

步骤 1: 安装 Homebrew (如果没有)
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

步骤 2: 安装 cloudflared
   brew install cloudflared

步骤 3: 重新运行此脚本
   ./start-server.sh

或者手动下载 cloudflared:
   1. 浏览器打开: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
   2. 下载 macOS ARM64 版本
   3. 终端执行: chmod +x ~/Downloads/cloudflared
   4. 复制到系统路径: sudo cp ~/Downloads/cloudflared /usr/local/bin/
   5. 验证安装: cloudflared --version
EOF
        echo ""
    fi
}

main
