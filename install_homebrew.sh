#!/bin/bash
# Homebrew 安装脚本（带镜像支持）

echo "========================================"
echo "  Homebrew 安装程序"
echo "========================================"
echo ""

# 检查是否已安装
if command -v brew &> /dev/null; then
    echo "✅ Homebrew 已安装"
    brew --version
    exit 0
fi

echo "开始安装 Homebrew..."
echo ""

# 方法1: 官方源
install_official() {
    echo "尝试官方源安装..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    return $?
}

# 方法2: Gitee 镜像
install_gitee() {
    echo "尝试 Gitee 镜像安装..."
    /bin/bash -c "$(curl -fsSL https://gitee.com/ineo6/homebrew-install/raw/master/install.sh)"
    return $?
}

# 方法3: 清华大学镜像
install_tsinghua() {
    echo "尝试清华大学镜像安装..."
    export HOMEBREW_API_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles/api"
    export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles"
    export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/homebrew-git"
    export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/homebrew-git"
    
    git clone --depth=1 https://mirrors.tuna.tsinghua.edu.cn/homebrew.git /opt/homebrew
    return $?
}

# 尝试安装
if install_official; then
    echo ""
    echo "✅ 官方源安装成功！"
    exit 0
fi

echo ""
echo "官方源安装失败，尝试镜像..."

if install_gitee; then
    echo ""
    echo "✅ Gitee 镜像安装成功！"
    exit 0
fi

echo ""
echo "Gitee 镜像失败，尝试清华大学镜像..."

if install_tsinghua; then
    echo ""
    echo "✅ 清华大学镜像安装成功！"
    echo ""
    echo "请将以下命令添加到你的 shell 配置文件中 (~/.zshrc 或 ~/.bash_profile):"
    echo '  export PATH="/opt/homebrew/bin:$PATH"'
    exit 0
fi

echo ""
echo "❌ 所有安装方式都失败了"
echo ""
echo "请手动下载安装："
echo "  1. 浏览器访问: https://brew.sh/"
echo "  2. 按照页面说明手动安装"
