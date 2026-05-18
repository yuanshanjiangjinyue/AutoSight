#!/usr/bin/env python3
"""使用 trycloudflare.com API 创建临时隧道"""

import urllib.request
import json
import time
import subprocess
import os
import signal

def start_tunnel(port=5000):
    """使用 cloudflared 直接连接 trycloudflare.com"""
    print(f"正在启动 Cloudflare 临时隧道...")
    print(f"本地端口: {port}")
    print()
    
    cloudflared_path = "/tmp/cloudflared"
    
    if not os.path.exists(cloudflared_path):
        print("❌ cloudflared 未找到，正在下载...")
        if not download_cloudflared():
            print("\n无法下载 cloudflared，请手动安装：")
            print("brew install cloudflared")
            return None
    else:
        print(f"✅ 找到 cloudflared: {cloudflared_path}")
    
    try:
        print("\n正在启动隧道...")
        print("=" * 60)
        
        process = subprocess.Popen(
            [cloudflared_path, "tunnel", "--url", f"http://localhost:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        tunnel_url = None
        for line in process.stdout:
            print(line.rstrip())
            
            if "trycloudflare.com" in line:
                parts = line.split("trycloudflare.com")
                if len(parts) > 1:
                    url_part = parts[1].split()[0].strip()
                    tunnel_url = f"https://{url_part}trycloudflare.com"
            
            if "Your quick Tunnel has been created!" in line or \
               ("https://" in line and "trycloudflare" in line):
                if not tunnel_url:
                    tunnel_url = extract_url(line)
        
        if tunnel_url:
            print("\n" + "=" * 60)
            print("🎉 隧道创建成功！")
            print(f"\n📎 公网访问地址: {tunnel_url}")
            print("\n⚠️  注意: 此链接为临时链接，关闭终端后将失效")
            print("   按 Ctrl+C 停止隧道")
            print("=" * 60)
            
            return process
        else:
            print("\n等待获取访问地址...")
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n\n正在停止隧道...")
        process.terminate()
        return None
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        return None

def extract_url(line):
    """从输出行中提取 URL"""
    import re
    url_pattern = r'https://[a-z0-9-]+\.trycloudflare\.com'
    match = re.search(url_pattern, line)
    return match.group(0) if match else None

def download_cloudflared():
    """下载 cloudflared ARM64 版本"""
    import platform
    
    version = "2025.1.0"
    url = f"https://github.com/cloudflare/cloudflared/releases/download/{version}/cloudflared-darwin-arm64"
    output_path = "/tmp/cloudflared"
    
    print(f"正在下载 cloudflared v{version}...")
    
    try:
        urllib.request.urlretrieve(url, output_path)
        os.chmod(output_path, 0o755)
        print(f"✅ 下载成功")
        
        with open(output_path, 'rb') as f:
            header = f.read(2)
            if header == b'MZ':
                print("✅ 二进制文件验证成功")
                return True
        
        return False
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  AutoSight 公网访问工具")
    print("=" * 60)
    print()
    
    start_tunnel(5000)
