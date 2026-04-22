#!/bin/bash
# ArtTouch NFC 互动视频系统 - 部署脚本

set -e

ARTCH_HOME="/home/admin/artouch"
BACKEND="$ARTCH_HOME/backend"
FRONTEND="$ARTCH_HOME/frontend"
NGINX_CONF="$ARTCH_HOME/nginx/artouch.conf"
SERVICE_FILE="$ARTCH_HOME/artouch.service"

echo "========================================="
echo "  ArtTouch NFC 部署脚本"
echo "========================================="

# 1. 安装后端依赖
echo "[1/6] 安装后端依赖..."
cd "$BACKEND"
pip3 install -r requirements.txt -q

# 2. 安装前端依赖并构建
echo "[2/6] 构建前端..."
cd "$FRONTEND"
npm install --silent 2>/dev/null
npm run build

# 3. 创建必要目录
echo "[3/6] 创建目录..."
mkdir -p "$ARTCH_HOME/videos"
mkdir -p "$ARTCH_HOME/data"
mkdir -p "$ARTCH_HOME/logs"
chmod 755 "$ARTCH_HOME/videos"

# 4. 配置Nginx
echo "[4/6] 配置Nginx..."
if [ -f /etc/nginx/sites-available/artouch.conf ]; then
    sudo rm -f /etc/nginx/sites-enabled/artouch.conf
    sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-available/artouch.conf
    sudo ln -sf /etc/nginx/sites-available/artouch.conf /etc/nginx/sites-enabled/artouch.conf
else
    echo "  注意: 请手动配置Nginx"
fi

# 5. 配置systemd
echo "[5/6] 配置systemd服务..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable artouch

# 6. 启动服务
echo "[6/6] 启动服务..."
sudo systemctl restart artouch
sudo systemctl restart nginx

echo ""
echo "========================================="
echo "  部署完成!"
echo "========================================="
echo ""
echo "服务状态:"
sudo systemctl status artouch --no-pager 2>/dev/null | head -5
echo ""
echo "访问地址:"
echo "  管理后台: https://www.artouch.tech/admin/"
echo "  API文档:  https://www.artouch.tech/api/docs"
echo "  播放页:   https://www.artouch.tech/nfc/play.html"
echo ""
echo "初始账号: admin / 123456"
echo "========================================="
