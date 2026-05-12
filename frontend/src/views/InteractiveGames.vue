<template>
  <div class="interactive-games-page">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="header-title">🧩 创意拼图·古画拼趣</span>
          <el-button type="primary" size="small" @click="showCreateDialog">+ 新增</el-button>
        </div>
      </template>

      <!-- Mobile-friendly gallery list -->
      <div class="gallery-section">
        <div v-if="loading" class="loading-state">加载中...</div>
        <div v-else class="gallery-list">
          <div
            v-for="g in galleries"
            :key="g.id"
            class="gallery-item"
            :class="{ active: activeGalleryId === g.id }"
            @click="handleGallerySwitch(g.id, activeGalleryId)"
          >
            <div class="item-left">
              <el-radio v-model="activeGalleryId" :label="g.id" size="small" class="item-radio" />
              <div class="item-info">
                <span class="item-title">{{ g.title }}</span>
                <span class="item-id">{{ g.id }}</span>
              </div>
            </div>
            <div class="item-right">
              <el-tag v-if="g.hasHorse" type="success" size="small">有马</el-tag>
              <el-tag v-else type="info" size="small">无马</el-tag>
              <span class="item-story">{{ g.story ? g.story.length : 0 }}段</span>
              <el-button type="warning" size="small" @click.stop="editGallery(g)">编辑</el-button>
              <el-button type="danger" size="small" @click.stop="handleDelete(g)">删除</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- Phone Preview -->
      <div class="phone-frame-wrapper">
        <div class="phone-frame">
          <div class="phone-notch"></div>
          <iframe
            :src="gameUrl"
            class="phone-iframe"
            sandbox="allow-scripts allow-same-origin allow-popups"
            loading="lazy"
            title="古画拼趣互动游戏"
            @load="onFrameLoad"
          ></iframe>
        </div>
        <div class="phone-label">📱 手机端体验（滑动拼图）</div>
      </div>
    </el-card>

    <!-- More Games -->
    <el-card shadow="hover" class="more-games-card">
      <template #header>
        <div class="card-header">
          <span>🎮 更多游戏</span>
        </div>
      </template>
      <div class="empty-state">🎮 更多游戏即将上线</div>
    </el-card>

    <!-- Create Dialog -->
    <el-dialog
      v-model="createDialogVisible"
      :title="editingGalleryId ? '编辑画卷' : '新增画卷'"
      width="90%"
      style="max-width: 500px"
      class="icloud-dialog"
      @close="resetForm"
    >
      <el-form ref="galleryFormRef" :model="galleryForm" label-width="100px">
        <el-form-item label="画卷名称" required>
          <el-input v-model="galleryForm.title" placeholder="如：韩幹·照夜白图" maxlength="100" />
        </el-form-item>
        <el-form-item label="马动画">
          <el-switch v-model="galleryForm.hasHorse" active-text="有" inactive-text="无" />
        </el-form-item>
        <el-form-item label="故事文字">
          <el-input v-model="galleryForm.storyText" type="textarea" :rows="4" placeholder="每行一个段落" />
        </el-form-item>
        <el-form-item label="上传图片" required>
          <el-upload :auto-upload="false" accept="image/*" :on-change="handleImageChange" :limit="1">
            <template #tip>
              <div class="upload-tip">上传后自动裁剪为600×600正方形</div>
            </template>
            <el-button type="primary">选择图片</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">
          {{ editingGalleryId ? '确认更新' : '确认新增' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const galleries = ref([])
const loading = ref(false)
const createDialogVisible = ref(false)
const submitting = ref(false)
const activeGalleryId = ref('')
const iframeKey = ref(0)
const editingGalleryId = ref(null)

const galleryForm = ref({
  title: '',
  hasHorse: false,
  storyText: '',
  image: null
})

async function fetchGalleries() {
  loading.value = true
  try {
    const res = await api.get('/gallery/')
    galleries.value = res.data
    const active = res.data.find(g => g.enabled === true)
    activeGalleryId.value = active ? active.id : ''
  } catch (err) {
    console.error('加载画卷失败', err)
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  editingGalleryId.value = null
  galleryForm.value = { title: '', hasHorse: false, storyText: '', image: null }
  createDialogVisible.value = true
}

function editGallery(row) {
  editingGalleryId.value = row.id
  galleryForm.value = {
    title: row.title || '',
    hasHorse: row.hasHorse || false,
    storyText: row.story ? row.story.join('\n') : '',
    image: null
  }
  createDialogVisible.value = true
}

function resetForm() {
  editingGalleryId.value = null
  galleryForm.value = { title: '', hasHorse: false, storyText: '', image: null }
}

function handleImageChange(file) {
  galleryForm.value.image = file.raw
  return false
}

async function handleCreate() {
  if (!galleryForm.value.title) { ElMessage.warning('请输入画卷名称'); return }
  if (!editingGalleryId.value && !galleryForm.value.image) { ElMessage.warning('请上传图片'); return }
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('title', galleryForm.value.title)
    fd.append('hasHorse', galleryForm.value.hasHorse ? 'true' : 'false')
    const storyLines = galleryForm.value.storyText
      ? galleryForm.value.storyText.split('\n').filter(s => s.trim())
      : [galleryForm.value.title]
    fd.append('story', JSON.stringify(storyLines))
    if (galleryForm.value.image) {
      fd.append('image', galleryForm.value.image)
    }
    if (editingGalleryId.value) {
      await api.patch(`/gallery/${editingGalleryId.value}`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      ElMessage.success('更新成功')
    } else {
      await api.post('/gallery/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      ElMessage.success('新增成功')
    }
    createDialogVisible.value = false
    editingGalleryId.value = null
    await fetchGalleries()
  } catch (err) {
    console.error(err)
    ElMessage.error(editingGalleryId.value ? '更新失败' : '新增失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  try {
    await api.delete(`/gallery/${row.id}`)
    ElMessage.success('删除成功')
    await fetchGalleries()
  } catch { ElMessage.error('删除失败') }
}

let switching = false
async function handleGallerySwitch(newVal, oldVal) {
  if (!newVal || switching) return
  switching = true
  try {
    await api.patch(`/gallery/${newVal}/toggle`)
    await fetchGalleries()
    iframeKey.value++
  } catch {
    activeGalleryId.value = oldVal
  } finally {
    switching = false
  }
}

function onFrameLoad() {
  // Refresh iframe when content loads
}

const gameUrl = computed(() => {
  const base = '/static/game/game.html'
  return activeGalleryId.value ? `${base}?album=${activeGalleryId.value}` : base
})

onMounted(() => { fetchGalleries() })
</script>

<style scoped>
.interactive-games-page {
  padding: 0;
}

.interactive-games-page :deep(.el-card) {
  border: none;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  margin-bottom: 16px;
}

.interactive-games-page :deep(.el-card__header) {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(0,0,0,0.04);
}

.card-header {
  font-size: 15px;
  font-weight: 600;
  color: #1d1d1f;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.header-title {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.interactive-games-page :deep(.el-card__body) {
  padding: 12px;
}

/* Gallery List - Card Style */
.gallery-section {
  margin-bottom: 12px;
}

.loading-state {
  text-align: center;
  padding: 24px;
  color: #86868b;
}

.gallery-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.gallery-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: #f8f8fa;
  border-radius: 10px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.gallery-item.active {
  background: #e8f0fe;
  border-color: #0071e3;
}

.gallery-item:active {
  opacity: 0.7;
}

.item-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.item-radio {
  flex-shrink: 0;
}

.item-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.item-title {
  font-size: 14px;
  font-weight: 500;
  color: #1d1d1f;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-id {
  font-size: 11px;
  color: #86868b;
  margin-top: 1px;
}

.item-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.item-story {
  font-size: 12px;
  color: #86868b;
  white-space: nowrap;
}

/* Phone Frame */
.phone-frame-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
  width: 100%;
}

.phone-label {
  margin-top: 8px;
  font-size: 12px;
  color: #86868b;
  text-align: center;
}

.phone-frame {
  width: 375px;
  height: 667px;
  border: 3px solid #1d1d1f;
  border-radius: 40px;
  overflow: hidden;
  position: relative;
  background: #fff;
  box-shadow: 0 4px 20px rgba(0,0,0,0.12);
  margin: 0 auto;
}

.phone-notch {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 150px;
  height: 24px;
  background: #1d1d1f;
  border-radius: 0 0 16px 16px;
  z-index: 10;
}

.phone-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.more-games-card {
  margin-top: 0 !important;
}

.empty-state {
  text-align: center;
  padding: 32px 16px;
  color: #86868b;
  font-size: 15px;
}

.upload-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .phone-frame {
    width: 90vw;
    max-width: 340px;
    height: calc(90vw * 1.78);
    max-height: 605px;
    border-radius: 32px;
  }

  .interactive-games-page :deep(.el-card__body) {
    padding: 10px;
  }

  .interactive-games-page :deep(.el-card__header) {
    padding: 12px 14px;
  }

  .header-title {
    font-size: 13px;
  }

  .gallery-item {
    padding: 8px 10px;
  }

  .item-title {
    font-size: 13px;
  }

  .item-right {
    gap: 6px;
  }
}
</style>
