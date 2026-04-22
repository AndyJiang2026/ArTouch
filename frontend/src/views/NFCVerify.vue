<template>
  <div class="verify-container">
    <el-card class="verify-card">
      <template #header>
        <div class="card-header">
          <span>🔐 NFC 防伪验伪</span>
        </div>
      </template>

      <!-- NFC Scan Section -->
      <div class="scan-section">
        <div v-if="!isSupported" class="not-supported">
          <el-alert type="warning" :closable="false">
            <template #title>
              <strong>您的浏览器不支持 Web NFC</strong>
            </template>
            <div style="margin-top: 8px;">
              请使用以下支持的浏览器：<br/>
              • Chrome 89+ (Android)<br/>
              • Chrome 91+ (ChromeOS)<br/>
              <div style="margin-top: 8px; font-size: 12px; color: #666;">
                iOS Safari 暂不支持 Web NFC
              </div>
            </div>
          </el-alert>
        </div>

        <div v-else class="scan-controls">
          <el-button
            type="primary"
            size="large"
            :loading="isScanning"
            @click="startScan"
          >
            {{ isScanning ? '扫描中...' : '📱 扫描 NFC 标签' }}
          </el-button>

          <p class="scan-hint">
            {{ isScanning ? '请将 NFC 标签靠近手机背部' : '点击按钮后将标签靠近手机' }}
          </p>
        </div>
      </div>

      <!-- Scan Result -->
      <div v-if="scanResult" class="result-section">
        <el-divider content-position="left">读取结果</el-divider>

        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="标签UID">
            <code class="uid-code">{{ scanResult.uid }}</code>
          </el-descriptions-item>
          <el-descriptions-item label="NDEF URL">
            <el-tag size="small">{{ scanResult.url }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- Verification Status -->
        <div class="verify-status">
          <template v-if="verifyState === 'idle'">
            <el-button type="success" @click="verifyTag">
              🔍 验伪确认
            </el-button>
          </template>

          <template v-else-if="verifyState === 'loading'">
            <el-icon class="is-loading" :size="20">
              <Loading />
            </el-icon>
            <span style="margin-left: 8px;">验伪中...</span>
          </template>

          <template v-else-if="verifyState === 'success'">
            <el-result
              icon="success"
              :title="verifyResult.is_first_verify ? '首次验证' : '验证成功'"
              :subTitle="verifyResult.message"
            >
              <template #extra>
                <el-descriptions :column="1" size="small">
                  <el-descriptions-item label="产品名称">
                    {{ verifyResult.product_name || '未关联产品' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="当前计数器">
                    {{ verifyResult.counter }}
                  </el-descriptions-item>
                  <el-descriptions-item label="验证时间">
                    {{ formatTime(verifyResult.verified_at) }}
                  </el-descriptions-item>
                </el-descriptions>
                <div style="margin-top: 16px;">
                  <el-tag type="success" size="large">✅ 正品确认</el-tag>
                </div>
              </template>
            </el-result>
          </template>

          <template v-else-if="verifyState === 'error'">
            <el-result
              icon="error"
              :title="verifyResult.result || '验证失败'"
              :subTitle="verifyResult.message"
            >
              <template #extra>
                <el-tag type="danger" size="large">❌ {{ verifyResult.result }}</el-tag>
              </template>
            </el-result>
          </template>
        </div>
      </div>

      <!-- Quick Verify by UID -->
      <el-divider content-position="left">或手动输入 UID 验伪</el-divider>

      <el-form :model="manualForm" @submit.prevent="manualVerify">
        <el-form-item label="标签UID">
          <el-input
            v-model="manualForm.uid"
            placeholder="例如: 041234567890"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="warning"
            :loading="manualVerifyState === 'loading'"
            @click="manualVerify"
          >
            手动验伪
          </el-button>
        </el-form-item>
      </el-form>

      <!-- Recent Verifications -->
      <el-divider content-position="left">最近验证记录</el-divider>

      <el-table :data="recentLogs" size="small" max-height="200">
        <el-table-column prop="uid" label="UID" width="140">
          <template #default="{ row }">
            <code>{{ row.uid }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="result" label="结果" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_success ? 'success' : 'danger'" size="small">
              {{ row.is_success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="verified_at" label="时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.verified_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

// State
const isSupported = ref(false)
const isScanning = ref(false)
const scanResult = ref(null)
const verifyState = ref('idle')  // idle | loading | success | error
const verifyResult = ref(null)
const manualForm = ref({ uid: '' })
const manualVerifyState = ref('idle')
const recentLogs = ref([])

// Web NFC scanning
let ndefScanTarget = null

async function startScan() {
  if (!isSupported.value) return

  isScanning.value = true
  scanResult.value = null
  verifyState.value = 'idle'
  verifyResult.value = null

  try {
    const ndef = new NDEFReader()

    await ndef.scan()

    ndef.onreading = (event) => {
      const serialNumber = event.serialNumber || ''
      const message = event.message

      // Parse NDEF records
      let url = ''
      let rawData = null

      for (const record of message.records) {
        if (record.recordType === 'url') {
          const decoder = new TextDecoder()
          url = decoder.decode(record.data)
        }
        // Store raw data for protected pages (if accessible)
        // Note: Web NFC API does NOT provide access to password-protected pages
        // The signature verification requires pre-shared data from factory init
        if (record.recordType === 'mime') {
          rawData = record.data
        }
      }

      scanResult.value = {
        uid: serialNumber.toUpperCase(),
        url: url,
        timestamp: new Date().toISOString()
      }

      isScanning.value = false
      ElMessage.success(`读取成功: UID=${serialNumber}`)
    }

    ndef.onreadingerror = () => {
      ElMessage.error('读取失败，请重试')
      isScanning.value = false
    }

  } catch (error) {
    console.error('NFC scan error:', error)
    ElMessage.error(`扫描失败: ${error.message}`)
    isScanning.value = false
  }
}

// Verify tag via API
async function verifyTag() {
  if (!scanResult.value) return

  verifyState.value = 'loading'

  try {
    // Note: In a real implementation, the signature and counter would be
    // read from the NTAG 216's protected pages (18-25). However, Web NFC API
    // does NOT provide access to password-protected pages.
    //
    // Real factory implementation options:
    // 1. Factory burns a known signature into the tag during initialization
    // 2. App uses native NFC (React Native / Flutter) to read protected pages
    // 3. Signature is derived from UID and computed client-side (less secure)
    //
    // For demo: we compute the expected signature server-side and verify

    const uid = scanResult.value.uid

    // First, query the tag info to get expected counter
    const tagInfoRes = await api.get(`/nfc/tags/${uid}`)
    const tagInfo = tagInfoRes.data

    if (!tagInfo.is_registered) {
      verifyState.value = 'error'
      verifyResult.value = {
        result: 'tag_not_found',
        message: '该标签未注册，请联系生产商'
      }
      return
    }

    // For demo: call verify with counter only (signature from protected storage)
    // In production, use native NFC to read pages 18-25
    // Here we simulate with a placeholder - real app needs native bridge
    const verifyRes = await api.post('/nfc/verify', {
      uid: uid.toLowerCase(),
      signature: '0000000000000000000000000000000000000000000000000000000000000000',
      counter: tagInfo.counter
    })

    verifyResult.value = verifyRes.data
    verifyState.value = verifyRes.data.is_authentic ? 'success' : 'error'

    // Refresh logs
    await loadRecentLogs()

  } catch (error) {
    console.error('Verify error:', error)
    verifyState.value = 'error'
    verifyResult.value = {
      result: 'error',
      message: error.response?.data?.detail || '验伪请求失败'
    }
  }
}

// Manual verify
async function manualVerify() {
  const uid = manualForm.value.uid.trim()
  if (!uid) {
    ElMessage.warning('请输入 UID')
    return
  }

  manualVerifyState.value = 'loading'

  try {
    const res = await api.get(`/nfc/tags/${uid}`)
    const tagInfo = res.data

    if (!tagInfo.is_registered) {
      ElMessage.error('该标签未注册')
      manualVerifyState.value = 'idle'
      return
    }

    // Demo: just query info, don't do full verification
    ElMessage.success(`已注册: ${tagInfo.product_name || '未知产品'}`)
    manualVerifyState.value = 'idle'

    // Refresh logs
    await loadRecentLogs()

  } catch (error) {
    console.error('Manual verify error:', error)
    ElMessage.error(error.response?.data?.detail || '查询失败')
    manualVerifyState.value = 'idle'
  }
}

// Load recent verification logs (for demo, we just show locally)
async function loadRecentLogs() {
  // In production, this would fetch from /api/nfc/logs/{uid}
  // For now, we use localStorage as a simple demo
  try {
    const stored = localStorage.getItem('nfc_verify_logs') || '[]'
    recentLogs.value = JSON.parse(stored).slice(0, 10)
  } catch (e) {
    recentLogs.value = []
  }
}

function formatTime(isoString) {
  if (!isoString) return '-'
  const d = new Date(isoString)
  return d.toLocaleString('zh-CN')
}

onMounted(() => {
  // Check Web NFC support
  if ('NDEFReader' in window) {
    isSupported.value = true
  }

  loadRecentLogs()
})

onUnmounted(() => {
  // Cleanup NFC scan
  if (ndefScanTarget) {
    ndefScanTarget = null
  }
})
</script>

<style scoped>
.verify-container {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.verify-card {
  border-radius: 12px;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
}

.scan-section {
  text-align: center;
  padding: 24px 0;
}

.scan-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.scan-hint {
  color: #888;
  font-size: 14px;
}

.not-supported {
  padding: 16px;
}

.result-section {
  margin-top: 24px;
}

.verify-status {
  margin-top: 24px;
  text-align: center;
  padding: 24px;
  background: #f5f7fa;
  border-radius: 8px;
}

.uid-code {
  font-family: 'Courier New', monospace;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
</style>
