<template>
  <div class="settings-page">
    <!-- 修改密码 -->
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>修改密码</span>
        </div>
      </template>
      
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        :label-position="isMobile ? 'top' : 'right'"
        :label-width="isMobile ? undefined : '120px'"
        style="max-width: 500px;"
      >
        <el-form-item label="原密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            placeholder="请输入原密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
          <div class="password-tip">密码必须包含大小写字母和数字，至少6位</div>
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleChangePassword">
            确认修改
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户信息 -->
    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>用户信息</span>
        </div>
      </template>
      
      <el-descriptions :column="isMobile ? 1 : 2" border>
        <el-descriptions-item label="用户名">
          {{ user?.username }}
        </el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag :type="user?.role === 'admin' ? 'danger' : 'success'" size="small">
            {{ user?.role === 'admin' ? '管理员' : '操作员' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          <span>{{ formatCreatedAt(user?.created_at) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="登录次数">
          <span>成功登录{{ user?.login_count || 0 }}次</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 用户管理 (仅管理员可见) -->
    <el-card v-if="isAdmin" shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" size="small" @click="showCreateDialog">
            创建操作员
          </el-button>
        </div>
      </template>
      
      <el-table :data="users" class="icloud-table" v-loading="loadingUsers" style="width: 100%;" table-layout="fixed">
        <el-table-column prop="username" label="用户名" min-width="100" align="center" />
        <el-table-column prop="role" label="角色" min-width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'success'" size="small">
              {{ row.role === 'admin' ? '管理员' : '操作员' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" min-width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="140" align="center">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="200" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button 
                type="warning"
                size="small" 
                @click="showEditUserDialog(row)"
              >
                编辑
              </el-button>
              <el-button 
                v-if="row.id !== user?.id" 
                :type="row.is_active ? 'danger' : 'success'"
                size="small" 
                @click="handleToggleUser(row)"
              >
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
              <el-button 
                v-if="row.id !== user?.id" 
                type="danger" 
                size="small" 
                @click="handleDeleteUser(row)"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingUserId ? '编辑用户' : '创建操作员'"
      width="90%"
      class="icloud-dialog"
      style="max-width: 450px;"
      @close="resetForm"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        :label-position="isMobile ? 'top' : 'right'"
        :label-width="isMobile ? undefined : '80px'"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="createForm.username"
            placeholder="请输入用户名"
            maxlength="50"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="createForm.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            show-password
          />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="createForm.role" style="width: 100%;">
            <el-option label="操作员" value="operator" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          {{ editingUserId ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const authStore = useAuthStore()
const passwordFormRef = ref(null)
const createFormRef = ref(null)
const submitting = ref(false)
const creating = ref(false)
const loadingUsers = ref(false)
const dialogVisible = ref(false)
const editingUserId = ref(null)
const isMobile = ref(window.innerWidth <= 768)

const user = computed(() => authStore.user)
const isAdmin = computed(() => authStore.isAdmin)

const users = ref([])

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const createForm = reactive({
  username: '',
  password: '',
  role: 'operator'
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
    { 
      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/,
      message: '密码必须包含大小写字母和数字',
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const createRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名3-50个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function formatCreatedAt(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}年${month}月${day}日启用`
}

async function handleChangePassword() {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await authStore.changePassword(passwordForm.oldPassword, passwordForm.newPassword)
        ElMessage.success('密码修改成功')
        passwordFormRef.value.resetFields()
      } catch (error) {
        // Error handled by interceptor
      } finally {
        submitting.value = false
      }
    }
  })
}

async function fetchUsers() {
  if (!isAdmin.value) return
  loadingUsers.value = true
  try {
    const response = await api.get('/users/')
    users.value = response.data.items || response.data
  } catch (error) {
    console.error('获取用户列表失败:', error)
  } finally {
    loadingUsers.value = false
  }
}

function showCreateDialog() {
  editingUserId.value = null
  dialogVisible.value = true
}

function showEditUserDialog(row) {
  editingUserId.value = row.id
  createForm.username = row.username
  createForm.password = ''
  createForm.role = row.role
  dialogVisible.value = true
}

function resetForm() {
  editingUserId.value = null
  createForm.username = ''
  createForm.password = ''
  createForm.role = 'operator'
  createFormRef.value?.resetFields()
}

async function handleCreate() {
  if (!createFormRef.value) return
  
  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      creating.value = true
      try {
        if (editingUserId.value) {
          const updatePayload = {
            username: createForm.username,
            role: createForm.role
          }
          if (createForm.password) {
            updatePayload.password = createForm.password
          }
          await api.put(`/users/${editingUserId.value}`, updatePayload)
          ElMessage.success('更新成功')
        } else {
          await api.post('/users/', {
            username: createForm.username,
            password: createForm.password,
            role: createForm.role,
            is_active: true
          })
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        editingUserId.value = null
        fetchUsers()
      } catch (error) {
        // Error handled by interceptor
      } finally {
        creating.value = false
      }
    }
  })
}

async function handleToggleUser(row) {
  try {
    const action = row.is_active ? '禁用' : '启用'
    await ElMessageBox.confirm(
      `确定要${action}用户"${row.username}"吗？`,
      `${action}确认`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await api.put(`/users/${row.id}`, { is_active: !row.is_active })
    ElMessage.success(`${action}成功`)
    fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('操作失败:', error)
    }
  }
}

async function handleDeleteUser(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户"${row.username}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await api.delete(`/users/${row.id}`)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

onMounted(() => {
  fetchUsers()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

function handleResize() {
  isMobile.value = window.innerWidth <= 768
}
</script>

<style scoped>
.settings-page {
  padding: 0;
}

.settings-page :deep(.el-card) {
  border: none;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.settings-page :deep(.el-card__header) {
  padding: 18px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.card-header {
  font-size: 15px;
  font-weight: 600;
  color: #1d1d1f;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-page :deep(.el-card__body) {
  padding: 24px;
}

:deep(.el-form-item__label) {
  color: #424245;
  font-size: 13px;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: none;
  border: 1px solid #d2d2d7;
}

:deep(.el-input__wrapper:hover) {
  border-color: #86868b;
}

:deep(.el-input.is-focus .el-input__wrapper) {
  border-color: #0071e3;
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.15);
}

:deep(.el-select__wrapper) {
  border-radius: 8px;
  box-shadow: none;
  border: 1px solid #d2d2d7;
}

:deep(.el-select__wrapper:hover) {
  border-color: #86868b;
}

:deep(.el-select__wrapper.is-focus) {
  border-color: #0071e3;
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.15);
}

.password-tip {
  font-size: 12px;
  color: #86868b;
  margin-top: 4px;
  line-height: 1.4;
}

/* 表格样式 */
.icloud-table {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-table__header-wrapper th) {
  background: #f5f5f7;
  color: #86868b;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  border: none;
  padding: 12px 16px;
  white-space: nowrap;
}

:deep(.el-table__body-wrapper td) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  padding: 14px 16px;
  font-size: 14px;
  color: #1d1d1f;
  white-space: nowrap;
}

:deep(.el-table__row:hover td) {
  background: #fafafa;
}

:deep(.el-table__row:last-child td) {
  border-bottom: none;
}

/* 操作按钮 */
.action-btns {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

/* 对话框样式 */
:deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
}

:deep(.el-dialog__header) {
  padding: 18px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

:deep(.el-dialog__title) {
  font-size: 17px;
  font-weight: 600;
  color: #1d1d1f;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-dialog__footer) {
  padding: 16px 24px;
  background: #f5f5f7;
}

/* 用户信息表格居中 */
:deep(.el-descriptions__cell) {
  text-align: center;
}

:deep(.el-descriptions__label) {
  text-align: center;
}

:deep(.el-descriptions__content) {
  text-align: center;
}

:deep(.el-descriptions-item) {
  align-content: center;
}

/* ========== 移动端适配 ========== */
@media (max-width: 768px) {
  .settings-page :deep(.el-card__body) {
    padding: 12px;
  }

  .settings-page :deep(.el-card__header) {
    padding: 12px 14px;
  }

  :deep(.el-card) {
    margin-top: 12px !important;
  }

  :deep(.el-form) {
    max-width: 100% !important;
  }

  :deep(.el-form-item) {
    margin-bottom: 18px;
  }

  :deep(.el-dialog) {
    width: 92% !important;
    max-width: 92% !important;
  }

  :deep(.el-dialog__body) {
    padding: 16px;
  }

  :deep(.el-dialog__header) {
    padding: 14px 16px;
  }

  :deep(.el-dialog__footer) {
    padding: 12px 16px;
  }

  :deep(.el-table__header-wrapper th),
  :deep(.el-table__body-wrapper td) {
    padding: 8px 6px;
    font-size: 12px;
  }

  .card-header {
    font-size: 14px;
  }

  .card-header .el-button {
    font-size: 12px;
    padding: 5px 10px;
  }
}
</style>
