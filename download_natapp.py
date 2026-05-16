#!/usr/bin/env python3
"""下载 NATAPP 客户端 - 带Headers"""

import urllib.request
import os

def download_natapp():
    url = "http://download.natapp.cn/assets/downloads/clients/3_0_3/natapp_darwin_arm64/natapp"
    output_path = os.path.expanduser("~/natapp/natapp")
    
    print(f"正在下载 NATAPP...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Apple Silicon Mac OS X) AppleWebKit/605.1.15',
        'Accept': '*/*',
    }
    
    try:
        print("下载中...")
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
            
        with open(output_path, 'wb') as f:
            f.write(data)
        
        os.chmod(output_path, 0o755)
        size = os.path.getsize(output_path)
        
        print(f"✅ 下载成功!")
        print(f"路径: {output_path}")
        print(f"大小: {size:,} bytes")
        
        with open(output_path, 'rb') as f:
            header = f.read(2)
            if header == b'MZ' or header == b'#!':
                print("✅ 文件验证成功")
                return True
            else:
                print(f"⚠️  文件头: {header}，可能有问题")
                return False
                
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

if __name__ == "__main__":
    download_natapp()
