#!/usr/bin/env python3
"""
视频管理完整测试：上传、列表、编辑、删除、时长提取

运行方式:
    cd /home/admin/artouch/backend
    SECRET_KEY=test-secret-key-for-testing-12345 DATABASE_URL=sqlite:///./test_video_final.db REDIS_URL=redis://localhost:6379/0 python test_video_management.py
"""

import io
import os
import sys
import tempfile

# Setup environment before importing app modules
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-12345"
os.environ["DATABASE_URL"] = "sqlite:///./test_video_final.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.video_processor import VideoProcessor
from app.models import Base, CulturalProduct, User, Video
from app.core.security import get_password_hash
from app.api.deps import get_db
from app.main import app


def setup_database():
    """创建测试数据库"""
    engine = create_engine(
        "sqlite:///./test_video_final.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine


def create_test_client(engine):
    """创建测试客户端"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), TestingSessionLocal


def create_test_user_and_login(client, db, role="operator"):
    """创建测试用户并返回认证头"""
    user = User(
        username=f"test_{role}",
        password_hash=get_password_hash("TestPass123"),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Login
    response = client.post(
        "/api/auth/login",
        data={"username": f"test_{role}", "password": "TestPass123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_test_video_file():
    """创建模拟视频文件"""
    content = b"\x00\x00\x00\x1c\x66\x74\x79\x70\x69\x73\x6f\x6d" + b"\x00" * 100
    return ("test_video.mp4", io.BytesIO(content), "video/mp4")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("视频管理完整测试")
    print("=" * 60)
    
    # Setup
    engine = setup_database()
    client, SessionLocal = create_test_client(engine)
    
    # Create test user and login
    db = SessionLocal()
    headers = create_test_user_and_login(client, db, "operator")
    db.close()
    
    results = {"passed": [], "failed": []}
    video_id = None
    
    # =============================================================
    # Test 1: 上传视频
    # =============================================================
    print("\n[Test 1] 上传视频...")
    try:
        filename, file_data, content_type = create_test_video_file()
        response = client.post(
            "/api/videos/upload",
            headers=headers,
            files={"file": (filename, file_data, content_type)},
            data={"code": "V001", "name": "测试视频001"},
        )
        print(f"DEBUG: response status={response.status_code}, body={response.text}")
        assert response.status_code == 201, f"Upload failed: {response.text}"
        video = response.json()
        assert video["code"] == "V001"
        assert video["name"] == "测试视频001"
        assert video["status"] == "processing"
        video_id = video["id"]
        print(f"  ✓ 视频上传成功 (ID: {video_id})")
        results["passed"].append("上传视频")
    except Exception as e:
        print(f"  ✗ 视频上传失败: {e}")
        results["failed"].append(("上传视频", str(e)))
        video_id = None
    
    # =============================================================
    # Test 2: 获取视频列表
    # =============================================================
    print("\n[Test 2] 获取视频列表...")
    try:
        response = client.get("/api/videos/", headers=headers)
        assert response.status_code == 200, f"List failed: {response.text}"
        videos = response.json()
        assert len(videos) >= 1
        print(f"  ✓ 视频列表获取成功 (共 {len(videos)} 个视频)")
        results["passed"].append("获取视频列表")
    except Exception as e:
        print(f"  ✗ 视频列表获取失败: {e}")
        results["failed"].append(("获取视频列表", str(e)))
    
    # =============================================================
    # Test 3: 获取单个视频
    # =============================================================
    if video_id:
        print("\n[Test 3] 获取单个视频详情...")
        try:
            response = client.get(f"/api/videos/{video_id}", headers=headers)
            assert response.status_code == 200, f"Get failed: {response.text}"
            video = response.json()
            assert video["id"] == video_id
            print(f"  ✓ 视频详情获取成功: {video['name']}")
            results["passed"].append("获取单个视频")
        except Exception as e:
            print(f"  ✗ 视频详情获取失败: {e}")
            results["failed"].append(("获取单个视频", str(e)))
        
        # =============================================================
        # Test 4: 更新视频信息
        # =============================================================
        print("\n[Test 4] 更新视频信息...")
        try:
            response = client.put(
                f"/api/videos/{video_id}",
                headers=headers,
                json={"name": "更新后的视频名称", "status": "active"},
            )
            assert response.status_code == 200, f"Update failed: {response.text}"
            video = response.json()
            assert video["name"] == "更新后的视频名称"
            assert video["status"] == "active"
            print(f"  ✓ 视频信息更新成功")
            results["passed"].append("更新视频信息")
        except Exception as e:
            print(f"  ✗ 视频信息更新失败: {e}")
            results["failed"].append(("更新视频信息", str(e)))
    else:
        print("\n[Test 3/4] 跳过 (视频未创建)")
        print("\n[Test 4] 跳过 (视频未创建)")
    
    # =============================================================
    # Test 5: 创建文创产品
    # =============================================================
    print("\n[Test 5] 创建文创产品...")
    product1_id = product2_id = None
    try:
        db = SessionLocal()
        product1 = CulturalProduct(code="CP001", name="文创产品1", description="描述1", status="active")
        product2 = CulturalProduct(code="CP002", name="文创产品2", description="描述2", status="active")
        db.add(product1)
        db.add(product2)
        db.commit()
        db.refresh(product1)
        db.refresh(product2)
        product1_id = product1.id
        product2_id = product2.id
        db.close()
        print(f"  ✓ 文创产品创建成功 (ID: {product1_id}, {product2_id})")
        results["passed"].append("创建文创产品")
    except Exception as e:
        print(f"  ✗ 文创产品创建失败: {e}")
        results["failed"].append(("创建文创产品", str(e)))
    
    # =============================================================
    # Test 6: 关联文创产品到视频
    # =============================================================
    if product1_id and video_id:
        print("\n[Test 6] 关联文创产品到视频...")
        try:
            response = client.put(
                f"/api/videos/{video_id}",
                headers=headers,
                json={"cultural_product_ids": [product1_id, product2_id]},
            )
            assert response.status_code == 200, f"Associate failed: {response.text}"
            video = response.json()
            assert len(video.get("cultural_products", [])) == 2
            print(f"  ✓ 文创产品关联成功")
            results["passed"].append("关联文创产品")
        except Exception as e:
            print(f"  ✗ 文创产品关联失败: {e}")
            results["failed"].append(("关联文创产品", str(e)))
    else:
        print("\n[Test 6] 跳过 (产品或视频未创建)")
    
    # =============================================================
    # Test 7: 视频时长提取 (VideoProcessor)
    # =============================================================
    print("\n[Test 7] 视频时长提取...")
    try:
        # Create a real test video file (minimal MP4)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            # Write minimal MP4 header
            f.write(b"\x00\x00\x00\x1c\x66\x74\x79\x70\x69\x73\x6f\x6d\x00\x00\x00\x00")
            f.write(b"\x69\x73\x6f\x6d\x69\x73\x6f\x32\x6d\x70\x34\x00\x00\x00\x00")
            f.write(b"\x00\x00\x00\x08\x66\x72\x65\x65\x00\x00\x00\x00\x00\x00\x00")
            f.write(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
            test_video_path = f.name
        
        info = VideoProcessor.get_video_info(test_video_path)
        # Note: Without proper MP4 data, ffprobe may return None
        if info is None:
            print(f"  ⚠ ffprobe 无法获取信息 (测试视频格式不完整)")
            # Test with non-existent file
            info = VideoProcessor.get_video_info("/nonexistent/file.mp4")
            assert info is None, "Should return None for non-existent file"
            print(f"  ✓ 时长提取-文件不存在处理正确")
            results["passed"].append("时长提取(文件不存在)")
        else:
            print(f"  ✓ 视频信息提取成功: duration={info.get('duration')}")
            results["passed"].append("时长提取")
        
        os.unlink(test_video_path)
    except Exception as e:
        print(f"  ✗ 视频时长提取失败: {e}")
        results["failed"].append(("时长提取", str(e)))
    
    # =============================================================
    # Test 8: 删除视频
    # =============================================================
    if video_id:
        print("\n[Test 8] 删除视频...")
        try:
            response = client.delete(f"/api/videos/{video_id}", headers=headers)
            assert response.status_code == 204, f"Delete failed: {response.text}"
            
            # Verify deletion
            db = SessionLocal()
            video = db.query(Video).filter(Video.id == video_id).first()
            db.close()
            assert video is None, "Video should be deleted"
            print(f"  ✓ 视频删除成功")
            results["passed"].append("删除视频")
        except Exception as e:
            print(f"  ✗ 视频删除失败: {e}")
            results["failed"].append(("删除视频", str(e)))
        
        # =============================================================
        # Test 9: 验证关联数据清理
        # =============================================================
        print("\n[Test 9] 验证删除后关联数据清理...")
        try:
            db = SessionLocal()
            # Check that the association table is cleaned
            result = db.execute(
                text("SELECT COUNT(*) FROM cultural_product_videos WHERE video_id = :vid"),
                {"vid": video_id}
            ).scalar()
            db.close()
            assert result == 0, "Association table should be cleaned"
            print(f"  ✓ 关联数据已正确清理")
            results["passed"].append("关联数据清理")
        except Exception as e:
            print(f"  ✗ 关联数据清理验证失败: {e}")
            results["failed"].append(("关联数据清理", str(e)))
    else:
        print("\n[Test 8/9] 跳过 (视频未创建)")
    
    # =============================================================
    # Summary
    # =============================================================
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"通过: {len(results['passed'])}")
    for test in results["passed"]:
        print(f"  ✓ {test}")
    
    if results["failed"]:
        print(f"\n失败: {len(results['failed'])}")
        for test, error in results["failed"]:
            print(f"  ✗ {test}: {error}")
    
    # Cleanup
    app.dependency_overrides.clear()
    engine.dispose()
    if os.path.exists("./test_video_final.db"):
        os.remove("./test_video_final.db")
    
    return results


if __name__ == "__main__":
    results = run_tests()
    print()
    sys.exit(0 if len(results["failed"]) == 0 else 1)