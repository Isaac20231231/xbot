#!/bin/bash
set -e

# 启动系统Redis服务
echo "启动系统Redis服务..."
redis-server /etc/redis/redis.conf --daemonize yes

# 等待系统Redis服务启动
echo "等待系统Redis服务可用..."
sleep 2

echo "系统将只使用端口6379的Redis服务"

# 检查并确保3000端口可用
if lsof -i:3000 > /dev/null 2>&1; then
    echo "警告：端口3000已被占用，尝试终止占用进程..."
    kill -9 $(lsof -t -i:3000) 2>/dev/null || true
    sleep 1
fi

# 启动WeTTy终端服务
if command -v wetty &> /dev/null; then
    wetty --port 3000 --host 0.0.0.0 --allow-iframe --base /wetty --command /bin/bash &
elif [ -f "/usr/local/bin/wetty" ]; then
    /usr/local/bin/wetty --port 3000 --host 0.0.0.0 --allow-iframe --base /wetty --command /bin/bash &
elif [ -f "/usr/bin/wetty" ]; then
    /usr/bin/wetty --port 3000 --host 0.0.0.0 --allow-iframe --base /wetty --command /bin/bash &
else
    echo "警告：wetty命令未找到，跳过启动WeTTy终端服务"
fi

sleep 3

echo "启动XXXBot主应用..."
exec python /app/main.py