#!/usr/bin/env python3
"""下载 cloudflared 工具 - ARM64 版本"""

import urllib.request
import json
import os

def get_latest_version():
    """获取 cloudflared 最新版本号"""
    url = "https://api.github.com/repos/cloudflare/cloudflared/releases/latest"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data['tag_name'].replace('v', '')
    except Exception as e:
        print(f"获取版本失败: {e}")
        return "2024.8.3"

def download_cloudflared():
    version = get_latest_version()
    url = f"https://github.com/cloudflare/cloudflared/releases/download/{version}/cloudflared-darwin-arm64"
    output_path = "/tmp/cloudflared"
    
    print(f"正在下载 cloudflared v{version} (ARM64)...")
    
    try:
        print(f"URL: {url}")
        urllib.request.urlretrieve(url, output_path)
        os.chmod(output_path, 0o755)
        print(f"✅ 下载成功: {output_path}")
        print(f"文件大小: {os.path.getsize(output_path)} bytes")
        
        with open(output_path, 'rb') as f:
            header = f.read(2)
            if header == b'MZ':
                print("✅ 二进制文件验证成功")
                return True
            else:
                print(f"⚠️ 文件可能损坏，文件头: {header}")
                return False
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

if __name__ == "__main__":
    download_cloudflared()
