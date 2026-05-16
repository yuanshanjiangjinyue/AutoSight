
# AutoSight 公网访问 - 手动安装指南

## 📋 当前状态

### ✅ 已在运行的服务
- **后端应用**: http://localhost:5000 ✅
- **反向代理**: http://localhost:8080 ✅
- **局域网访问**: http://192.168.43.135:5000 ✅

---

## 🚀 Cloudflare Tunnel 安装步骤

### 方法一：使用 Homebrew（推荐）

```bash
# 1. 安装 Homebrew（如果没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装 cloudflared
brew install cloudflare/cloudflare/cloudflared

# 3. 启动隧道
cloudflared tunnel --url http://localhost:5000
```

### 方法二：手动下载

1. 访问 https://github.com/cloudflare/cloudflared/releases/latest
2. 下载 `cloudflared-darwin-arm64.tgz` (M系列Mac)
   或 `cloudflared-darwin-amd64.tgz` (Intel Mac)
3. 解压并安装到 PATH

### 方法三：使用安装脚本（自动检测并安装）

```bash
# 复制此命令到终端运行
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && brew install cloudflare/cloudflare/cloudflared && cloudflared tunnel --url http://localhost:5000
```

---

## 🔧 一键启动脚本

我已经为你准备好了启动脚本：

### 1. 公网访问脚本
```bash
./deploy-public.sh
```
选择选项 1 即可自动安装并启动。

### 2. 快速启动 Cloudflare（如果已安装）
```bash
cloudflared tunnel --url http://localhost:5000
```

---

## 📝 预期输出

启动成功后，你会看到类似这样的信息：

```
2024-01-01T00:00:00Z INF Requesting new quick Tunnel on trycloudflare.com endpoint
2024-01-01T00:00:00Z INF +------------------------------------------------------------------+
2024-01-01T00:00:00Z INF |  Your quick Tunnel has been created!                            |
2024-01-01T00:00:00Z INF |  You can now update it with: cloudflared tunnel update <tunnel>  |
2024-01-01T00:00:00Z INF +------------------------------------------------------------------+
2024-01-01T00:00:00Z INF |  URI:                     http://localhost:5000                 |
2024-01-01T00:00:00Z INF |  Conured to:              https://random-name.trycloudflare.com |
2024-01-01T00:00:00Z INF +------------------------------------------------------------------+
```

**复制 `https://random-name.trycloudflare.com` 这个地址，发给你的朋友即可访问！**

---

## ⚠️ 注意事项

1. **临时链接**: 使用 `--url` 参数的链接是临时的，关闭终端后失效
2. **永久链接**: 如果需要永久链接，需要：
   - 注册 Cloudflare 账号
   - 创建命名的 Tunnel
   - 绑定域名

3. **网络要求**: 确保你的网络可以访问 Cloudflare

---

## 🎯 快速测试清单

在运行之前，确认以下几点：

- [ ] 后端应用运行在 http://localhost:5000 ✅
- [ ] 可以访问 http://localhost:5000 查看登录页面 ✅
- [ ] 测试账号：admin / 123456 ✅

---

## 💡 常见问题

### Q: 启动失败，显示 "command not found: cloudflared"
**A**: cloudflared 未安装或未添加到 PATH。重新执行安装步骤。

### Q: 启动成功但无法访问
**A**: 检查防火墙设置，确保允许 outgoing 连接。

### Q: 链接有效期是多久？
**A**: 使用 `--url` 参数的临时链接，关闭终端后失效。
    需要永久链接请参考 DEPLOYMENT.md 配置命名隧道。

---

## 📞 获取帮助

查看详细文档：
- [DEPLOYMENT.md](file:///Users/lawrence/Documents/Auto-Analysis/DEPLOYMENT.md) - 完整部署指南
- [PUBLIC_GUIDE.md](file:///Users/lawrence/Documents/Auto-Analysis/PUBLIC_GUIDE.md) - 公网访问指南

---

**准备好后，打开终端运行：**
```bash
cloudflared tunnel --url http://localhost:5000
```

然后把生成的链接发给你的朋友即可！🚀

