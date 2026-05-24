import requests

# 创建会话来保持cookie
session = requests.Session()

# 步骤1: 访问登录页面获取csrf token（如果需要）
print("步骤1: 访问登录页面")
login_page = session.get('http://localhost:5000/')
print(f"登录页面状态: {login_page.status_code}")

# 步骤2: 管理员登录
print("\n步骤2: 管理员登录")
login_data = {'username': 'admin', 'password': '123456'}
login_response = session.post('http://localhost:5000/api/admin/login', json=login_data)
print(f"登录响应状态: {login_response.status_code}")
if login_response.ok:
    data = login_response.json()
    token = data['token']
    print(f"获取到token: {token[:20]}...")
    
    # 设置Authorization header
    session.headers['Authorization'] = f'Bearer {token}'
    
    # 步骤3: 访问admin页面
    print("\n步骤3: 访问管理员页面")
    admin_page = session.get('http://localhost:5000/admin')
    print(f"管理员页面状态: {admin_page.status_code}")
    print(f"页面内容长度: {len(admin_page.text)}")
    
    # 步骤4: 获取分析数据
    print("\n步骤4: 获取分析数据")
    analytics = session.get('http://localhost:5000/api/admin/analytics')
    print(f"分析数据状态: {analytics.status_code}")
    if analytics.ok:
        print("分析数据:", analytics.json())
    
    # 步骤5: 获取用户列表
    print("\n步骤5: 获取用户列表")
    users = session.get('http://localhost:5000/api/admin/users')
    print(f"用户列表状态: {users.status_code}")
    if users.ok:
        user_list = users.json()
        print(f"用户数量: {len(user_list)}")
        for u in user_list:
            print(f"  - {u['username']} ({u['membership_level']})")
    
    # 步骤6: 获取操作日志
    print("\n步骤6: 获取操作日志")
    logs = session.get('http://localhost:5000/api/admin/logs')
    print(f"日志状态: {logs.status_code}")
    if logs.ok:
        log_list = logs.json()
        print(f"日志数量: {len(log_list)}")
        if log_list:
            print("最新日志:")
            for log in log_list[:5]:
                print(f"  {log['created_at']} - {log['username']} - {log['operation_type']}")
    
else:
    print(f"登录失败: {login_response.text}")