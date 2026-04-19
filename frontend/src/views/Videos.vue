<template>
  <div class="videos-page">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>视频列表</span>
          <div class="header-actions">
            <el-button type="primary" @click="showUploadDialog">
              <el-icon><Upload /></el-icon>
              上传视频
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="tableData" stripe style="width: 100%">
        <el-table-column prop="code" label="编号" width="100" />
        <el-table-column prop="name" label="中文名" min-width="200" />
        <el-table-column prop="duration" label="时长" width="100">
          <template #default="{ row }">
            {{ row.duration ? formatDuration(row.duration) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">
            {{ row.file_size ? formatFileSize(row.file_size) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handlePreview(row)">
              预览
            </el-button>
            <el-button type="warning" size="small" @click="showEditDialog(row)">
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

    <!-- 上传视频对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传视频" width="500px">
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules" label-width="80px">
        <el-form-item label="编号" prop="code">
          <el-input v-model="uploadForm.code" placeholder="3位数字，如001" maxlength="3" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="uploadForm.name" placeholder="请输入视频名称" maxlength="200" />
        </el-form-item>
        <el-form-item label="视频文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".mp4"
          >
            <template #trigger>
              <el-button type="primary">选择MP4文件</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">支持MP4格式，最大200MB</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑视频" width="500px" @close="resetEditForm">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入视频名称" maxlength="200" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="editForm.status">
            <el-radio label="active">启用</el-radio>
            <el-radio label="inactive">禁用</el-radio>
            <el-radio label="processing">处理中</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleUpdate">确定</el-button>
      </template>
    </el-dialog>

    <!-- 视频预览对话框 -->
    <el-dialog v-model="previewDialogVisible" title="视频预览" width="800px">
      <div class="video-preview">
        <video
          v-if="previewUrl"
          ref="videoPlayer"
          :src="previewUrl"
          controls
          autoplay
          style="width: 100%; max-height: 500px;"
        >
          您的浏览器不支持视频播放
        </video>
        <div v-else class="preview-empty">
          <el-icon :size="48"><VideoCamera /></el-icon>
          <p>暂无视频</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const tableData = ref([])
const uploadDialogVisible = ref(false)
const editDialogVisible = ref(false)
const previewDialogVisible = ref(false)
const uploading = ref(false)
const submitting = ref(false)
const uploadFormRef = ref(null)
const editFormRef = ref(null)
const uploadRef = ref(null)
const videoPlayer = ref(null)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const uploadForm = reactive({
  code: '',
  name: '',
  file: null
})

const editForm = reactive({
  id: null,
  name: '',
  status: 'active'
})

const uploadRules = {
  code: [
    { required: true, message: '请输入编号', trigger: 'blur' },
    { pattern: /^\d{3}$/, message: '编号必须是3位数字', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入名称', trigger: 'blur' }
  ],
  file: [
    { required: true, message: '请选择视频文件', trigger: 'change' }
  ]
}

const editRules = {
  name: [
    { required: true, message: '请输入名称', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

const previewUrl = ref('')

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

function formatDuration(seconds) {
  if (!seconds) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatFileSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function getStatusType(status) {
  const types = {
    active: 'success',
    inactive: 'info',
    processing: 'warning'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    active: '启用',
    inactive: '禁用',
    processing: '处理中'
  }
  return texts[status] || status
}

async function fetchData() {
  try {
    const response = await api.get('/videos', {
      params: {
        skip: (pagination.page - 1) * pagination.pageSize,
        limit: pagination.pageSize
      }
    })
    tableData.value = response.data
    pagination.total = response.data.length
  } catch (error) {
    console.error('获取视频列表失败:', error)
  }
}

function showUploadDialog() {
  uploadForm.code = ''
  uploadForm.name = ''
  uploadForm.file = null
  uploadDialogVisible.value = true
}

function handleFileChange(file) {
  uploadForm.file = file.raw
}

function handleFileRemove() {
  uploadForm.file = null
}

async function handleUpload() {
  if (!uploadFormRef.value) return
  
  await uploadFormRef.value.validate(async (valid) => {
    if (valid) {
      if (!uploadForm.file) {
        ElMessage.warning('请选择视频文件')
        return
      }
      
      const formData = new FormData()
      formData.append('code', uploadForm.code)
      formData.append('name', uploadForm.name)
      formData.append('file', uploadForm.file)
      
      uploading.value = true
      try {
        await api.post('/videos/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        ElMessage.success('上传成功')
        uploadDialogVisible.value = false
        fetchData()
        
        // 自动处理视频获取时长
        ElMessage.info('视频正在处理中，请稍后刷新查看时长')
      } catch (error) {
        // Error handled by interceptor
      } finally {
        uploading.value = false
      }
    }
  })
}

function showEditDialog(row) {
  editForm.id = row.id
  editForm.name = row.name
  editForm.status = row.status
  editDialogVisible.value = true
}

function resetEditForm() {
  editFormRef.value?.resetFields()
}

async function handleUpdate() {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await api.put(`/videos/${editForm.id}`, {
          name: editForm.name,
          status: editForm.status
        })
        ElMessage.success('更新成功')
        editDialogVisible.value = false
        fetchData()
      } catch (error) {
        // Error handled by interceptor
      } finally {
        submitting.value = false
      }
    }
  })
}

function handlePreview(row) {
  if (row.file_path) {
    previewUrl.value = row.file_path
  } else {
    previewUrl.value = ''
  }
  previewDialogVisible.value = true
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除视频"${row.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await api.delete(`/videos/${row.id}`)
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
.videos-page {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.video-preview {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.preview-empty {
  text-align: center;
  color: #999;
}

.preview-empty p {
  margin-top: 10px;
}
</style>
