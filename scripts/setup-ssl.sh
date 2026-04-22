#!/bin/bash
# ArtTouch SSL证书申请脚本 (Let's Encrypt)

set -e

DOMAIN="www.artouch.tech"
EMAIL="admin@artouch.tech"
CERT_PATH="/etc/letsencrypt/live/$DOMAIN"

echo "========================================="
echo "  SSL证书申请"
echo "========================================="

# 检查certbot
if ! command -v certbot &> /dev/null; then
    echo "安装certbot..."
    sudo apt-get update -qq
    sudo apt-get install -y certbot python3-certbot-nginx
fi

# 申请证书
echo "申请SSL证书..."
sudo certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive

echo ""
echo "========================================="
echo "  证书申请完成!"
echo "========================================="
echo "证书位置: $CERT_PATH"
echo "到期时间: $(sudo certbot certificates | grep "$DOMAIN" -A 1 | grep expires || echo '请手动查看')"
