<template>
  <div class="nfc-tags-page">
    <div class="page-card">
      <div class="card-header">
        <span class="card-title">NFC标签列表</span>
        <el-button type="primary" class="btn-primary" @click="showDialog('create')">
          <el-icon><Plus /></el-icon>
          创建NFC标签
        </el-button>
      </div>

      <el-table :data="tableData" class="icloud-table">
        <el-table-column label="URL码" width="180" align="center">
          <template #default="{ row }">
            <code class="code-tag">{{ getUrlCode(row) }}</code>
          </template>
        </el-table-column>
        <el-table-column label="文创品" min-width="150" align="center">
          <template #default="{ row }">
            {{ getProductName(row.cultural_product_id) }}
          </template>
        </el-table-column>
        <el-table-column label="视频" min-width="150" align="center">
          <template #default="{ row }">
            {{ getVideoName(row.video_id) }}
          </template>
        </el-table-column>
        <el-table-column label="SKU" min-width="120" align="center">
          <template #default="{ row }">
            {{ row.sku_id ? getSkuName(row.sku_id) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="approval_status" label="审批状态" width="100" min-width="100" align="center">
          <template #default="{ row }">
            <span class="status-badge" :class="getApprovalClass(row.approval_status)">
              {{ getApprovalText(row.approval_status) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" min-width="80" align="center">
          <template #default="{ row }">
            <span class="status-dot" :class="getStatusClass(row.status)"></span>
          </template>
        </el-table-column>
        <el-table-column prop="expires_at" label="过期时间" width="120" align="center">
          <template #default="{ row }">
            <span class="text-muted">{{ row.expires_at || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button v-if="isAdmin" type="success" size="small" @click="handleApprove(row)">
                通过
              </el-button>
              <el-button v-if="isAdmin" type="danger" size="small" @click="handleReject(row)">
                驳回
              </el-button>
              <el-button type="warning" size="small" @click="showDialog('edit', row)">
                编辑
              </el-button>
              <el-button type="danger" size="small" @click="handleDelete(row)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      class="icloud-dialog"
      @close="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
        <el-form-item label="文创品" prop="cultural_product_id">
          <el-select v-model="form.cultural_product_id" placeholder="请选择文创品" style="width: 100%;" :disabled="dialogType === 'edit'">
            <el-option
              v-for="product in products"
              :key="product.id"
              :label="`${product.code} - ${product.name}`"
              :value="product.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="视频" prop="video_id">
          <el-select v-model="form.video_id" placeholder="请选择视频" style="width: 100%;">
            <el-option
              v-for="video in videos"
              :key="video.id"
              :label="`${video.code} - ${video.name}`"
              :value="video.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="SKU" prop="sku_id">
          <el-select
            v-model="form.sku_id"
            placeholder="请选择SKU单品（可选）"
            clearable
            style="width: 100%;"
            :disabled="!form.cultural_product_id"
          >
            <el-option
              v-for="sku in filteredSkus"
              :key="sku.id"
              :label="`${sku.code} - ${sku.name}`"
              :value="sku.id"
            />
          </el-select>
          <div v-if="form.cultural_product_id && filteredSkus.length === 0" class="form-tip">
            该文创品下暂无SKU，请先在产品库中添加SKU
          </div>
        </el-form-item>
        <el-form-item label="过期时间" prop="expires_at">
          <el-date-picker
            v-model="form.expires_at"
            type="date"
            placeholder="设置有效期（可选）"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
            :disabled-date="disabledDate"
          />
        </el-form-item>
        <el-form-item v-if="dialogType === 'edit'" label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio label="active">启用</el-radio>
            <el-radio label="disabled">禁用</el-radio>
            <el-radio label="expired">过期</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button class="btn-secondary" @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const tableData = ref([])
const products = ref([])
const videos = ref([])
const skus = ref([])
const dialogVisible = ref(false)
const dialogType = ref('create')
const submitting = ref(false)
const formRef = ref(null)
const currentEditId = ref(null)

const isAdmin = computed(() => authStore.isAdmin)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const form = reactive({
  cultural_product_id: null,
  video_id: null,
  sku_id: null,
  expires_at: '',
  status: 'active'
})

const formRules = {
  cultural_product_id: [
    { required: true, message: '请选择文创品', trigger: 'change' }
  ],
  video_id: [
    { required: true, message: '请选择视频', trigger: 'change' }
  ]
}

const dialogTitle = computed(() => dialogType.value === 'create' ? '创建NFC标签' : '编辑NFC标签')

const filteredSkus = computed(() => {
  if (!form.cultural_product_id) return []
  return skus.value.filter(sku => sku.cultural_product_id === form.cultural_product_id)
})

function disabledDate(date) {
  return date < new Date(new Date().setHours(0, 0, 0, 0))
}

function getProductName(productId) {
  const product = products.value.find(p => p.id === productId)
  return product ? `${product.code} - ${product.name}` : '-'
}

function getVideoName(videoId) {
  const video = videos.value.find(v => v.id === videoId)
  return video ? `${video.code} - ${video.name}` : '-'
}

function getSkuName(skuId) {
  const sku = skus.value.find(s => s.id === skuId)
  return sku ? `${sku.code} - ${sku.name}` : '-'
}

function getUrlCode(row) {
  const product = products.value.find(p => p.id === row.cultural_product_id)
  const video = videos.value.find(v => v.id === row.video_id)
  const sku = row.sku_id ? skus.value.find(s => s.id === row.sku_id) : null
  const productCode = product?.code || 'XXX'
  const videoCode = video?.code || 'XXX'
  const skuCode = sku?.code || 'XXX'
  return `/nfc/${productCode}/${videoCode}/${skuCode}`
}

function getApprovalClass(status) {
  const classes = {
    pending: 'status-pending',
    approved: 'status-success',
    rejected: 'status-rejected'
  }
  return classes[status] || ''
}

function getApprovalText(status) {
  const texts = {
    pending: '待审批',
    approved: '已通过',
    rejected: '已驳回'
  }
  return texts[status] || status
}

function getStatusClass(status) {
  const classes = {
    active: 'dot-success',
    disabled: 'dot-disabled',
    expired: 'dot-expired'
  }
  return classes[status] || ''
}

async function fetchData() {
  try {
    const response = await api.get('/nfc-tags/', {
      params: {
        skip: (pagination.page - 1) * pagination.pageSize,
        limit: pagination.pageSize
      }
    })
    tableData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('获取NFC标签列表失败:', error)
  }
}

async function fetchProducts() {
  try {
    const response = await api.get('/cultural-products', { params: { limit: 1000 } })
    products.value = response.data.items
  } catch (error) {
    console.error('获取文创品列表失败:', error)
  }
}

async function fetchVideos() {
  try {
    const response = await api.get('/videos', { params: { limit: 1000 } })
    videos.value = response.data.items
  } catch (error) {
    console.error('获取视频列表失败:', error)
  }
}

async function fetchSkus() {
  try {
    const response = await api.get('/skus/', { params: { limit: 1000 } })
    skus.value = response.data.items
  } catch (error) {
    console.error('获取SKU列表失败:', error)
  }
}

function showDialog(type, row = null) {
  dialogType.value = type
  if (type === 'edit' && row) {
    currentEditId.value = row.id
    Object.assign(form, {
      cultural_product_id: row.cultural_product_id,
      video_id: row.video_id,
      sku_id: row.sku_id,
      expires_at: row.expires_at || '',
      status: row.status
    })
  }
  dialogVisible.value = true
}

function resetForm() {
  formRef.value?.resetFields()
  currentEditId.value = null
  Object.assign(form, {
    cultural_product_id: null,
    video_id: null,
    sku_id: null,
    expires_at: '',
    status: 'active'
  })
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const submitData = {
          cultural_product_id: form.cultural_product_id,
          video_id: form.video_id,
          sku_id: form.sku_id || null,
          expires_at: form.expires_at || null
        }

        if (dialogType.value === 'create') {
          await api.post('/nfc-tags', submitData)
          ElMessage.success('创建成功')
        } else {
          const updateData = {
            video_id: form.video_id,
            sku_id: form.sku_id || null,
            status: form.status
          }
          if (form.expires_at) {
            updateData.expires_at = form.expires_at
          }
          await api.put(`/nfc-tags/${currentEditId.value}`, updateData)
          ElMessage.success('更新成功')
        }
        dialogVisible.value = false
        fetchData()
      } catch (error) {
        // Error handled by interceptor
      } finally {
        submitting.value = false
      }
    }
  })
}

async function handleApprove(row) {
  try {
    await ElMessageBox.confirm(
      `确定要通过NFC标签"${row.url_code}"吗？`,
      '审批确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'success'
      }
    )
    await api.post(`/nfc-tags/${row.id}/approve`)
    ElMessage.success('审批通过')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('审批失败:', error)
    }
  }
}

async function handleReject(row) {
  try {
    await ElMessageBox.confirm(
      `确定要驳回NFC标签"${row.url_code}"吗？`,
      '审批确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await api.post(`/nfc-tags/${row.id}/reject`)
    ElMessage.success('已驳回')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('驳回失败:', error)
    }
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除NFC标签"${row.url_code}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await api.delete(`/nfc-tags/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

onMounted(() => {
  fetchData()
  fetchProducts()
  fetchVideos()
  fetchSkus()
})
</script>

<style scoped>
.nfc-tags-page {
  height: 100%;
}

/* iCloud Card */
.page-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d1d1f;
}

/* Primary Button */
.btn-primary {
  background: #0071e3;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  padding: 8px 16px;
}

.btn-primary:hover {
  background: #0077ed;
}

/* iCloud Table */
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

/* Code Tag */
.code-tag {
  background: #f5f5f7;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 13px;
  font-family: 'SF Mono', Monaco, monospace;
  color: #1d1d1f;
  white-space: nowrap;
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.status-success {
  background: #e8f8ed;
  color: #34c759;
}

.status-pending {
  background: #fff5e6;
  color: #ff9500;
}

.status-rejected {
  background: #ffebe9;
  color: #ff3b30;
}

/* Status Dot */
.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}

.dot-success {
  background: #34c759;
}

.dot-disabled {
  background: #86868b;
}

.dot-expired {
  background: #ff3b30;
}

.text-muted {
  color: #86868b;
  font-size: 13px;
}

/* Action Buttons */
.action-btns {
  display: flex;
  gap: 6px;
}

.btn-approve {
  background: #34c759;
  border: none;
  color: white;
  border-radius: 6px;
  font-size: 12px;
  padding: 6px 12px;
}

.btn-approve:hover {
  background: #30d158;
}

.btn-reject {
  background: #ff3b30;
  border: none;
  color: white;
  border-radius: 6px;
  font-size: 12px;
  padding: 6px 12px;
}

.btn-reject:hover {
  background: #ff453a;
}

.btn-text {
  background: transparent;
  border: none;
  color: #0071e3;
  font-size: 13px;
  padding: 6px 10px;
  border-radius: 6px;
}

.btn-text:hover {
  background: rgba(0, 113, 227, 0.1);
}

.btn-danger {
  color: #ff3b30;
}

.btn-danger:hover {
  background: rgba(255, 59, 48, 0.1);
}

/* Pagination */
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-pagination) {
  font-size: 14px;
}

:deep(.el-pagination__total) {
  color: #86868b;
}

/* Dialog */
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

:deep(.el-form-item__label) {
  color: #424245;
  font-size: 13px;
  font-weight: 500;
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  border-radius: 8px;
  box-shadow: none;
  border: 1px solid #d2d2d7;
}

:deep(.el-input__wrapper:hover),
:deep(.el-select__wrapper:hover) {
  border-color: #86868b;
}

:deep(.el-input.is-focus .el-input__wrapper),
:deep(.el-select__wrapper.is-focus) {
  border-color: #0071e3;
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.15);
}

.btn-secondary {
  background: #ffffff;
  border: 1px solid #d2d2d7;
  border-radius: 8px;
  color: #424245;
  font-size: 14px;
  padding: 10px 18px;
}

.btn-secondary:hover {
  background: #f5f5f7;
}

.form-tip {
  font-size: 12px;
  color: #86868b;
  margin-top: 4px;
}
</style>
