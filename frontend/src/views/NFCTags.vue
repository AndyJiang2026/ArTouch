<template>
  <div class="nfc-tags-page">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>NFC标签列表</span>
          <el-button type="primary" @click="showDialog('create')">
            <el-icon><Plus /></el-icon>
            创建NFC标签
          </el-button>
        </div>
      </template>
      
      <el-table :data="tableData" stripe style="width: 100%">
        <el-table-column prop="url_code" label="URL码" width="180">
          <template #default="{ row }">
            <code style="font-size: 13px;">{{ row.url_code }}</code>
          </template>
        </el-table-column>
        <el-table-column label="文创品" min-width="150">
          <template #default="{ row }">
            {{ getProductName(row.cultural_product_id) }}
          </template>
        </el-table-column>
        <el-table-column label="视频" min-width="150">
          <template #default="{ row }">
            {{ getVideoName(row.video_id) }}
          </template>
        </el-table-column>
        <el-table-column label="SKU" min-width="120">
          <template #default="{ row }">
            {{ row.sku_id ? getSkuName(row.sku_id) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="approval_status" label="审批状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getApprovalType(row.approval_status)" size="small">
              {{ getApprovalText(row.approval_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="expires_at" label="过期时间" width="120">
          <template #default="{ row }">
            {{ row.expires_at || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.approval_status === 'pending' && isAdmin" type="success" size="small" @click="handleApprove(row)">
              通过
            </el-button>
            <el-button v-if="row.approval_status === 'pending' && isAdmin" type="warning" size="small" @click="handleReject(row)">
              驳回
            </el-button>
            <el-button type="primary" size="small" @click="showDialog('edit', row)">
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
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
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="550px"
      @close="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
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
          <el-select v-model="form.sku_id" placeholder="请选择SKU（可选）" clearable style="width: 100%;">
            <el-option
              v-for="sku in skus"
              :key="sku.id"
              :label="`${sku.code} - ${sku.name}`"
              :value="sku.id"
            />
          </el-select>
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
        <el-button @click="dialogVisible = false">取消</el-button>
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

function getApprovalType(status) {
  const types = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return types[status] || 'info'
}

function getApprovalText(status) {
  const texts = {
    pending: '待审批',
    approved: '已通过',
    rejected: '已驳回'
  }
  return texts[status] || status
}

function getStatusType(status) {
  const types = {
    active: 'success',
    disabled: 'info',
    expired: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    active: '启用',
    disabled: '禁用',
    expired: '过期'
  }
  return texts[status] || status
}

async function fetchData() {
  try {
    const response = await api.get('/nfc-tags', {
      params: {
        skip: (pagination.page - 1) * pagination.pageSize,
        limit: pagination.pageSize
      }
    })
    tableData.value = response.data
    pagination.total = response.data.length
  } catch (error) {
    console.error('获取NFC标签列表失败:', error)
  }
}

async function fetchProducts() {
  try {
    const response = await api.get('/cultural-products', { params: { limit: 1000 } })
    products.value = response.data
  } catch (error) {
    console.error('获取文创品列表失败:', error)
  }
}

async function fetchVideos() {
  try {
    const response = await api.get('/videos', { params: { limit: 1000 } })
    videos.value = response.data
  } catch (error) {
    console.error('获取视频列表失败:', error)
  }
}

async function fetchSkus() {
  try {
    const response = await api.get('/skus', { params: { limit: 1000 } })
    skus.value = response.data
  } catch (error) {
    console.error('获取SKU列表失败:', error)
  }
}

function showDialog(type, row = null) {
  dialogType.value = type
  if (type === 'edit' && row) {
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
          const updateData = { status: form.status }
          if (form.expires_at) {
            updateData.expires_at = form.expires_at
          }
          const row = tableData.value.find(item => item.id === form.video_id)
          await api.put(`/nfc-tags/${row.id}`, updateData)
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
