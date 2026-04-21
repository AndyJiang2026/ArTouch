<template>
  <div class="cultural-products">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>文创品列表</span>
          <el-button type="primary" @click="showDialog('create')">
            <el-icon><Plus /></el-icon>
            新增文创品
          </el-button>
        </div>
      </template>

      <el-table :data="tableData" style="width: 100%" class="icloud-table">
        <el-table-column prop="code" label="编号" width="80" min-width="80" align="center">
          <template #default="{ row }">
            <span class="mono">{{ row.code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="中文名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="80" min-width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" align="center">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button type="primary" size="small" @click="showDialog('edit', row)">
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
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @close="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px">
        <el-form-item label="编号" prop="code">
          <el-input v-model="form.code" placeholder="3位数字，如001" maxlength="3" :disabled="dialogType === 'edit'" />
        </el-form-item>
        <el-form-item label="中文名" prop="name">
          <el-input v-model="form.name" placeholder="请输入文创品名称" maxlength="200" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio label="active">启用</el-radio>
            <el-radio label="inactive">禁用</el-radio>
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

const tableData = ref([])
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
  description: '',
  status: 'active'
})

const formRules = {
  code: [
    { required: true, message: '请输入编号', trigger: 'blur' },
    { pattern: /^\d{3}$/, message: '编号必须是3位数字', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入中文名', trigger: 'blur' },
    { min: 1, max: 200, message: '名称长度在1-200之间', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

const dialogTitle = computed(() => dialogType.value === 'create' ? '新增文创品' : '编辑文创品')

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

async function fetchData() {
  try {
    const response = await api.get('/cultural-products/', {
      params: {
        skip: (pagination.page - 1) * pagination.pageSize,
        limit: pagination.pageSize
      }
    })
    tableData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('获取文创品列表失败:', error)
  }
}

function showDialog(type, row = null) {
  dialogType.value = type
  if (type === 'edit' && row) {
    Object.assign(form, {
      code: row.code,
      name: row.name,
      description: row.description || '',
      status: row.status
    })
  }
  dialogVisible.value = true
}

function resetForm() {
  formRef.value?.resetFields()
  Object.assign(form, {
    code: '',
    name: '',
    description: '',
    status: 'active'
  })
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (dialogType.value === 'create') {
          await api.post('/cultural-products', form)
          ElMessage.success('创建成功')
        } else {
          const row = tableData.value.find(item => item.code === form.code)
          await api.put(`/cultural-products/${row.id}`, form)
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
      `确定要删除文创品"${row.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await api.delete(`/cultural-products/${row.id}`)
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
})
</script>

<style scoped>
.cultural-products {
  height: 100%;
}

.cultural-products :deep(.el-card) {
  border: none;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header span {
  font-size: 15px;
  font-weight: 600;
  color: #1d1d1f;
}

.card-header :deep(.el-button--primary) {
  background: #0071e3;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
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

.action-btns {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.mono {
  font-family: 'SF Mono', 'Menlo', monospace;
  letter-spacing: 0.05em;
}
</style>
