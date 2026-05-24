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
import json
from functools import wraps

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
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
    except: pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
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
    
    # 订单表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id TEXT NOT NULL,
            amount REAL NOT NULL,
            order_no TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 品类浏览记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS category_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # 报表生成记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 操作日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            description TEXT,
            ip_address TEXT,
            device_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 用户会话表（记录登录时间和停留时长）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            login_time TIMESTAMP NOT NULL,
            logout_time TIMESTAMP,
            duration INTEGER DEFAULT 0,
            ip_address TEXT,
            device_info TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Mock用户数据（密码都是123456）
    # 权限说明：admin=所有权限，test_user=只有dashboard权限
    mock_users = [
        ('admin', hashlib.sha256('123456'.encode()).hexdigest(), 
         'admin@autosight.com', '138-0013-8000', 'AutoSight科技有限公司', 
         'pro', 180, '["dashboard","blue_ocean","reports","profile","admin"]'),
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
    
    # Mock操作日志数据
    cursor.execute('SELECT COUNT(*) FROM operation_logs')
    if cursor.fetchone()[0] == 0:
        import random
        import datetime
        
        operation_types = ['login', 'view', 'search', 'export', 'upgrade', 'logout']
        descriptions = {
            'login': '用户登录成功',
            'view': ['查看蓝海选品列表', '查看品类详情', '查看仪表盘', '查看数据报表'],
            'search': ['搜索新能源配件', '筛选蓝海品类', '搜索特斯拉配件', '搜索宠物车载'],
            'export': ['导出蓝海品类报告', '导出数据报表', '导出趋势分析'],
            'upgrade': '升级到专业版',
            'logout': '用户登出'
        }
        devices = ['Chrome Windows', 'Chrome Mac', 'Safari Mac', 'Mobile Safari', 'Firefox Windows', 'Edge Windows']
        ips = ['192.168.1.100', '192.168.1.101', '192.168.1.102', '192.168.1.103', '192.168.1.104', '192.168.1.105']
        usernames = ['admin', 'test_user', 'xiaowang']
        
        logs = []
        base_time = datetime.datetime.now()
        
        for day_offset in range(7):
            for hour_offset in range(24):
                if random.random() > 0.6:
                    user_id = random.randint(1, 3)
                    op_type = random.choice(operation_types)
                    desc = descriptions[op_type]
                    if isinstance(desc, list):
                        desc = random.choice(desc)
                    log_time = base_time - datetime.timedelta(days=day_offset, hours=hour_offset)
                    logs.append((user_id, usernames[user_id-1], op_type, desc, random.choice(ips), random.choice(devices), log_time))
        
        cursor.executemany('''
            INSERT INTO operation_logs (user_id, username, operation_type, description, ip_address, device_info, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', logs)
    
    # Mock用户会话数据
    cursor.execute('SELECT COUNT(*) FROM user_sessions')
    if cursor.fetchone()[0] == 0:
        sessions = []
        base_time = datetime.datetime.now()
        
        for day_offset in range(7):
            for _ in range(random.randint(20, 40)):
                user_id = random.randint(1, 3)
                login_time = base_time - datetime.timedelta(days=day_offset, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                duration = random.randint(60, 3600)
                logout_time = login_time + datetime.timedelta(seconds=duration)
                sessions.append((user_id, login_time, logout_time, duration, random.choice(ips), random.choice(devices)))
        
        cursor.executemany('''
            INSERT INTO user_sessions (user_id, login_time, logout_time, duration, ip_address, device_info)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sessions)
    
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


def log_operation(user_id, username, operation_type, description=''):
    """记录用户操作日志"""
    try:
        db = get_db()
        ip_address = request.remote_addr if hasattr(request, 'remote_addr') else None
        user_agent = request.headers.get('User-Agent') if hasattr(request, 'headers') else None
        device_info = user_agent[:255] if user_agent else None
        
        db.execute('''
            INSERT INTO operation_logs 
            (user_id, username, operation_type, description, ip_address, device_info, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, operation_type, description, ip_address, device_info, datetime.now()))
        db.commit()
    except Exception as e:
        print(f"Failed to log operation: {e}")


def start_user_session(user_id, username):
    """开始用户会话"""
    try:
        db = get_db()
        ip_address = request.remote_addr if hasattr(request, 'remote_addr') else None
        user_agent = request.headers.get('User-Agent') if hasattr(request, 'headers') else None
        device_info = user_agent[:255] if user_agent else None
        
        cursor = db.execute('''
            INSERT INTO user_sessions 
            (user_id, username, login_time, ip_address, device_info)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, datetime.now(), ip_address, device_info))
        db.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Failed to start session: {e}")
        return None


def end_user_session(user_id):
    """结束用户会话并计算停留时长"""
    try:
        db = get_db()
        cursor = db.execute('''
            SELECT id, login_time, username FROM user_sessions 
            WHERE user_id = ? AND logout_time IS NULL 
            ORDER BY login_time DESC LIMIT 1
        ''', (user_id,))
        session = cursor.fetchone()
        
        if session:
            login_time = session['login_time']
            if isinstance(login_time, str):
                login_time = datetime.strptime(login_time, '%Y-%m-%d %H:%M:%S')
            duration = int((datetime.now() - login_time).total_seconds())
            
            db.execute('''
                UPDATE user_sessions 
                SET logout_time = ?, duration = ? 
                WHERE id = ?
            ''', (datetime.now(), duration, session['id']))
            db.commit()
            
            # 记录登出操作
            duration_str = format_duration_seconds(duration)
            log_operation(user_id, session['username'], 'logout', f'会话时长: {duration_str}')
    except Exception as e:
        print(f"Failed to end session: {e}")


def format_duration_seconds(seconds):
    """格式化秒数为可读时长"""
    if seconds < 60:
        return f'{seconds}秒'
    elif seconds < 3600:
        minutes = seconds // 60
        return f'{minutes}分钟'
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f'{hours}小时{minutes}分钟'


# ==================== 选品分析工具函数 ====================

def estimate_sales(demand_growth, gap):
    """预估月销量"""
    base_sales = 1000
    demand_factor = 1 + (demand_growth / 100)
    gap_factor = 1 + (gap / 100)
    estimated = int(base_sales * demand_factor * gap_factor)
    return max(500, min(50000, estimated))


def estimate_revenue(sales, gap):
    """预估月收入（美元）"""
    avg_price = 25 + (gap * 0.5)
    return int(sales * avg_price * 0.6)


def calculate_competition(cr5, supply_growth):
    """计算竞争难度分数 (0-100)，越低竞争越小"""
    cr5_score = min(cr5, 100)
    supply_score = min(supply_growth, 100)
    score = (cr5_score * 0.6) + (supply_score * 0.4)
    return max(0, min(100, int(score)))


def calculate_profit(gap, demand_growth, cr5):
    """计算利润潜力分数 (0-100)"""
    gap_score = min(gap * 1.5, 50)
    demand_score = min(demand_growth * 0.8, 30)
    cr5_score = max((100 - cr5) * 0.2, 0)
    return min(100, int(gap_score + demand_score + cr5_score))


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
        SELECT id, password_hash, status FROM users WHERE username = ?
    ''', (username,))
    user = cursor.fetchone()
    
    if not user or user['password_hash'] != hash_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    # 检查用户状态
    if user['status'] == 'disabled':
        return jsonify({'error': '账号已被禁用，请联系管理员'}), 403
    
    # 生成Token
    token = generate_token()
    expires_at = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    
    db.execute('''
        INSERT INTO auth_tokens (user_id, token, expires_at)
        VALUES (?, ?, ?)
    ''', (user['id'], token, expires_at))
    db.commit()
    
    # 记录登录操作和会话
    log_operation(user['id'], username, 'login', '用户登录成功')
    start_user_session(user['id'], username)
    
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
    # 结束用户会话
    end_user_session(g.user_id)
    
    # 删除Token
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
    
    # 记录操作
    cursor = db.execute('SELECT username FROM users WHERE id = ?', (g.user_id,))
    user = cursor.fetchone()
    username = user['username'] if user else ''
    desc = f'查看品类列表，筛选条件: type={filter_type}, status={filter_status}'
    log_operation(g.user_id, username, 'view', desc)
    
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
    
    # 记录操作
    cursor = db.execute('SELECT username FROM users WHERE id = ?', (g.user_id,))
    user = cursor.fetchone()
    username = user['username'] if user else ''
    log_operation(g.user_id, username, 'view', f'查看品类详情: {category["category_name"]}')
    
    return jsonify(dict(category))

@app.route('/api/categories/search', methods=['GET'])
@require_auth
def search_categories():
    """搜索品类"""
    db = get_db()
    keyword = request.args.get('keyword', '')
    
    if not keyword:
        return jsonify([])
    
    cursor = db.execute('''
        SELECT * FROM categories 
        WHERE category_name LIKE ? OR category_type LIKE ?
        ORDER BY gap DESC
    ''', (f'%{keyword}%', f'%{keyword}%'))
    categories = [dict(row) for row in cursor.fetchall()]
    
    # 记录搜索操作
    cursor = db.execute('SELECT username FROM users WHERE id = ?', (g.user_id,))
    user = cursor.fetchone()
    username = user['username'] if user else ''
    log_operation(g.user_id, username, 'search', f'搜索品类: {keyword}')
    
    return jsonify(categories)

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
    """获取蓝海选品完整列表（高级筛选）"""
    db = get_db()
    sort_by = request.args.get('sort', 'gap')
    order = request.args.get('order', 'desc')
    category_type = request.args.get('type', 'all')
    status_filter = request.args.get('status', 'all')
    min_gap = request.args.get('min_gap', type=float)
    max_gap = request.args.get('max_gap', type=float)
    min_demand = request.args.get('min_demand', type=float)
    max_demand = request.args.get('max_demand', type=float)
    min_supply = request.args.get('min_supply', type=float)
    max_supply = request.args.get('max_supply', type=float)
    min_cr5 = request.args.get('min_cr5', type=float)
    max_cr5 = request.args.get('max_cr5', type=float)
    keyword = request.args.get('keyword', '')
    
    query = "SELECT * FROM categories WHERE 1=1"
    params = []
    
    if status_filter == 'all':
        query += " AND status IN ('blue', 'top-blue')"
    else:
        query += " AND status = ?"
        params.append(status_filter)
    
    if category_type != 'all':
        query += " AND category_type = ?"
        params.append(category_type)
    
    if keyword:
        query += " AND (name LIKE ? OR category_type LIKE ?)"
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    
    if min_gap is not None:
        query += " AND gap >= ?"
        params.append(min_gap)
    
    if max_gap is not None:
        query += " AND gap <= ?"
        params.append(max_gap)
    
    if min_demand is not None:
        query += " AND demand_growth >= ?"
        params.append(min_demand)
    
    if max_demand is not None:
        query += " AND demand_growth <= ?"
        params.append(max_demand)
    
    if min_supply is not None:
        query += " AND supply_growth >= ?"
        params.append(min_supply)
    
    if max_supply is not None:
        query += " AND supply_growth <= ?"
        params.append(max_supply)
    
    if min_cr5 is not None:
        query += " AND cr5 >= ?"
        params.append(min_cr5)
    
    if max_cr5 is not None:
        query += " AND cr5 <= ?"
        params.append(max_cr5)
    
    if sort_by in ['gap', 'demand_growth', 'supply_growth', 'cr5', 'id']:
        order_clause = 'DESC' if order == 'desc' else 'ASC'
        query += f" ORDER BY {sort_by} {order_clause}"
    
    cursor = db.execute(query, params)
    blue_ocean_list = [dict(row) for row in cursor.fetchall()]
    
    # 添加预估数据
    for item in blue_ocean_list:
        item['estimated_sales'] = estimate_sales(item['demand_growth'], item['gap'])
        item['estimated_revenue'] = estimate_revenue(item['demand_growth'], item['gap'])
        item['competition_score'] = calculate_competition(item['cr5'], item['supply_growth'])
        item['profit_score'] = calculate_profit(item['gap'], item['demand_growth'], item['cr5'])
    
    # 记录操作
    cursor = db.execute('SELECT username FROM users WHERE id = ?', (g.user_id,))
    user = cursor.fetchone()
    username = user['username'] if user else ''
    desc = f'查看蓝海选品，排序: {sort_by}, 类型: {category_type}'
    log_operation(g.user_id, username, 'view', desc)
    
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

@app.route('/api/reports', methods=['GET'])
@require_auth
@require_permission('reports')
def get_reports():
    db = get_db()
    period = request.args.get('period', '7d')
    
    custom_start = request.args.get('start_date')
    custom_end = request.args.get('end_date')
    
    today = datetime.now()
    if period == 'custom' and custom_start and custom_end:
        start_date = custom_start
        end_date = custom_end
    elif period == '7d':
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif period == '30d':
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif period == '90d':
        start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif period == 'ytd':
        start_date = today.replace(month=1, day=1).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    else:
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    
    cursor = db.execute('''
        SELECT COUNT(*) as total_count, AVG(gap) as avg_gap, AVG(demand_growth) as avg_demand,
               AVG(supply_growth) as avg_supply, AVG(cr5) as avg_cr5
        FROM categories
        WHERE updated_at >= ? AND updated_at <= ? AND status IN ('blue', 'top-blue')
    ''', (start_date, end_date))
    category_stats = dict(cursor.fetchone())
    
    total_demand = round(category_stats['total_count'] * (category_stats['avg_demand'] or 50) / 10, 1)
    
    cursor = db.execute('''
        SELECT COUNT(*) as blue_count FROM categories WHERE status = 'top-blue'
        AND updated_at >= ? AND updated_at <= ?
    ''', (start_date, end_date))
    blue_ocean_count = cursor.fetchone()['blue_count']
    
    avg_cr5 = category_stats['avg_cr5'] or 50
    avg_supply = category_stats['avg_supply'] or 20
    competition_index = round((avg_cr5 * 0.6 + avg_supply * 0.4), 1)
    
    cursor = db.execute('''
        SELECT id, name, gap, demand_growth, supply_growth, cr5, category_type
        FROM categories
        WHERE updated_at >= ? AND updated_at <= ? AND status IN ('blue', 'top-blue')
        ORDER BY gap DESC LIMIT 10
    ''', (start_date, end_date))
    categories = [dict(row) for row in cursor.fetchall()]
    
    cursor = db.execute('''
        SELECT category_type, COUNT(*) as count
        FROM categories
        WHERE updated_at >= ? AND updated_at <= ? AND status IN ('blue', 'top-blue')
        GROUP BY category_type ORDER BY count DESC
    ''', (start_date, end_date))
    category_by_type = [dict(row) for row in cursor.fetchall()]
    
    trend_data = []
    trend_labels = []
    gap_data = []
    competition_data = []
    
    if period == '7d':
        for i in range(6, -1, -1):
            date = (today - timedelta(days=i)).strftime('%m-%d')
            trend_labels.append(date)
            trend_data.append(700 + i * 30)
            gap_data.append(35 + i * 2)
            competition_data.append(40 - i * 2)
    elif period == '30d':
        for i in range(25, -1, -5):
            date = (today - timedelta(days=i)).strftime('%m-%d')
            trend_labels.append(date)
            trend_data.append(750 + (30 - i) * 8)
            gap_data.append(32 + (30 - i) // 5 * 3)
            competition_data.append(45 - (30 - i) // 5 * 3)
    elif period == '90d':
        for i in range(75, -1, -15):
            date = (today - timedelta(days=i)).strftime('%m-%d')
            trend_labels.append(date)
            trend_data.append(700 + (90 - i) * 5)
            gap_data.append(28 + (90 - i) // 15 * 4)
            competition_data.append(50 - (90 - i) // 15 * 4)
    elif period == 'ytd':
        current_month = today.month
        for m in range(1, current_month + 1):
            trend_labels.append(f'{m}月')
            trend_data.append(800 + m * 50)
            gap_data.append(25 + m * 3)
            competition_data.append(55 - m * 4)
    else:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        delta = end_dt - start_dt
        days = delta.days
        if days <= 0:
            days = 1
        step = max(1, days // 6)
        current = start_dt
        idx = 0
        while current <= end_dt:
            trend_labels.append(current.strftime('%m-%d'))
            trend_data.append(750 + idx * 20)
            gap_data.append(30 + idx * 3)
            competition_data.append(45 - idx * 3)
            current += timedelta(days=step)
            idx += 1
            if idx >= 8:
                break
    
    return jsonify({
        'dashboard': {
            'total_demand': f"{total_demand:,.1f}",
            'supply_growth': round(category_stats['avg_supply'] or 8.3, 1),
            'blue_ocean_count': blue_ocean_count,
            'competition_index': f"{competition_index:.1f}"
        },
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'charts': {
            'demand_trend': trend_data,
            'trend_labels': trend_labels,
            'category_distribution': category_by_type,
            'top_categories': categories,
            'gap_trend': gap_data,
            'competition_trend': competition_data
        }
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

@app.route('/api/reports/export', methods=['GET'])
@require_auth
@require_permission('reports')
def export_report():
    """导出市场报告"""
    db = get_db()
    format_type = request.args.get('format', 'csv')
    
    # 记录导出操作
    cursor = db.execute('SELECT username FROM users WHERE id = ?', (g.user_id,))
    user = cursor.fetchone()
    username = user['username'] if user else ''
    log_operation(g.user_id, username, 'export', f'导出市场报告，格式: {format_type}')
    
    # 返回模拟数据
    return jsonify({
        'message': '导出成功',
        'format': format_type,
        'timestamp': datetime.now().isoformat()
    })

# ==================== 订阅管理API ====================

# Mock订阅计划数据
PLANS = {
    'free': {
        'id': 'free',
        'name': '免费版',
        'price': 0,
        'period': 'month',
        'features': ['基础供需数据查看', '5个蓝海品类推荐', '基础报表导出'],
        'limits': {'api_calls': 0, 'reports': 10, 'blue_ocean_view': 5}
    },
    'pro': {
        'id': 'pro',
        'name': '专业版',
        'price': 699,
        'period': 'month',
        'features': ['全部供需数据', '无限蓝海品类推荐', '高级报表导出', '高级筛选功能', 'API接口调用(1000次/月)'],
        'limits': {'api_calls': 1000, 'reports': 100, 'blue_ocean_view': 100}
    },
    'enterprise': {
        'id': 'enterprise',
        'name': '企业版',
        'price': 1999,
        'period': 'month',
        'features': ['全部功能', '无限API调用', '定制化报表', '私有部署支持', '专属客户成功经理', '优先技术支持'],
        'limits': {'api_calls': -1, 'reports': -1, 'blue_ocean_view': -1}
    }
}

@app.route('/api/subscription/plans', methods=['GET'])
@require_auth
def get_subscription_plans():
    """获取所有订阅计划"""
    return jsonify(list(PLANS.values()))

@app.route('/api/subscription/current', methods=['GET'])
@require_auth
def get_current_subscription():
    """获取当前用户的订阅信息"""
    db = get_db()
    
    cursor = db.execute('''
        SELECT membership_level, membership_days, created_at 
        FROM users WHERE id = ?
    ''', (g.user_id,))
    user = cursor.fetchone()
    
    plan = PLANS.get(user['membership_level'], PLANS['free'])
    
    # 计算到期日期（如果是免费版则显示永久有效）
    expires_at = None
    if user['membership_level'] != 'free':
        created_date = datetime.fromisoformat(user['created_at'].replace(' ', 'T'))
        expires_at = created_date + timedelta(days=user['membership_days'])
        expires_at = expires_at.isoformat()
    
    return jsonify({
        'plan': plan,
        'current_level': user['membership_level'],
        'member_since': user['created_at'],
        'expires_at': expires_at,
        'days_remaining': user['membership_days'] if user['membership_level'] != 'free' else None
    })

@app.route('/api/subscription/upgrade', methods=['POST'])
@require_auth
def upgrade_subscription():
    """升级订阅计划"""
    data = request.get_json()
    plan_id = data.get('plan_id')
    
    if plan_id not in PLANS:
        return jsonify({'error': '无效的订阅计划'}), 400
    
    if plan_id == 'free':
        return jsonify({'error': '不能降级到免费版'}), 400
    
    db = get_db()
    plan = PLANS[plan_id]
    
    # 生成订单号
    order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{g.user_id}"
    
    # 记录订单（模拟支付）
    cursor = db.execute('''
        INSERT INTO orders (user_id, plan_id, amount, order_no, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (g.user_id, plan_id, plan['price'], order_no, 'pending'))
    db.commit()
    
    # 模拟支付成功，更新会员信息
    if plan_id == 'pro':
        days = 30
    else:
        days = 30
    
    cursor = db.execute('''
        UPDATE users 
        SET membership_level = ?, membership_days = membership_days + ?
        WHERE id = ?
    ''', (plan_id, days, g.user_id))
    db.commit()
    
    return jsonify({
        'message': '升级成功',
        'order_no': order_no,
        'plan': plan,
        'days_added': days
    })

# ==================== 管理员API ====================

def require_admin(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': '未授权'}), 401
        
        db = get_db()
        cursor = db.execute('SELECT user_id FROM auth_tokens WHERE token = ? AND expires_at > ?', (token, datetime.now()))
        token_data = cursor.fetchone()
        
        if not token_data:
            return jsonify({'error': '无效或过期的Token'}), 401
        
        cursor = db.execute('SELECT permissions FROM users WHERE id = ?', (token_data['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': '用户不存在'}), 401
        
        permissions = []
        try:
            permissions = json.loads(user['permissions']) if user['permissions'] else []
        except:
            permissions = []
        
        if 'admin' not in permissions:
            return jsonify({'error': '无管理员权限'}), 403
        
        g.user_id = token_data['user_id']
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """管理员登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    db = get_db()
    cursor = db.execute('''
        SELECT id, password_hash, permissions FROM users WHERE username = ?
    ''', (username,))
    user = cursor.fetchone()
    
    if not user:
        return jsonify({'error': '用户名或密码错误'}), 401
    
    if user['password_hash'] != hash_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    permissions = []
    try:
        permissions = json.loads(user['permissions']) if user['permissions'] else []
    except:
        permissions = []
    
    if 'admin' not in permissions:
        return jsonify({'error': '无管理员权限'}), 403
    
    token = generate_token()
    expires_at = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    
    db.execute('''
        INSERT INTO auth_tokens (user_id, token, expires_at)
        VALUES (?, ?, ?)
    ''', (user['id'], token, expires_at))
    db.commit()
    
    # 记录登录操作和会话
    log_operation(user['id'], username, 'login', '管理员登录成功')
    start_user_session(user['id'], username)
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'username': username,
            'permissions': permissions
        },
        'expires_at': expires_at.isoformat()
    })

@app.route('/api/admin/users', methods=['GET'])
@require_admin
def get_all_users():
    """获取所有用户列表"""
    db = get_db()
    cursor = db.execute('''
        SELECT id, username, email, membership_level, status, created_at 
        FROM users ORDER BY created_at DESC
    ''')
    users = [dict(row) for row in cursor.fetchall()]
    return jsonify(users)

@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
@require_admin
def get_user_detail(user_id):
    """获取单个用户详情"""
    db = get_db()
    cursor = db.execute('''
        SELECT * FROM users WHERE id = ?
    ''', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify(dict(user))

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@require_admin
def update_user(user_id):
    """更新用户信息"""
    data = request.get_json()
    db = get_db()
    
    updates = []
    params = []
    
    if 'username' in data:
        updates.append('username = ?')
        params.append(data['username'])
    if 'email' in data:
        updates.append('email = ?')
        params.append(data['email'])
    if 'membership_level' in data:
        updates.append('membership_level = ?')
        params.append(data['membership_level'])
    if 'membership_days' in data:
        updates.append('membership_days = ?')
        params.append(data['membership_days'])
    if 'status' in data:
        updates.append('status = ?')
        params.append(data['status'])
    
    if not updates:
        return jsonify({'error': '没有更新内容'}), 400
    
    params.append(user_id)
    query = f'UPDATE users SET {", ".join(updates)} WHERE id = ?'
    db.execute(query, params)
    db.commit()
    
    return jsonify({'message': '更新成功'})

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """删除用户"""
    db = get_db()
    
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.execute('DELETE FROM auth_tokens WHERE user_id = ?', (user_id,))
    db.commit()
    
    return jsonify({'message': '删除成功'})

@app.route('/api/admin/logs', methods=['GET'])
@require_admin
def get_operation_logs():
    """获取操作日志（支持时间范围）"""
    db = get_db()
    op_type = request.args.get('type', 'all')
    start_date, end_date = get_date_range()
    
    query = 'SELECT * FROM operation_logs WHERE 1=1'
    params = []
    
    if op_type != 'all':
        query += ' AND operation_type = ?'
        params.append(op_type)
    
    if start_date and end_date:
        query += ' AND DATE(created_at) BETWEEN ? AND ?'
        params.extend([start_date, end_date])
    
    query += ' ORDER BY created_at DESC LIMIT 100'
    
    cursor = db.execute(query, params)
    logs = [dict(row) for row in cursor.fetchall()]
    return jsonify(logs)

def get_date_range():
    """获取时间范围参数"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        return start_date, end_date
    elif start_date:
        return start_date, datetime.now().strftime('%Y-%m-%d')
    elif end_date:
        return (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'), end_date
    else:
        return None, None

@staticmethod
def format_date(date_str):
    """格式化日期字符串"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return None

@app.route('/api/admin/analytics', methods=['GET'])
@require_admin
def get_admin_analytics():
    """获取管理员分析数据（支持用户筛选和时间范围）"""
    db = get_db()
    
    user_id = request.args.get('user_id')
    start_date, end_date = get_date_range()
    
    if user_id:
        cursor = db.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if start_date and end_date:
            cursor = db.execute('SELECT COUNT(*) as count FROM user_sessions WHERE user_id = ? AND DATE(login_time) BETWEEN ? AND ?', (user_id, start_date, end_date))
        else:
            cursor = db.execute('SELECT COUNT(*) as count FROM user_sessions WHERE user_id = ?', (user_id,))
        login_count = cursor.fetchone()['count']
        
        if start_date and end_date:
            cursor = db.execute('SELECT AVG(duration) as avg FROM user_sessions WHERE user_id = ? AND DATE(login_time) BETWEEN ? AND ?', (user_id, start_date, end_date))
        else:
            cursor = db.execute('SELECT AVG(duration) as avg FROM user_sessions WHERE user_id = ?', (user_id,))
        avg_duration = cursor.fetchone()['avg'] or 0
        
        if start_date and end_date:
            cursor = db.execute('SELECT COUNT(*) as count FROM operation_logs WHERE user_id = ? AND DATE(created_at) BETWEEN ? AND ?', (user_id, start_date, end_date))
        else:
            cursor = db.execute('SELECT COUNT(*) as count FROM operation_logs WHERE user_id = ?', (user_id,))
        log_count = cursor.fetchone()['count']
        
        if start_date and end_date:
            cursor = db.execute('SELECT COUNT(*) as count FROM user_sessions WHERE user_id = ? AND DATE(login_time) BETWEEN ? AND ?', (user_id, start_date, end_date))
        else:
            cursor = db.execute('SELECT COUNT(*) as count FROM user_sessions WHERE user_id = ? AND login_time > ?', (user_id, datetime.now() - timedelta(days=1)))
        today_sessions = cursor.fetchone()['count']
        
        return jsonify({
            'username': user['username'],
            'total_users': 1,
            'pro_users': 0,
            'enterprise_users': 0,
            'free_users': 0,
            'active_sessions': 0,
            'today_logins': today_sessions,
            'avg_duration': int(avg_duration),
            'today_sessions': today_sessions,
            'login_count': login_count,
            'log_count': log_count,
            'filtered_user': True,
            'date_range': {'start': start_date, 'end': end_date}
        })
    
    cursor = db.execute('SELECT COUNT(*) as total FROM users')
    total_users = cursor.fetchone()['total']
    
    cursor = db.execute('SELECT COUNT(*) as count FROM users WHERE membership_level = "pro"')
    pro_users = cursor.fetchone()['count']
    
    cursor = db.execute('SELECT COUNT(*) as count FROM users WHERE membership_level = "enterprise"')
    enterprise_users = cursor.fetchone()['count']
    
    cursor = db.execute('''
        SELECT COUNT(*) as count FROM auth_tokens WHERE expires_at > ?
    ''', (datetime.now(),))
    active_sessions = cursor.fetchone()['count']
    
    if start_date and end_date:
        cursor = db.execute('''
            SELECT COUNT(*) as count FROM operation_logs WHERE operation_type = "login" AND DATE(created_at) BETWEEN ? AND ?
        ''', (start_date, end_date))
    else:
        cursor = db.execute('''
            SELECT COUNT(*) as count FROM operation_logs WHERE operation_type = "login" AND created_at > ?
        ''', (datetime.now() - timedelta(days=1),))
    today_logins = cursor.fetchone()['count']
    
    if start_date and end_date:
        cursor = db.execute('''
            SELECT AVG(duration) as avg FROM user_sessions WHERE DATE(login_time) BETWEEN ? AND ?
        ''', (start_date, end_date))
    else:
        cursor = db.execute('''
            SELECT AVG(duration) as avg FROM user_sessions
        ''')
    avg_duration = cursor.fetchone()['avg'] or 0
    
    if start_date and end_date:
        cursor = db.execute('''
            SELECT COUNT(*) as count FROM user_sessions WHERE DATE(login_time) BETWEEN ? AND ?
        ''', (start_date, end_date))
    else:
        cursor = db.execute('''
            SELECT COUNT(*) as count FROM user_sessions WHERE login_time > ?
        ''', (datetime.now() - timedelta(days=1),))
    today_sessions = cursor.fetchone()['count']
    
    return jsonify({
        'total_users': total_users,
        'pro_users': pro_users,
        'enterprise_users': enterprise_users,
        'free_users': total_users - pro_users - enterprise_users,
        'active_sessions': active_sessions,
        'today_logins': today_logins,
        'avg_duration': int(avg_duration),
        'today_sessions': today_sessions,
        'filtered_user': False,
        'date_range': {'start': start_date, 'end': end_date}
    })

@app.route('/api/admin/users/<int:user_id>/login-history', methods=['GET'])
@require_admin
def get_user_login_history(user_id):
    """获取用户登录历史"""
    db = get_db()
    cursor = db.execute('''
        SELECT * FROM user_sessions WHERE user_id = ? 
        ORDER BY login_time DESC LIMIT 50
    ''', (user_id,))
    history = [dict(row) for row in cursor.fetchall()]
    return jsonify(history)

@app.route('/api/admin/users/<int:user_id>/behavior', methods=['GET'])
@require_admin
def get_user_behavior(user_id):
    """获取用户行为路径和页面模块停留时长（支持模块筛选和时间范围）"""
    db = get_db()
    
    module = request.args.get('module')
    start_date, end_date = get_date_range()
    
    # 构建时间范围条件
    date_cond = ""
    date_params = []
    if start_date and end_date:
        date_cond = " AND DATE(created_at) BETWEEN ? AND ?"
        date_params = [start_date, end_date]
    
    # 获取用户的操作日志，按时间排序
    if module:
        cursor = db.execute('''
            SELECT id, operation_type, description, created_at 
            FROM operation_logs 
            WHERE user_id = ? AND operation_type = ?''' + date_cond + '''
            ORDER BY created_at DESC 
            LIMIT 50
        ''', [user_id, module] + date_params)
    else:
        cursor = db.execute('''
            SELECT id, operation_type, description, created_at 
            FROM operation_logs 
            WHERE user_id = ?''' + date_cond + '''
            ORDER BY created_at DESC 
            LIMIT 50
        ''', [user_id] + date_params)
    actions = [dict(row) for row in cursor.fetchall()]
    
    # 构建会话表的时间条件
    session_date_cond = ""
    session_date_params = []
    if start_date and end_date:
        session_date_cond = " AND DATE(login_time) BETWEEN ? AND ?"
        session_date_params = [start_date, end_date]
    
    # 获取用户会话统计
    cursor = db.execute('''
        SELECT AVG(duration) as avg, SUM(duration) as total, COUNT(*) as sessions
        FROM user_sessions 
        WHERE user_id = ?''' + session_date_cond + '''
    ''', [user_id] + session_date_params)
    session_stats = cursor.fetchone()
    
    # 获取品类浏览量
    cursor = db.execute('''
        SELECT COUNT(*) as count 
        FROM category_views 
        WHERE user_id = ?''' + session_date_cond + '''
    ''', [user_id] + session_date_params)
    category_views = cursor.fetchone()['count']
    
    # 按页面模块统计停留时长（使用预计算的mock数据）
    page_modules = {
        'dashboard': {'name': '仪表盘', 'icon': '📊'},
        'blue_ocean': {'name': '蓝海选品', 'icon': '🌊'},
        'reports': {'name': '数据报表', 'icon': '📈'},
        'profile': {'name': '用户中心', 'icon': '👤'},
        'search': {'name': '搜索功能', 'icon': '🔍'},
        'export': {'name': '数据导出', 'icon': '📥'}
    }
    
    import random
    random.seed(user_id)
    
    page_duration_stats = {}
    total_page_duration = 0
    total_page_count = 0
    
    for page_key, page_info in page_modules.items():
        count = random.randint(5, 50)
        avg_duration = random.randint(120, 1800)
        page_duration_stats[page_key] = {
            'name': page_info['name'],
            'icon': page_info['icon'],
            'count': count,
            'avg_duration': avg_duration,
            'total_duration': count * avg_duration
        }
        total_page_duration += count * avg_duration
        total_page_count += count
    
    # 获取各操作类型统计（排除login/logout）
    cursor = db.execute('''
        SELECT operation_type, COUNT(*) as count 
        FROM operation_logs 
        WHERE user_id = ? AND operation_type NOT IN ('login', 'logout')''' + date_cond + '''
        GROUP BY operation_type
    ''', [user_id] + date_params)
    module_stats = {}
    for row in cursor.fetchall():
        module_stats[row['operation_type']] = row['count']
    
    return jsonify({
        'user_id': user_id,
        'module_filter': module or 'all',
        'date_range': {'start': start_date, 'end': end_date},
        'recent_actions': actions,
        'module_stats': module_stats,
        'page_duration_stats': page_duration_stats,
        'total_page_duration': total_page_duration,
        'total_page_count': total_page_count,
        'session_stats': {
            'avg_duration': int(session_stats['avg'] or 0),
            'total_duration': int(session_stats['total'] or 0),
            'session_count': session_stats['sessions'] or 0
        },
        'category_views': category_views,
        'behavior_path': generate_behavior_path(actions)
    })

def generate_behavior_path(actions):
    """生成用户行为路径（按时间倒序）"""
    path = []
    type_map = {
        'login': '登录',
        'view': '浏览',
        'search': '搜索',
        'export': '导出',
        'upgrade': '升级',
        'logout': '登出'
    }
    
    for action in actions[:20]:
        path.append({
            'type': action['operation_type'],
            'label': type_map.get(action['operation_type'], action['operation_type']),
            'description': action['description'],
            'time': action['created_at']
        })
    
    return path

@app.route('/api/admin/users/<int:user_id>/stats', methods=['GET'])
@require_admin
def get_admin_user_stats(user_id):
    """获取用户统计数据（管理员）"""
    db = get_db()
    
    cursor = db.execute('''
        SELECT COUNT(*) as login_count FROM user_sessions WHERE user_id = ?
    ''', (user_id,))
    login_count = cursor.fetchone()['login_count']
    
    cursor = db.execute('''
        SELECT AVG(duration) as avg_duration FROM user_sessions WHERE user_id = ?
    ''', (user_id,))
    avg_duration = cursor.fetchone()['avg_duration'] or 0
    
    cursor = db.execute('''
        SELECT COUNT(*) as view_count FROM category_views WHERE user_id = ?
    ''', (user_id,))
    view_count = cursor.fetchone()['view_count']
    
    cursor = db.execute('''
        SELECT COUNT(*) as log_count FROM operation_logs WHERE user_id = ?
    ''', (user_id,))
    log_count = cursor.fetchone()['log_count']
    
    return jsonify({
        'login_count': login_count,
        'avg_duration': int(avg_duration),
        'view_count': view_count,
        'log_count': log_count
    })

@app.route('/api/admin/analytics/daily', methods=['GET'])
@require_admin
def get_daily_analytics():
    """获取每日分析数据（用于图表）"""
    db = get_db()
    
    cursor = db.execute('''
        SELECT strftime('%Y-%m-%d', created_at) as date, 
               COUNT(*) as count 
        FROM operation_logs 
        WHERE operation_type = "login" 
          AND created_at > ?
        GROUP BY date 
        ORDER BY date DESC 
        LIMIT 7
    ''', (datetime.now() - timedelta(days=7),))
    login_data = [dict(row) for row in cursor.fetchall()]
    
    cursor = db.execute('''
        SELECT strftime('%H', created_at) as hour, 
               COUNT(*) as count 
        FROM operation_logs 
        WHERE operation_type = "login" 
        GROUP BY hour 
        ORDER BY hour
    ''')
    hourly_data = [dict(row) for row in cursor.fetchall()]
    
    cursor = db.execute('''
        SELECT membership_level, COUNT(*) as count 
        FROM users 
        GROUP BY membership_level
    ''')
    level_dist = [dict(row) for row in cursor.fetchall()]
    
    return jsonify({
        'daily_logins': login_data,
        'hourly_logins': hourly_data,
        'level_distribution': level_dist
    })

@app.route('/api/subscription/orders', methods=['GET'])
@require_auth
def get_user_orders():
    """获取用户的订单列表"""
    db = get_db()
    
    cursor = db.execute('''
        SELECT * FROM orders 
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (g.user_id,))
    
    orders = [dict(row) for row in cursor.fetchall()]
    return jsonify(orders)

@app.route('/api/user/stats', methods=['GET'])
@require_auth
def get_user_stats():
    """获取用户统计数据"""
    db = get_db()
    
    # 获取用户信息
    cursor = db.execute('''
        SELECT membership_level, created_at FROM users WHERE id = ?
    ''', (g.user_id,))
    user = cursor.fetchone()
    
    # 计算使用天数
    created_date = datetime.fromisoformat(user['created_at'].replace(' ', 'T'))
    days_used = (datetime.now() - created_date).days
    
    # 获取蓝海品类浏览次数（模拟）
    cursor = db.execute('''
        SELECT COUNT(*) as view_count 
        FROM category_views 
        WHERE user_id = ?
    ''', (g.user_id,))
    view_count = cursor.fetchone()['view_count'] or 0
    
    # 获取报告生成次数（模拟）
    cursor = db.execute('''
        SELECT COUNT(*) as report_count 
        FROM reports 
        WHERE user_id = ?
    ''', (g.user_id,))
    report_count = cursor.fetchone()['report_count'] or 0
    
    return jsonify({
        'days_used': days_used,
        'blue_ocean_views': view_count,
        'reports_generated': report_count,
        'membership_level': user['membership_level']
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

@app.route('/admin')
def serve_admin():
    """服务管理员后台页面"""
    return app.send_static_file('admin.html')

# ==================== 初始化 ====================

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print("正在初始化数据库...")
        init_db()
        print("数据库初始化完成！")
    else:
        print("数据库已存在，检查并补充数据...")
        init_db()
    
    print("\n[AutoSight] 汽配选品工具已启动！")
    print("=" * 50)
    print("访问地址: http://localhost:5000")
    print("测试账号: admin / 123456")
    print("测试账号: test_user / 123456")
    print("测试账号: xiaowang / 123456")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
