
# AutoSight 汽配选品工具 - 公网部署指南

## 🚀 方案一：Cloudflare Tunnel（最推荐，免费！）

无需公网IP，无需配置路由器，无需备案！

### 安装步骤：

**1. 安装 cloudflared（macOS）：**
```bash
brew install cloudflared
```

**2. 登录 Cloudflare：**
```bash
cloudflared tunnel login
```

**3. 创建隧道：**
```bash
cloudflared tunnel create auto-sight
```

**4. 配置隧道（替换 your-domain.com）：**
```bash
cloudflared tunnel route dns auto-sight your-domain.com
```

**5. 创建配置文件：**
```yaml
# config.yml
tunnel: YOUR-TUNNEL-ID
credentials-file: /Users/lawrence/.cloudflared/YOUR-TUNNEL-ID.json

ingress:
  - hostname: your-domain.com
    service: http://localhost:5000
  - service: http_status:404
```

**6. 运行隧道：**
```bash
cloudflared tunnel run --config config.yml
```

---

## 🐳 方案二：Docker Compose（推荐用于生产）

### 启动命令：
```bash
# 启动（包含 Nginx + 应用）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

---

## 🌐 方案三：传统云服务器部署

### 1. 安装 Nginx：
```bash
# Ubuntu/Debian
apt update && apt install nginx -y

# CentOS/RHEL
yum install nginx -y
```

### 2. 复制配置：
```bash
cp nginx.conf /etc/nginx/conf.d/auto-sight.conf
nginx -t  # 测试配置
systemctl restart nginx
```

### 3. 配置防火墙：
```bash
# 开放 80/443 端口
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 4. 使用 Gunicorn 运行应用：
```bash
pip install gunicorn
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

---

## ✅ 所有部署方案已准备好！

文件说明：
- `nginx.conf` - Nginx 反向代理配置
- `docker-compose.yml` - Docker 一键部署（包含 Nginx）
- `Dockerfile` - 应用容器镜像
- `requirements.txt` - Python 依赖

选择适合你的方案开始部署吧！

