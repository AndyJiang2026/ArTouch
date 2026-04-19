<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #409eff;">
            <el-icon><Postcard /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_tags }}</div>
            <div class="stat-label">标签总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #67c23a;">
            <el-icon><VideoCamera /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_videos }}</div>
            <div class="stat-label">视频总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #e6a23c;">
            <el-icon><VideoPlay /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_clicks }}</div>
            <div class="stat-label">播放次数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #f56c6c;">
            <el-icon><Calendar /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.today_clicks }}</div>
            <div class="stat-label">今日访问</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #909399;">
            <el-icon><Box /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_skus }}</div>
            <div class="stat-label">SKU总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #c71585;">
            <el-icon><Goods /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_cultural_products }}</div>
            <div class="stat-label">文创品总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #00ced1;">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.active_tags }}</div>
            <div class="stat-label">活跃标签</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #ff8c00;">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.pending_tags }}</div>
            <div class="stat-label">待审批</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>访问趋势 (本周)</span>
            </div>
          </template>
          <div ref="chartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>热门标签 TOP 10</span>
            </div>
          </template>
          <div class="top-tags">
            <div v-if="stats.top_tags?.length === 0" class="empty-text">
              暂无数据
            </div>
            <div
              v-for="(tag, index) in stats.top_tags"
              :key="tag.tag_id"
              class="top-tag-item"
            >
              <span class="tag-rank" :class="{ 'top-3': index < 3 }">{{ index + 1 }}</span>
              <span class="tag-code">{{ tag.url_code }}</span>
              <span class="tag-count">{{ tag.click_count }} 次</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'

const chartRef = ref(null)
let chart = null

const stats = reactive({
  total_clicks: 0,
  today_clicks: 0,
  week_clicks: 0,
  month_clicks: 0,
  total_tags: 0,
  active_tags: 0,
  pending_tags: 0,
  total_cultural_products: 0,
  total_videos: 0,
  total_skus: 0,
  top_tags: []
})

async function fetchStats() {
  try {
    const response = await api.get('/dashboard/stats')
    Object.assign(stats, response.data)
    await nextTick()
    initChart()
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

function initChart() {
  if (!chartRef.value) return
  
  chart = echarts.init(chartRef.value)
  
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const data = [120, 200, 150, 80, 70, 110, 130]
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: days,
      boundaryGap: false
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '访问次数',
        type: 'line',
        smooth: true,
        data: data,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        },
        lineStyle: {
          color: '#409eff'
        },
        itemStyle: {
          color: '#409eff'
        }
      }
    ]
  }
  
  chart.setOption(option)
}

onMounted(() => {
  fetchStats()
  window.addEventListener('resize', () => {
    chart?.resize()
  })
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
}

.stat-icon .el-icon {
  font-size: 28px;
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 8px;
}

.chart-row {
  margin-bottom: 20px;
}

.card-header {
  font-size: 16px;
  font-weight: 500;
}

.chart-container {
  height: 300px;
}

.top-tags {
  max-height: 340px;
  overflow-y: auto;
}

.empty-text {
  text-align: center;
  color: #999;
  padding: 40px 0;
}

.top-tag-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.top-tag-item:last-child {
  border-bottom: none;
}

.tag-rank {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #e0e0e0;
  color: #666;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.tag-rank.top-3 {
  background: #409eff;
  color: white;
}

.tag-code {
  flex: 1;
  font-family: monospace;
  font-size: 14px;
}

.tag-count {
  color: #999;
  font-size: 13px;
}
</style>
