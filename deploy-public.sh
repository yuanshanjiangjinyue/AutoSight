
#!/bin/bash
# AutoSight 公网部署脚本

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

clear
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AutoSight 公网访问工具${NC}"
echo -e "${GREEN}========================================${NC}"

echo ""
echo "请选择部署方案："
echo ""
echo "  1. 使用 trycloudflare.com (临时，无需注册)"
echo "  2. 安装 Cloudflare Tunnel (推荐，永久免费)"
echo "  3. 使用本地网络 IP (仅限局域网)"
echo "  4. 退出"
echo ""

read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo -e "${YELLOW}正在检查是否有 cloudflared...${NC}"
        if ! command -v cloudflared &> /dev/null; then
            echo -e "${YELLOW}正在安装 cloudflared...${NC}"
            if command -v brew &> /dev/null; then
                brew install cloudflared
            else
                echo -e "${RED}请先安装 Homebrew，或使用方案 2${NC}"
                exit 1
            fi
        fi
        
        echo -e "${GREEN}正在启动临时隧道...${NC}"
        echo -e "${YELLOW}⏳ 请稍候，正在连接 Cloudflare...${NC}"
        echo ""
        cloudflared tunnel --url http://localhost:5000
        ;;
        
    2)
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  Cloudflare Tunnel 完整部署${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "步骤 1: 安装 cloudflared"
        echo -e "${YELLOW}   brew install cloudflared${NC}"
        echo ""
        echo -e "步骤 2: 登录 Cloudflare"
        echo -e "${YELLOW}   cloudflared tunnel login${NC}"
        echo ""
        echo -e "步骤 3: 创建隧道"
        echo -e "${YELLOW}   cloudflared tunnel create auto-sight${NC}"
        echo ""
        echo -e "步骤 4: 绑定域名（如果有）"
        echo -e "${YELLOW}   cloudflared tunnel route dns auto-sight your-domain.com${NC}"
        echo ""
        echo -e "步骤 5: 运行隧道"
        echo -e "${YELLOW}   cloudflared tunnel --url http://localhost:5000${NC}"
        echo ""
        echo -e "========================================${NC}"
        echo -e "详细文档请查看: ${GREEN}DEPLOYMENT.md${NC}"
        ;;
        
    3)
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  局域网访问${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        
        # 获取本机 IP
        if command -v ipconfig &> /dev/null; then
            IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1)
        else
            IP=$(hostname -I | awk '{print $1}')
        fi
        
        if [ -z "$IP" ]; then
            IP="localhost"
        fi
        
        echo -e "✅ 你的局域网地址："
        echo ""
        echo -e "   ${GREEN}http://$IP:5000${NC}"
        echo ""
        echo -e "确保手机/电脑在同一 Wi-Fi 下即可访问！"
        echo ""
        echo -e "${YELLOW}注意: 这只能在局域网内访问，公网无法访问${NC}"
        ;;
        
    4)
        echo -e "${YELLOW}已退出${NC}"
        exit 0
        ;;
        
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

