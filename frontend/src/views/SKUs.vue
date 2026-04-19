<template>
  <div class="skus-page">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>SKU列表</span>
          <el-button type="primary" @click="showDialog('create')">
            <el-icon><Plus /></el-icon>
            新增SKU
          </el-button>
        </div>
      </template>
      
      <el-table :data="tableData" stripe style="width: 100%">
        <el-table-column prop="code" label="编号" width="100" />
        <el-table-column prop="name" label="中文名" min-width="150" />
        <el-table-column prop="cultural_product_name" label="关联文创品" min-width="150">
          <template #default="{ row }">
            {{ getProductName(row.cultural_product_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="default_video_name" label="默认视频" min-width="150">
          <template #default="{ row }">
            {{ row.default_video_id ? getVideoName(row.default_video_id) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="production_date" label="生产日期" width="120">
          <template #default="{ row }">
            {{ row.production_date || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="notes" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
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
        <el-form-item label="编号" prop="code">
          <el-input v-model="form.code" placeholder="3位数字，如001" maxlength="3" :disabled="dialogType === 'edit'" />
        </el-form-item>
        <el-form-item label="中文名" prop="name">
          <el-input v-model="form.name" placeholder="请输入SKU名称" maxlength="200" />
        </el-form-item>
        <el-form-item label="关联文创品" prop="cultural_product_id">
          <el-select v-model="form.cultural_product_id" placeholder="请选择文创品" style="width: 100%;">
            <el-option
              v-for="product in products"
              :key="product.id"
              :label="`${product.code} - ${product.name}`"
              :value="product.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="默认视频" prop="default_video_id">
          <el-select v-model="form.default_video_id" placeholder="请选择视频（可选）" clearable style="width: 100%;">
            <el-option
              v-for="video in videos"
              :key="video.id"
              :label="`${video.code} - ${video.name}`"
              :value="video.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="生产日期" prop="production_date">
          <el-date-picker
            v-model="form.production_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="请输入备注" />
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

const tableData = ref([])
const products = ref([])
const videos = ref([])
const dialogVisible = ref(false)
const dialogType = ref('create')
const submitting = ref(false)
const formRef = ref(null)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const form = reactive({
  code: '',
  name: '',
  cultural_product_id: null,
  default_video_id: null,
  production_date: '',
  notes: ''
})

const formRules = {
  code: [
    { required: true, message: '请输入编号', trigger: 'blur' },
    { pattern: /^\d{3}$/, message: '编号必须是3位数字', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入中文名', trigger: 'blur' }
  ],
  cultural_product_id: [
    { required: true, message: '请选择关联文创品', trigger: 'change' }
  ]
}

const dialogTitle = computed(() => dialogType.value === 'create' ? '新增SKU' : '编辑SKU')

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

function getProductName(productId) {
  const product = products.value.find(p => p.id === productId)
  return product ? `${product.code} - ${product.name}` : '-'
}

function getVideoName(videoId) {
  const video = videos.value.find(v => v.id === videoId)
  return video ? `${video.code} - ${video.name}` : '-'
}

async function fetchData() {
  try {
    const response = await api.get('/skus', {
      params: {
        skip: (pagination.page - 1) * pagination.pageSize,
        limit: pagination.pageSize
      }
    })
    tableData.value = response.data
    pagination.total = response.data.length
  } catch (error) {
    console.error('获取SKU列表失败:', error)
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

function showDialog(type, row = null) {
  dialogType.value = type
  if (type === 'edit' && row) {
    Object.assign(form, {
      code: row.code,
      name: row.name,
      cultural_product_id: row.cultural_product_id,
      default_video_id: row.default_video_id,
      production_date: row.production_date || '',
      notes: row.notes || ''
    })
  }
  dialogVisible.value = true
}

function resetForm() {
  formRef.value?.resetFields()
  Object.assign(form, {
    code: '',
    name: '',
    cultural_product_id: null,
    default_video_id: null,
    production_date: '',
    notes: ''
  })
}

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const submitData = {
          code: form.code,
          name: form.name,
          cultural_product_id: form.cultural_product_id,
          default_video_id: form.default_video_id || null,
          production_date: form.production_date || null,
          notes: form.notes || null
        }
        
        if (dialogType.value === 'create') {
          await api.post('/skus', submitData)
          ElMessage.success('创建成功')
        } else {
          const row = tableData.value.find(item => item.code === form.code)
          await api.put(`/skus/${row.id}`, submitData)
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

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除SKU"${row.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await api.delete(`/skus/${row.id}`)
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
})
</script>

<style scoped>
.skus-page {
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
