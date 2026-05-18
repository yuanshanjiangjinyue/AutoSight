# AutoSight 公网访问解决方案

## 当前情况

你的 Mac 网络环境有以下限制：
- ❌ 无法从 GitHub 下载任何工具
- ❌ 无法使用 localtunnel 服务
- ✅ 可以访问部分网站（如 npm、nodejs.org）

服务器状态：
- ✅ 后端服务 (5000端口): 正常运行
- ✅ 反向代理 (8080端口): 正常运行
- ✅ 本地访问: 完全正常

## 可行方案

### 方案 1: 使用代理或 VPN（推荐）

如果你有代理服务器或 VPN，可以配置环境变量：

```bash
# 如果你有 HTTP/HTTPS 代理
export HTTP_PROXY="http://your-proxy-server:port"
export HTTPS_PROXY="http://your-proxy-server:port"

# 然后重试安装
brew install cloudflared
```

### 方案 2: 使用国内可访问的隧道服务

尝试使用国内的内网穿透服务：

1. **花生壳** (需要注册)
   - https://hsk.oray.com/
   - 有免费版可用

2. **NATAPP** (需要注册)
   - https://natapp.cn/
   - 提供免费隧道

3. **Sakura Frp** (需要注册)
   - https://www.natfrp.com/
   - 有免费节点

### 方案 3: 使用云服务器部署（最稳定）

购买一台云服务器（如阿里云、腾讯云），在服务器上部署 AutoSight：

**优点：**
- 24/7 运行，无需本地电脑
- 稳定的公网 IP
- 完全可控

**步骤：**

1. 购买云服务器（建议：阿里云 ECS 或腾讯云）
   - 最低配置：1核1G 即可
   - 系统：Ubuntu 20.04 或 CentOS 8

2. 连接服务器并安装依赖：
   ```bash
   # 更新系统
   sudo apt update && sudo apt upgrade -y
   
   # 安装 Python 和 pip
   sudo apt install -y python3 python3-pip
   
   # 安装 Flask
   pip3 install flask flask-cors
   
   # 上传代码
   scp -r /Users/lawrence/Documents/Auto-Analysis user@your-server-ip:/opt/
   
   # 启动服务
   cd /opt/Auto-Analysis
   python3 app.py
   ```

3. 配置防火墙
   - 开放 5000 端口
   - 或使用 Nginx 反向代理

4. 域名绑定（如有域名）
   - 配置 DNS 解析
   - 申请 SSL 证书

### 方案 4: 使用 ngrok 国内版或其他工具

如果你能找到可访问的 ngrok 下载链接，可以尝试：

1. 从可访问的镜像下载
2. 配置 ngrok 账户和 authtoken
3. 运行 `ngrok http 5000`

## 立即可用的本地访问

虽然无法立即实现公网访问，但你的服务在本地完全可以正常使用：

**本地访问地址：**
- http://localhost:5000
- http://localhost:8080
- http://192.168.43.135:5000 (局域网 IP)

**登录信息：**
- 管理员: admin / 123456
- 测试用户: test_user / 123456
- 普通用户: xiaowang / 123456

## 推荐行动

1. **短期**：使用手机热点或找到可用的代理来下载 cloudflared
2. **中期**：注册一个国内的内网穿透服务（花生壳、NATAPP 等）
3. **长期**：购买云服务器进行正式部署

## 获取帮助

如果需要我帮你：
- 编写详细的云服务器部署脚本
- 配置 Nginx 和 SSL 证书
- 编写自动化部署脚本

请告诉我你选择的方案！
