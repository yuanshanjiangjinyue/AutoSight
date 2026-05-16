
# AutoSight 公网访问快速指南

## 🎉 立即可以体验的方案

---

## 📱 方案一：局域网访问（最简单）

如果对方在同一 Wi-Fi 下：

**访问地址：** http://192.168.43.135:5000

**说明：** 只能在同一 Wi-Fi 下的设备访问

---

## ☁️ 方案二：Cloudflare Tunnel（推荐，永久免费）

无需公网 IP，无需配置路由器，强烈推荐！

### 步骤 1：安装 Cloudflare Tunnel

```bash
brew install cloudflared
```

### 步骤 2：运行临时隧道（无需注册，立即使用）

```bash
cloudflared tunnel --url http://localhost:5000
```

运行后会给你一个类似这样的地址：
- `https://odd-dry-poem-marketing.trycloudflare.com`

把这个地址发给朋友，他们就可以访问了！

### （可选）步骤 3：永久配置（需要域名）

如果你有自己的域名：

```bash
# 1. 登录
cloudflared tunnel login

# 2. 创建隧道
cloudflared tunnel create auto-sight

# 3. 绑定域名
cloudflared tunnel route dns auto-sight your-domain.com

# 4. 运行隧道
cloudflared tunnel --url http://localhost:5000
```

---

## 🚀 方案三：使用 ngrok（简单，免费）

### 步骤 1：安装 ngrok

```bash
brew install ngrok
```

### 步骤 2：运行隧道

```bash
ngrok http 5000
```

会给你一个地址，例如：
- `https://abc123.ngrok-free.app`

---

## 📝 使用公网部署脚本

运行交互式脚本选择方案：

```bash
./deploy-public.sh
```

---

## ✅ 当前服务状态

| 服务 | 地址 | 状态 |
|------|------|------|
| 后端应用 | http://localhost:5000 | ✅ 运行中 |
| 反向代理 | http://localhost:8080 | ✅ 运行中 |
| 局域网 | http://192.168.43.135:5000 | ✅ 可用 |

---

## 👤 测试账号

| 账号 | 密码 | 权限 |
|------|------|------|
| admin | 123456 | 全部功能 |
| test_user | 123456 | 仅供需看板 |

---

## 📚 详细文档

完整部署文档请查看：[DEPLOYMENT.md](file:///Users/lawrence/Documents/Auto-Analysis/DEPLOYMENT.md)

