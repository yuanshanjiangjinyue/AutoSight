
#!/bin/bash
# AutoSight 生产环境启动脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AutoSight 汽配选品工具 - 生产模式${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查是否使用 Docker
if [ -f "docker-compose.yml" ] && command -v docker-compose &>/dev/null; then
    echo -e "${YELLOW}检测到 Docker Compose 配置文件${NC}"
    read -p "是否使用 Docker 部署？(y/n): " use_docker
    
    if [ "$use_docker" = "y" ] || [ "$use_docker" = "Y" ]; then
        echo -e "${GREEN}正在启动 Docker 容器...${NC}"
        mkdir -p data logs/nginx
        docker-compose up -d
        echo -e "${GREEN}✅ Docker 部署成功！${NC}"
        echo -e "📍 访问地址: http://localhost"
        exit 0
    fi
fi

# 检查是否有 gunicorn
if ! command -v gunicorn &>/dev/null; then
    echo -e "${YELLOW}正在安装生产依赖...${NC}"
    pip install gunicorn -q
fi

# 创建必要目录
mkdir -p data logs

echo -e "${GREEN}正在启动服务...${NC}"

# 使用 Gunicorn 启动（生产推荐）
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 -t 300 --access-logfile logs/access.log --error-logfile logs/error.log app:app

echo -e "${GREEN}✅ 服务已启动！${NC}"
echo -e "📍 访问地址: http://localhost:5000"

