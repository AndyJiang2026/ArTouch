<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1><span class="logo-ar">Ar</span><span class="logo-touch">Touch</span></h1>
        <p>NFC 互动视频管理系统</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 首次登录强制修改密码对话框 -->
    <el-dialog
      v-model="showPasswordDialog"
      title="首次登录 - 请修改密码"
      width="450px"
      :close-on-click-modal="false"
      :show-close="false"
      class="icloud-dialog"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
      >
        <el-form-item label="原密码" prop="oldPassword">
          <el-input v-model="passwordForm.oldPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
          <div class="password-tip">密码必须包含大小写字母和数字，至少6位</div>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" :loading="changingPassword" @click="handleChangePassword">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginFormRef = ref(null)
const passwordFormRef = ref(null)
const loading = ref(false)
const changingPassword = ref(false)
const showPasswordDialog = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
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

async function handleLogin() {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const result = await authStore.login(loginForm.username, loginForm.password)

        if (result.is_first_login) {
          showPasswordDialog.value = true
          passwordForm.oldPassword = loginForm.password
        } else {
          ElMessage.success('登录成功')
          router.push({ name: 'Dashboard' })
        }
      } catch (error) {
        // Error is handled by interceptor
      } finally {
        loading.value = false
      }
    }
  })
}

async function handleChangePassword() {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      changingPassword.value = true
      try {
        await authStore.changePassword(passwordForm.oldPassword, passwordForm.newPassword)
        ElMessage.success('密码修改成功')
        showPasswordDialog.value = false
        router.push({ name: 'Dashboard' })
      } catch (error) {
        // Error is handled by interceptor
      } finally {
        changingPassword.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e8f0f8 0%, #f5f5f7 50%, #fafafa 100%);
}

/* iCloud Style Login Card */
.login-card {
  width: 380px;
  padding: 48px 40px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 32px;
  font-weight: 600;
  color: #1d1d1f;
  margin-bottom: 4px;
  letter-spacing: -0.02em;
}

.login-header .logo-ar {
  color: #EA4335;
}

.login-header .logo-touch {
  color: #4285F4;
}

.login-header p {
  font-size: 14px;
  color: #86868b;
}

.login-form {
  margin-top: 8px;
}

.login-form :deep(.el-input__wrapper) {
  padding: 14px 16px;
  border-radius: 10px;
  box-shadow: none;
  border: 1px solid #d2d2d7;
  transition: all 0.2s ease;
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: #86868b;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: #0071e3;
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.15);
}

.login-form :deep(.el-input__inner) {
  font-size: 15px;
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 500;
  background: #0071e3;
  border: none;
  border-radius: 10px;
  margin-top: 8px;
}

.login-button:hover {
  background: #0077ed;
}

.login-button:active {
  background: #005bb5;
}

.password-tip {
  font-size: 12px;
  color: #86868b;
  margin-top: 4px;
}

/* Dialog Override */
:deep(.icloud-dialog .el-dialog) {
  border-radius: 14px;
  overflow: hidden;
}

:deep(.icloud-dialog .el-dialog__header) {
  padding: 18px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

:deep(.icloud-dialog .el-dialog__title) {
  font-size: 17px;
  font-weight: 600;
  color: #1d1d1f;
}

:deep(.icloud-dialog .el-dialog__body) {
  padding: 24px;
}

:deep(.icloud-dialog .el-dialog__footer) {
  padding: 16px 24px;
  background: #f5f5f7;
}
</style>
