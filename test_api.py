import requests

# 模拟登录
login_data = {'username': 'admin', 'password': '123456'}
response = requests.post('http://localhost:5000/api/admin/login', json=login_data)
print('登录响应:', response.status_code)
if response.ok:
    data = response.json()
    print('Token:', data['token'])
    print('用户:', data['user'])
    
    # 测试获取用户列表
    headers = {'Authorization': f'Bearer {data["token"]}'}
    users_response = requests.get('http://localhost:5000/api/admin/users', headers=headers)
    print('\n用户列表响应:', users_response.status_code)
    if users_response.ok:
        users = users_response.json()
        print('用户数量:', len(users))
        for user in users:
            print(f"  - {user['id']}: {user['username']} ({user['membership_level']})")
    
    # 测试获取日志
    logs_response = requests.get('http://localhost:5000/api/admin/logs', headers=headers)
    print('\n日志响应:', logs_response.status_code)
    if logs_response.ok:
        logs = logs_response.json()
        print('日志数量:', len(logs))

    # 测试获取分析数据
    analytics_response = requests.get('http://localhost:5000/api/admin/analytics', headers=headers)
    print('\n分析数据响应:', analytics_response.status_code)
    if analytics_response.ok:
        analytics = analytics_response.json()
        print('分析数据:', analytics)
