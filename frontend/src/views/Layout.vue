<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <h2><span class="logo-ar">Ar</span><span class="logo-touch">Touch</span></h2>
      </div>
      <el-menu
        :default-active="$route.name"
        class="sidebar-menu"
        router
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/cultural-products">
          <el-icon><Goods /></el-icon>
          <span>文创品管理</span>
        </el-menu-item>
        <el-menu-item index="/video-management">
          <el-icon><VideoCamera /></el-icon>
          <span>视频管理</span>
        </el-menu-item>
        <el-menu-item index="/skus">
          <el-icon><Box /></el-icon>
          <span>SKU管理</span>
        </el-menu-item>
        <el-menu-item index="/nfc-tags">
          <el-icon><Postcard /></el-icon>
          <span>NFC标签</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>

      <!-- User Info -->
      <div class="user-section">
        <div class="user-avatar">{{ userInitial }}</div>
        <span class="user-name">{{ authStore.user?.username }}</span>
      </div>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <h3>{{ $route.name === 'Dashboard' ? '首页' : $route.meta?.title || $route.name }}</h3>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              <el-icon><Avatar /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  设置
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const userInitial = computed(() => {
  return authStore.user?.username?.charAt(0).toUpperCase() || 'A'
})

function handleCommand(command) {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      authStore.logout()
      router.push({ name: 'Login' })
    }).catch(() => {})
  } else if (command === 'settings') {
    router.push({ name: 'Settings' })
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

/* iCloud Style Sidebar */
.sidebar {
  background: #ffffff;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.logo h2 {
  color: #1d1d1f;
  font-size: 22px;
  font-weight: 600;
  margin: 0;
  letter-spacing: -0.02em;
}

.logo-ar {
  color: #EA4335;
}

.logo-touch {
  color: #4285F4;
}

.sidebar-menu {
  border: none;
  background: transparent;
  flex: 1;
  padding: 12px 8px;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 220px;
}

:deep(.el-menu-item) {
  height: 44px;
  line-height: 44px;
  margin: 2px 0;
  border-radius: 10px;
  color: #424245;
  font-size: 14px;
  font-weight: 500;
  padding-left: 16px !important;
  padding-right: 16px !important;
  white-space: nowrap;
}

:deep(.el-menu-item:hover) {
  background: #f5f5f7;
  color: #1d1d1f;
}

:deep(.el-menu-item.is-active) {
  background: #0071e3;
  color: #ffffff;
}

:deep(.el-menu-item.is-active .el-icon) {
  color: #ffffff;
}

/* User Section */
.user-section {
  padding: 16px 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #1d1d1f;
}

/* Header */
.header {
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.header-left h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #1d1d1f;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-dropdown {
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 20px;
  color: #86868b;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s;
}

.user-dropdown:hover {
  background: #f5f5f7;
  color: #1d1d1f;
}

/* Main Content */
.main-content {
  background: #f5f5f7;
  padding: 24px;
}
</style>
