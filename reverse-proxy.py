
#!/usr/bin/env python3
"""
AutoSight 简单反向代理（本地开发用）
适用于无法安装 Nginx 的环境
"""

import http.server
import socketserver
import urllib.request
import urllib.error
from http.client import HTTPResponse
from io import BytesIO
import sys

PORT = 80
BACKEND_URL = "http://127.0.0.1:5000"


class ReverseProxyHandler(http.server.SimpleHTTPRequestHandler):
    """反向代理处理类"""
    
    def do_GET(self):
        self.proxy_request('GET')
    
    def do_POST(self):
        self.proxy_request('POST')
    
    def do_PUT(self):
        self.proxy_request('PUT')
    
    def do_DELETE(self):
        self.proxy_request('DELETE')
    
    def do_OPTIONS(self):
        self.proxy_request('OPTIONS')
    
    def proxy_request(self, method):
        try:
            # 构建后端请求
            url = f"{BACKEND_URL}{self.path}"
            headers = {k: v for k, v in self.headers.items() if k not in ('Host', 'Content-Length')}
            
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # 创建请求
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            
            # 发送请求到后端
            with urllib.request.urlopen(req, timeout=300) as response:
                # 设置响应状态码
                self.send_response(response.status)
                
                # 转发响应头
                for k, v in response.getheaders():
                    if k.lower() not in ('content-encoding', 'transfer-encoding', 'connection'):
                        self.send_header(k, v)
                
                self.end_headers()
                
                # 转发响应内容
                self.wfile.write(response.read())
                
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for k, v in e.headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_error(502, f"代理错误: {str(e)}")
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = PORT
    
    try:
        with socketserver.TCPServer(("", port), ReverseProxyHandler) as httpd:
            print(f"\n🚀 AutoSight 反向代理已启动")
            print("=" * 50)
            print(f"📍 代理地址: http://localhost:{port}")
            print(f"🔗 后端地址: {BACKEND_URL}")
            print(f"\n⚠️  注意: 请确保后端应用已在 {BACKEND_URL} 运行")
            print("\n按 Ctrl+C 停止代理")
            print("=" * 50)
            httpd.serve_forever()
            
    except PermissionError:
        print(f"\n❌ 端口 {port} 需要管理员权限")
        print(f"💡 尝试使用 sudo 运行，或指定其他端口:")
        print(f"   sudo python3 reverse-proxy.py")
        print(f"   python3 reverse-proxy.py 8080\n")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"\n❌ 端口 {port} 已被占用")
            print(f"💡 请使用其他端口: python3 reverse-proxy.py 8080\n")
        else:
            raise
    except KeyboardInterrupt:
        print("\n\n✅ 反向代理已停止\n")


if __name__ == "__main__":
    main()

