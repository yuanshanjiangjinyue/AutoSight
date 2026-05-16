"""
AutoSight 汽配选品工具 - Flask后端服务
轻量级Python后端 + SQLite数据库
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DATABASE = 'autosight.db'
TOKEN_EXPIRY_HOURS = 24

# ==================== 数据库初始化 ====================

def init_db():
    """初始化数据库，创建表和Mock数据"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # 用户表（增强版）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            company_name TEXT,
            membership_level TEXT DEFAULT 'free',
            membership_days INTEGER DEFAULT 0,
            permissions TEXT DEFAULT '["dashboard"]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 添加新字段（如果不存在）
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN company_name TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN membership_level TEXT DEFAULT 'free'")
    except: pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN membership_days INTEGER DEFAULT 0")
    except: pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN permissions TEXT DEFAULT '[\"dashboard\"]'")
    except: pass
    
    # 认证Token表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 品类表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_type TEXT,
            demand_growth REAL,
            supply_growth REAL,
            gap REAL,
            cr5 REAL,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 趋势数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trend_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            demand_value REAL,
            supply_value REAL,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # Mock用户数据（密码都是123456）
    # 权限说明：admin=所有权限，test_user=只有dashboard权限
    mock_users = [
        ('admin', hashlib.sha256('123456'.encode()).hexdigest(), 
         'admin@autosight.com', '138-0013-8000', 'AutoSight科技有限公司', 
         'pro', 180, '["dashboard","blue_ocean","reports","profile"]'),
        ('test_user', hashlib.sha256('123456'.encode()).hexdigest(), 
         'test@autosight.com', '139-1234-5678', '跨境汽配贸易有限公司', 
         'pro', 90, '["dashboard"]'),
        ('xiaowang', hashlib.sha256('123456'.encode()).hexdigest(), 
         'xiaowang@autosight.com', '136-5678-9012', '小王汽配工作室', 
         'free', 0, '["dashboard"]'),
    ]
    
    for user in mock_users:
        cursor.execute('SELECT id FROM users WHERE username = ?', (user[0],))
        result = cursor.fetchone()
        if not result:
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, phone, company_name, membership_level, membership_days, permissions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', user)
        else:
            # 更新现有用户信息
            cursor.execute('''
                UPDATE users SET 
                    email = ?, phone = ?, company_name = ?, 
                    membership_level = ?, membership_days = ?, permissions = ?
                WHERE username = ?
            ''', (user[2], user[3], user[4], user[5], user[6], user[7], user[0]))
    
    # Mock品类数据
    mock_categories = [
        ('新能源车便携充电枪', 'new-energy', 120.0, 35.0, 85.0, 22.0, 'top-blue'),
        ('特斯拉Model 3定制脚垫', 'custom', 87.0, 25.0, 62.0, 18.0, 'top-blue'),
        ('新能源LED智能尾灯', 'new-energy', 71.0, 17.0, 54.0, 18.0, 'blue'),
        ('宠物车载防脏座套', 'pet', 63.0, 18.0, 45.0, 25.0, 'blue'),
        ('800V高压快充转换头', 'new-energy', 45.0, 12.0, 33.0, 28.0, 'blue'),
        ('车载冰箱压缩机', 'new-energy', 58.0, 22.0, 36.0, 31.0, 'blue'),
        ('智能行车记录仪', 'electronics', 42.0, 28.0, 14.0, 35.0, 'blue'),
        ('特斯拉Model Y专用窗帘', 'custom', 95.0, 30.0, 65.0, 20.0, 'top-blue'),
        ('新能源充电桩保护箱', 'new-energy', 55.0, 15.0, 40.0, 27.0, 'blue'),
        ('宠物车载安全笼', 'pet', 48.0, 20.0, 28.0, 29.0, 'blue'),
        ('通用机油滤芯', 'general', 7.0, 21.0, -14.0, 62.0, 'red'),
        ('通用汽车脚垫', 'general', 5.0, 23.0, -18.0, 58.0, 'red'),
        ('普通行车记录仪', 'electronics', 8.0, 25.0, -17.0, 65.0, 'red'),
        ('传统车载充电器', 'general', 3.0, 19.0, -16.0, 70.0, 'red'),
        ('通用车蜡镀膜剂', 'general', 6.0, 22.0, -16.0, 68.0, 'red'),
    ]
    
    for cat in mock_categories:
        cursor.execute('SELECT id FROM categories WHERE name = ?', (cat[0],))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO categories (name, category_type, demand_growth, supply_growth, gap, cr5, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', cat)
    
    # Mock趋势数据（6个月）
    cursor.execute('SELECT COUNT(*) FROM trend_data')
    if cursor.fetchone()[0] == 0:
        trend_data = []
        months = ['1月', '2月', '3月', '4月', '5月', '6月']
        
        for cat_id in range(1, 16):
            base_demand = 10 + (cat_id * 3)
            base_supply = 5 + (cat_id * 1)
            
            for i, month in enumerate(months):
                demand_val = base_demand + (i * 8) + (15 - cat_id) * 2
                supply_val = base_supply + (i * 2)
                trend_data.append((cat_id, month, demand_val, supply_val))
        
        cursor.executemany('''
            INSERT INTO trend_data (category_id, month, demand_value, supply_value)
            VALUES (?, ?, ?, ?)
        ''', trend_data)
    
    conn.commit()
    conn.close()

def get_db():
    """获取数据库连接"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """关闭数据库连接"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ==================== 认证中间件 ====================

def generate_token():
    """生成随机Token"""
    return secrets.token_hex(32)

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_token(token):
    """验证Token是否有效"""
    db = get_db()
    cursor = db.execute('''
        SELECT user_id FROM auth_tokens 
        WHERE token = ? AND expires_at > datetime('now')
    ''', (token,))
    result = cursor.fetchone()
    return result['user_id'] if result else None

def require_auth(f):
    """认证装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': '未提供认证Token'}), 401
        
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Token无效或已过期'}), 401
        
        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated

def require_permission(permission):
    """权限验证装饰器"""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            db = get_db()
            cursor = db.execute('SELECT permissions FROM users WHERE id = ?', (g.user_id,))
            user = cursor.fetchone()
            
            import json
            user_permissions = []
            try:
                user_permissions = json.loads(user['permissions']) if user['permissions'] else []
            except:
                user_permissions = []
            
            if permission not in user_permissions:
                return jsonify({
                    'error': '您没有权限访问此功能',
                    'required': permission,
                    'user_permissions': user_permissions
                }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

# ==================== 用户认证API ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    db = get_db()
    password_hash = hash_password(password)
    
    try:
        db.execute('''
            INSERT INTO users (username, password_hash, email)
            VALUES (?, ?, ?)
        ''', (username, password_hash, email))
        db.commit()
        
        return jsonify({'message': '注册成功'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': '用户名已存在'}), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    db = get_db()
    cursor = db.execute('''
        SELECT id, password_hash FROM users WHERE username = ?
    ''', (username,))
    user = cursor.fetchone()
    
    if not user or user['password_hash'] != hash_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    # 生成Token
    token = generate_token()
    expires_at = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    
    db.execute('''
        INSERT INTO auth_tokens (user_id, token, expires_at)
        VALUES (?, ?, ?)
    ''', (user['id'], token, expires_at))
    db.commit()
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'username': username
        },
        'expires_at': expires_at.isoformat()
    })

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """用户登出"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    db = get_db()
    db.execute('DELETE FROM auth_tokens WHERE token = ?', (token,))
    db.commit()
    return jsonify({'message': '登出成功'})

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """获取当前用户详细信息"""
    db = get_db()
    cursor = db.execute('''
        SELECT id, username, email, phone, company_name, membership_level, membership_days, permissions, created_at 
        FROM users WHERE id = ?
    ''', (g.user_id,))
    user = cursor.fetchone()
    
    import json
    permissions = []
    try:
        permissions = json.loads(user['permissions']) if user['permissions'] else []
    except:
        permissions = []
    
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'phone': user['phone'] or '',
        'company_name': user['company_name'] or '',
        'membership_level': user['membership_level'],
        'membership_days': user['membership_days'],
        'permissions': permissions,
        'created_at': user['created_at']
    })

# ==================== 品类数据API ====================

@app.route('/api/categories', methods=['GET'])
@require_auth
def get_categories():
    """获取所有品类数据"""
    db = get_db()
    filter_type = request.args.get('type', 'all')
    filter_status = request.args.get('status', 'all')
    
    query = 'SELECT * FROM categories WHERE 1=1'
    params = []
    
    if filter_type != 'all':
        query += ' AND category_type = ?'
        params.append(filter_type)
    
    if filter_status != 'all':
        query += ' AND status = ?'
        params.append(filter_status)
    
    query += ' ORDER BY gap DESC'
    
    cursor = db.execute(query, params)
    categories = [dict(row) for row in cursor.fetchall()]
    
    return jsonify(categories)

@app.route('/api/categories/<int:category_id>', methods=['GET'])
@require_auth
def get_category(category_id):
    """获取单个品类详情"""
    db = get_db()
    cursor = db.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
    category = cursor.fetchone()
    
    if not category:
        return jsonify({'error': '品类不存在'}), 404
    
    return jsonify(dict(category))

@app.route('/api/categories/<int:category_id>/trend', methods=['GET'])
@require_auth
def get_category_trend(category_id):
    """获取品类趋势数据"""
    db = get_db()
    cursor = db.execute('''
        SELECT month, demand_value, supply_value 
        FROM trend_data 
        WHERE category_id = ?
        ORDER BY id
    ''', (category_id,))
    
    trend = [dict(row) for row in cursor.fetchall()]
    return jsonify(trend)

@app.route('/api/dashboard/stats', methods=['GET'])
@require_auth
def get_dashboard_stats():
    """获取仪表盘统计数据"""
    db = get_db()
    
    # 总品类数
    cursor = db.execute('SELECT COUNT(*) as count FROM categories')
    total_categories = cursor.fetchone()['count']
    
    # 蓝海品类数
    cursor = db.execute("SELECT COUNT(*) as count FROM categories WHERE status IN ('blue', 'top-blue')")
    blue_ocean_count = cursor.fetchone()['count']
    
    # 平均供需缺口（蓝海品类）
    cursor = db.execute("SELECT AVG(gap) as avg_gap FROM categories WHERE status IN ('blue', 'top-blue')")
    avg_gap = cursor.fetchone()['avg_gap'] or 0
    
    # 平均需求增速（蓝海品类）
    cursor = db.execute("SELECT AVG(demand_growth) as avg_demand FROM categories WHERE status IN ('blue', 'top-blue')")
    avg_demand = cursor.fetchone()['avg_demand'] or 0
    
    return jsonify({
        'total_categories': total_categories,
        'blue_ocean_count': blue_ocean_count,
        'avg_gap': round(avg_gap, 1),
        'avg_demand': round(avg_demand, 1)
    })

@app.route('/api/recommendations', methods=['GET'])
@require_auth
@require_permission('blue_ocean')
def get_recommendations():
    """获取蓝海选品推荐"""
    db = get_db()
    limit = request.args.get('limit', 10, type=int)
    
    cursor = db.execute('''
        SELECT * FROM categories 
        WHERE status IN ('blue', 'top-blue') 
        ORDER BY gap DESC, demand_growth DESC
        LIMIT ?
    ''', (limit,))
    
    recommendations = [dict(row) for row in cursor.fetchall()]
    return jsonify(recommendations)

@app.route('/api/blue-ocean', methods=['GET'])
@require_auth
@require_permission('blue_ocean')
def get_blue_ocean():
    """获取蓝海选品完整列表"""
    db = get_db()
    sort_by = request.args.get('sort', 'gap')
    order = request.args.get('order', 'desc')
    category_type = request.args.get('type', 'all')
    
    query = "SELECT * FROM categories WHERE status IN ('blue', 'top-blue')"
    params = []
    
    if category_type != 'all':
        query += " AND category_type = ?"
        params.append(category_type)
    
    if sort_by in ['gap', 'demand_growth', 'supply_growth', 'cr5']:
        order_clause = 'DESC' if order == 'desc' else 'ASC'
        query += f" ORDER BY {sort_by} {order_clause}"
    
    cursor = db.execute(query, params)
    blue_ocean_list = [dict(row) for row in cursor.fetchall()]
    
    return jsonify(blue_ocean_list)

@app.route('/api/categories/<int:category_id>/analysis', methods=['GET'])
@require_auth
@require_permission('blue_ocean')
def get_category_analysis(category_id):
    """获取品类详细分析"""
    db = get_db()
    
    # 获取品类基本信息
    cursor = db.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
    category = cursor.fetchone()
    
    if not category:
        return jsonify({'error': '品类不存在'}), 404
    
    # 获取趋势数据
    cursor = db.execute('''
        SELECT month, demand_value, supply_value 
        FROM trend_data 
        WHERE category_id = ?
        ORDER BY id
    ''', (category_id,))
    trend = [dict(row) for row in cursor.fetchall()]
    
    # 获取相似品类推荐
    cursor = db.execute('''
        SELECT * FROM categories 
        WHERE category_type = ? AND id != ? AND status IN ('blue', 'top-blue')
        ORDER BY gap DESC
        LIMIT 5
    ''', (category['category_type'], category_id))
    similar = [dict(row) for row in cursor.fetchall()]
    
    return jsonify({
        'category': dict(category),
        'trend': trend,
        'similar': similar
    })

@app.route('/api/reports/market', methods=['GET'])
@require_auth
@require_permission('reports')
def get_market_report():
    """获取市场分析报告"""
    db = get_db()
    
    # 按品类类型统计
    cursor = db.execute('''
        SELECT 
            category_type,
            COUNT(*) as count,
            AVG(gap) as avg_gap,
            AVG(demand_growth) as avg_demand,
            AVG(cr5) as avg_cr5
        FROM categories
        WHERE status IN ('blue', 'top-blue')
        GROUP BY category_type
        ORDER BY avg_gap DESC
    ''')
    by_type = [dict(row) for row in cursor.fetchall()]
    
    # 按状态统计
    cursor = db.execute('''
        SELECT 
            status,
            COUNT(*) as count,
            AVG(gap) as avg_gap,
            AVG(demand_growth) as avg_demand
        FROM categories
        GROUP BY status
    ''')
    by_status = [dict(row) for row in cursor.fetchall()]
    
    # TOP 5 蓝海品类
    cursor = db.execute('''
        SELECT * FROM categories
        WHERE status IN ('blue', 'top-blue')
        ORDER BY gap DESC
        LIMIT 5
    ''')
    top5 = [dict(row) for row in cursor.fetchall()]
    
    return jsonify({
        'by_type': by_type,
        'by_status': by_status,
        'top5': top5
    })

@app.route('/api/reports/trends', methods=['GET'])
@require_auth
@require_permission('reports')
def get_trends_report():
    """获取趋势分析报告"""
    db = get_db()
    
    # 获取所有品类的趋势汇总
    cursor = db.execute('''
        SELECT 
            td.month,
            AVG(td.demand_value) as avg_demand,
            AVG(td.supply_value) as avg_supply
        FROM trend_data td
        GROUP BY td.month
        ORDER BY td.id
    ''')
    overall_trend = [dict(row) for row in cursor.fetchall()]
    
    # 按品类类型分别统计
    cursor = db.execute('''
        SELECT 
            c.category_type,
            td.month,
            AVG(td.demand_value) as avg_demand,
            AVG(td.supply_value) as avg_supply
        FROM trend_data td
        JOIN categories c ON td.category_id = c.id
        GROUP BY c.category_type, td.month
        ORDER BY td.id
    ''')
    by_type = {}
    for row in cursor.fetchall():
        cat_type = row['category_type']
        if cat_type not in by_type:
            by_type[cat_type] = []
        by_type[cat_type].append({
            'month': row['month'],
            'avg_demand': row['avg_demand'],
            'avg_supply': row['avg_supply']
        })
    
    return jsonify({
        'overall': overall_trend,
        'by_type': by_type
    })

# ==================== 静态文件服务 ====================

@app.route('/')
def serve_index():
    """服务登录页面"""
    return app.send_static_file('login.html')

@app.route('/dashboard')
def serve_dashboard():
    """服务仪表盘页面"""
    return app.send_static_file('dashboard.html')

@app.route('/profile')
def serve_profile():
    """服务用户详情页面"""
    return app.send_static_file('profile.html')

@app.route('/blue-ocean')
def serve_blue_ocean():
    """服务蓝海选品页面"""
    return app.send_static_file('blue-ocean.html')

@app.route('/category/<int:category_id>')
def serve_category_detail(category_id):
    """服务品类详情页面"""
    return app.send_static_file('category-detail.html')

@app.route('/reports')
def serve_reports():
    """服务数据报表页面"""
    return app.send_static_file('reports.html')

# ==================== 初始化 ====================

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print("正在初始化数据库...")
        init_db()
        print("数据库初始化完成！")
    else:
        print("数据库已存在，检查并补充数据...")
        init_db()
    
    print("\n🏠 AutoSight 汽配选品工具已启动！")
    print("=" * 50)
    print("📍 访问地址: http://localhost:5000")
    print("👤 测试账号: admin / 123456")
    print("👤 测试账号: test_user / 123456")
    print("👤 测试账号: xiaowang / 123456")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
