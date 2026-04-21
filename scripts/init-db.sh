#!/bin/bash
# ArtTouch 数据库初始化脚本

set -e

cd /home/admin/artouch/backend

echo "初始化数据库..."
python3 -c "
from app.main import app
from app.database import engine
from app.models import Base

# 创建所有表
Base.metadata.create_all(bind=engine)
print('数据库表创建完成')

# 初始化管理员账号
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.orm import Session
from app.database import SessionLocal

db = SessionLocal()
try:
    existing = db.query(User).filter(User.username == 'admin').first()
    if not existing:
        admin = User(
            username='admin',
            password_hash=get_password_hash('123456'),
            role='admin',
            is_active=True
        )
        db.add(admin)
        db.commit()
        print('管理员账号创建完成: admin/123456')
    else:
        print('管理员账号已存在')
finally:
    db.close()
"
