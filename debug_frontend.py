import requests
import json

# 模拟浏览器请求
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# 1. 先获取登录页面
print("=== 1. 获取登录页面 ===")
r = requests.get('http://localhost:5000/', headers=headers)
print(f"状态: {r.status_code}")

# 2. 管理员登录
print("\n=== 2. 管理员登录 ===")
login_data = {'username': 'admin', 'password': '123456'}
r = requests.post('http://localhost:5000/api/admin/login', json=login_data, headers=headers)
print(f"状态: {r.status_code}")
if r.ok:
    data = r.json()
    token = data['token']
    print(f"Token: {token[:20]}...")
    
    # 添加认证头
    headers['Authorization'] = f'Bearer {token}'
    
    # 3. 获取分析数据
    print("\n=== 3. 获取分析数据 ===")
    r = requests.get('http://localhost:5000/api/admin/analytics', headers=headers)
    print(f"状态: {r.status_code}")
    if r.ok:
        analytics = r.json()
        print("分析数据:", json.dumps(analytics, indent=2, ensure_ascii=False))
    
    # 4. 获取每日分析数据
    print("\n=== 4. 获取每日分析数据 ===")
    r = requests.get('http://localhost:5000/api/admin/analytics/daily', headers=headers)
    print(f"状态: {r.status_code}")
    if r.ok:
        daily = r.json()
        print("每日数据:", json.dumps(daily, indent=2, ensure_ascii=False))
    
    # 5. 获取用户列表
    print("\n=== 5. 获取用户列表 ===")
    r = requests.get('http://localhost:5000/api/admin/users', headers=headers)
    print(f"状态: {r.status_code}")
    if r.ok:
        users = r.json()
        print(f"用户数量: {len(users)}")
    
    # 6. 获取用户统计
    print("\n=== 6. 获取用户统计 ===")
    r = requests.get('http://localhost:5000/api/admin/users/1/stats', headers=headers)
    print(f"状态: {r.status_code}")
    if r.ok:
        stats = r.json()
        print("用户统计:", json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 7. 获取日志
    print("\n=== 7. 获取操作日志 ===")
    r = requests.get('http://localhost:5000/api/admin/logs', headers=headers)
    print(f"状态: {r.status_code}")
    if r.ok:
        logs = r.json()
        print(f"日志数量: {len(logs)}")
    
    # 8. 访问管理员页面
    print("\n=== 8. 访问管理员页面 ===")
    r = requests.get('http://localhost:5000/admin', headers=headers)
    print(f"状态: {r.status_code}")
    print(f"页面长度: {len(r.text)}")
    print(f"页面标题: {r.text[:500]}...")

else:
    print(f"登录失败: {r.text}")