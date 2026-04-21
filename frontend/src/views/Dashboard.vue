<template>
  <div class="dashboard">
    <!-- Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #0071e3 0%, #5a9fd4 100%);">
          <el-icon><Postcard /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value highlight">{{ stats.total_tags }}</div>
          <div class="stat-label">标签总数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #34c759 0%, #30d158 100%);">
          <el-icon><VideoCamera /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_videos }}</div>
          <div class="stat-label">视频总数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #ff9500 0%, #ff9f0a 100%);">
          <el-icon><VideoPlay /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_clicks }}</div>
          <div class="stat-label">播放次数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #ff3b30 0%, #ff453a 100%);">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value warning">{{ stats.pending_tags }}</div>
          <div class="stat-label">待审批</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #86868b 0%, #a1a1a6 100%);">
          <el-icon><Box /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_skus }}</div>
          <div class="stat-label">SKU总数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #c71585 0%, #db4d8f 100%);">
          <el-icon><Goods /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_cultural_products }}</div>
          <div class="stat-label">文创品总数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #00ced1 0%, #20b2aa 100%);">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.active_tags }}</div>
          <div class="stat-label">活跃标签</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #ff9500 0%, #ffcc00 100%);">
          <el-icon><Calendar /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.today_clicks }}</div>
          <div class="stat-label">今日访问</div>
        </div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-header">
          <span class="chart-title">访问趋势 (本周)</span>
        </div>
        <div ref="chartRef" class="chart-container"></div>
      </div>

      <div class="chart-card">
        <div class="chart-header">
          <span class="chart-title">热门标签 TOP 10</span>
        </div>
        <div class="top-tags">
          <div v-if="stats.top_tags?.length === 0" class="empty-text">
            暂无数据
          </div>
          <div
            v-for="(tag, index) in stats.top_tags"
            :key="tag.tag_id"
            class="top-tag-item"
          >
            <span class="tag-rank" :class="{ 'top-1': index === 0 }">{{ index + 1 }}</span>
            <span class="tag-code">{{ tag.url_code }}</span>
            <span class="tag-count">{{ tag.click_count }} 次</span>
          </div>
        </div>
      </div>
    </div>
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
  top_tags: [],
  week_daily_clicks: []
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
  const data = stats.week_daily_clicks && stats.week_daily_clicks.length === 7
    ? stats.week_daily_clicks
    : [0, 0, 0, 0, 0, 0, 0]

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: days,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#d2d2d7' } },
      axisLabel: { color: '#86868b' }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f5f5f7' } },
      axisLabel: { color: '#86868b' }
    },
    series: [
      {
        name: '访问次数',
        type: 'line',
        smooth: true,
        data: data,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 113, 227, 0.25)' },
            { offset: 1, color: 'rgba(0, 113, 227, 0.02)' }
          ])
        },
        lineStyle: {
          color: '#0071e3',
          width: 3
        },
        itemStyle: {
          color: '#0071e3'
        },
        symbol: 'circle',
        symbolSize: 8
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

/* iCloud Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 18px 20px;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
  min-height: 80px;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  flex-shrink: 0;
}

.stat-icon .el-icon {
  font-size: 20px;
  color: white;
}

.stat-content {
  flex: 1;
  min-width: 0;
  text-align: center;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #1d1d1f;
  line-height: 1.1;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.stat-value.highlight {
  color: #0071e3;
}

.stat-value.warning {
  color: #ff9500;
}

.stat-label {
  font-size: 12px;
  font-weight: 500;
  color: #86868b;
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

/* Charts Grid */
.charts-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}

.chart-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.chart-header {
  margin-bottom: 16px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
}

.chart-container {
  height: 240px;
}

/* Top Tags */
.top-tags {
  max-height: 260px;
  overflow-y: auto;
}

.empty-text {
  text-align: center;
  color: #86868b;
  padding: 40px 0;
  font-size: 14px;
}

.top-tag-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.top-tag-item:last-child {
  border-bottom: none;
}

.tag-rank {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: #f5f5f7;
  color: #86868b;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.tag-rank.top-1 {
  background: linear-gradient(135deg, #ffd700 0%, #ffb800 100%);
  color: white;
}

.tag-code {
  flex: 1;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 14px;
  font-weight: 500;
  color: #1d1d1f;
}

.tag-count {
  color: #0071e3;
  font-size: 13px;
  font-weight: 500;
}
</style>
