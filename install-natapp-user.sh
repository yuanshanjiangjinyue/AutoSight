#!/bin/sh
# NATAPP 安装脚本 - 修改版（安装到用户目录）

set -e

NATAPP_VERSION="3.0.3"
INSTALL_DIR="$HOME/natapp"
NATAPP_SCRIPT_BASE="https://natapp.cn"
AUTHTOKEN="0bc5046deb6ce1c4"
KEY="6561"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { printf '%s[natapp]%s %s\n' "$CYAN"   "$NC" "$*"; }
success() { printf '%s[natapp]%s %s\n' "$GREEN"  "$NC" "$*"; }
warn()    { printf '%s[natapp]%s %s\n' "$YELLOW" "$NC" "$*"; }
error()   { printf '%s[natapp]%s %s\n' "$RED"    "$NC" "$*" >&2; exit 1; }

detect_os() {
    case "$(uname -s)" in
        Linux*)
            if [ -f /system/build.prop ] || command -v getprop >/dev/null 2>&1; then
                echo "android"
            else
                echo "linux"
            fi ;;
        Darwin*)  echo "darwin" ;;
        FreeBSD*) echo "freebsd" ;;
        *)        error "不支持的操作系统: $(uname -s)" ;;
    esac
}

detect_arch() {
    local machine
    machine="$(uname -m)"
    case "$machine" in
        x86_64|amd64)    echo "amd64" ;;
        i?86|i386)       echo "386" ;;
        aarch64|arm64)   echo "arm64" ;;
        armv7*|armv6*)   echo "arm" ;;
        mips64le)        echo "mips64le" ;;
        mipsle|mipsel)   echo "mipsle_compress" ;;
        mips)            echo "mips_compress" ;;
        *)               error "暂不支持的 CPU 架构: $machine" ;;
    esac
}

get_download_url() {
    local os arch
    os="$1"
    arch="$2"
    case "${os}_${arch}" in
        "darwin_amd64")    echo "http://download.natapp.cn/assets/downloads/clients/3_0_3/natapp_darwin_amd64/natapp" ;;
        "darwin_arm64")    echo "http://download.natapp.cn/assets/downloads/clients/3_0_3/natapp_darwin_arm64/natapp" ;;
        "linux_amd64")     echo "http://download.natapp.cn/assets/downloads/clients/3_0_3/natapp_linux_amd64/natapp" ;;
        "linux_arm64")     echo "http://download.natapp.cn/assets/downloads/clients/3_0_3/natapp_linux_arm64/natapp" ;;
        "linux_arm")      echo "http://download.natapp.cn/assets/downloads/clients/3_0_3/natapp_linux_arm/natapp" ;;
        *)                error "暂不支持: $os / $arch" ;;
    esac
}

download_file() {
    local url="$1"
    local dest="$2"
    
    info "正在下载..."
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$dest" || error "下载失败"
    elif command -v wget >/dev/null 2>&1; then
        wget -q "$url" -O "$dest" || error "下载失败"
    else
        error "需要 curl 或 wget"
    fi
}

os="$(detect_os)"
arch="$(detect_arch)"
info "检测到系统: $os / $arch"

mkdir -p "$INSTALL_DIR"

url="$(get_download_url "$os" "$arch")"
if [ -n "$KEY" ]; then
    case "$url" in
        *[\?]*) url="${url}&key=${KEY}&authtoken=${AUTHTOKEN}" ;;
        *)      url="${url}?key=${KEY}&authtoken=${AUTHTOKEN}" ;;
    esac
fi

dest_file="$INSTALL_DIR/natapp"
download_file "$url" "$dest_file"
chmod +x "$dest_file"

info "下载完成!"
success "安装成功!"

echo ""
echo "启动隧道:"
echo "  $dest_file -authtoken=$AUTHTOKEN"
echo ""
echo "或者直接运行:"
echo "  cd $INSTALL_DIR && ./natapp"
echo ""

cat > "$INSTALL_DIR/start.sh" << EOF
#!/bin/sh
exec "$INSTALL_DIR/natapp" -authtoken=$AUTHTOKEN
EOF
chmod +x "$INSTALL_DIR/start.sh"
echo "已创建启动脚本: $INSTALL_DIR/start.sh"
