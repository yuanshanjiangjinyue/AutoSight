#!/bin/bash
# AutoSight + NATAPP 一键启动脚本

echo "========================================"
echo "  AutoSight 服务启动"
echo "========================================"
echo ""

# 检查并启动后端服务
check_backend() {
    echo "检查后端服务..."
    
    if lsof -i :5000 >/dev/null 2>&1; then
        echo "✅ 后端服务已在运行"
    else
        echo "启动后端服务..."
        cd /Users/lawrence/Documents/Auto-Analysis
        nohup python3 app.py > /tmp/autosight-backend.log 2>&1 &
        sleep 3
        
        if lsof -i :5000 >/dev/null 2>&1; then
            echo "✅ 后端服务启动成功"
        else
            echo "❌ 后端服务启动失败"
            return 1
        fi
    fi
}

# 检查并启动 NATAPP
check_natapp() {
    echo ""
    echo "检查 NATAPP 隧道..."
    
    if pgrep -f "natapp.*authtoken=0bc5046deb6ce1c4" > /dev/null; then
        echo "✅ NATAPP 已在运行"
    else
        echo "启动 NATAPP 隧道..."
        /opt/natapp/natapp -log=stdout -authtoken=0bc5046deb6ce1c4 &
        sleep 2
        
        if pgrep -f "natapp.*authtoken=0bc5046deb6ce1c4" > /dev/null; then
            echo "✅ NATAPP 启动成功"
        else
            echo "❌ NATAPP 启动失败"
            return 1
        fi
    fi
}

# 显示访问信息
show_info() {
    echo ""
    echo "========================================"
    echo "  🎉 启动完成！"
    echo "========================================"
    echo ""
    echo "本地访问："
    echo "  http://localhost:5000"
    echo "  http://localhost:8080"
    echo ""
    echo "局域网访问："
    echo "  http://192.168.43.135:5000"
    echo ""
    echo "🌐 公网访问（NATAPP）："
    echo "  http://n8ddac43.natappfree.cc"
    echo ""
    echo "⚠️  注意：NATAPP 免费隧道可能随时变化"
    echo ""
    echo "登录信息："
    echo "  管理员: admin / 123456"
    echo "  测试用户: test_user / 123456"
    echo "  普通用户: xiaowang / 123456"
    echo ""
    echo "========================================"
}

# 主流程
main() {
    check_backend
    check_natapp
    show_info
}

main
