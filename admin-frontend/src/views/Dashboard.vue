<template>
  <div class="dashboard">
    <!-- Page Header -->
    <header class="page-header">
      <div>
        <h1>运营总览</h1>
        <p class="subtitle">实时查看场馆运营数据</p>
      </div>
      <div class="header-actions">
        <el-button @click="refreshAll">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="goReservations">管理预约</el-button>
      </div>
    </header>

    <!-- Stats Grid -->
    <section class="stats-section">
      <div class="stat-card">
        <div class="stat-label">会员总数</div>
        <div class="stat-value">{{ stats.memberCount }}</div>
        <div class="stat-desc">当前有效会员</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">账户余额</div>
        <div class="stat-value">¥ {{ formatMoney(stats.totalBalance) }}</div>
        <div class="stat-desc">账户余额总额</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">今日预约</div>
        <div class="stat-value">{{ stats.todayReservations }}</div>
        <div class="stat-desc">待使用场地</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">本月收入</div>
        <div class="stat-value">¥ {{ formatMoney(stats.monthRevenue) }}</div>
        <div class="stat-desc">累计营收</div>
      </div>
    </section>

    <!-- Charts Section -->
    <section class="charts-section">
      <div class="chart-card">
        <div class="card-header">
          <h3>营收趋势</h3>
          <span class="badge">近7日</span>
        </div>
        <div class="chart-container">
          <VChart v-if="!loading" :option="revenueChartOption" autoresize />
          <div v-else class="loading-placeholder">加载中...</div>
        </div>
      </div>
      <div class="chart-card">
        <div class="card-header">
          <h3>预约分布</h3>
          <span class="badge">按状态</span>
        </div>
        <div class="chart-container">
          <VChart v-if="!loading" :option="reservationChartOption" autoresize />
          <div v-else class="loading-placeholder">加载中...</div>
        </div>
      </div>
    </section>

    <!-- Recent Activity -->
    <section class="activity-section">
      <div class="activity-card">
        <div class="card-header">
          <h3>最近预约</h3>
          <el-button text size="small" @click="goReservations">查看全部</el-button>
        </div>
        <div class="activity-list">
          <div v-for="item in recentReservations" :key="item.id" class="activity-item">
            <div class="activity-time">{{ formatTime(item.start_time) }}</div>
            <div class="activity-content">
              <div class="activity-title">{{ item.court_name }}</div>
              <div class="activity-sub">{{ item.member_name }}</div>
            </div>
            <el-tag :type="getStatusType(item.status)" size="small">{{ item.status }}</el-tag>
          </div>
          <div v-if="recentReservations.length === 0" class="empty-state">暂无预约</div>
        </div>
      </div>

      <div class="activity-card">
        <div class="card-header">
          <h3>最近交易</h3>
          <el-button text size="small" @click="goTransactions">查看全部</el-button>
        </div>
        <div class="activity-list">
          <div v-for="item in recentTransactions" :key="item.id" class="activity-item">
            <div class="activity-content">
              <div class="activity-title">{{ item.type }}</div>
              <div class="activity-sub">{{ item.member_name }}</div>
            </div>
            <div class="transaction-amount" :class="item.amount >= 0 ? 'positive' : 'negative'">
              {{ item.amount >= 0 ? '+' : '' }}¥ {{ formatMoney(Math.abs(item.amount)) }}
            </div>
          </div>
          <div v-if="recentTransactions.length === 0" class="empty-state">暂无交易</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import http from '../utils/http'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const router = useRouter()
const loading = ref(false)

const stats = ref({
  memberCount: 0,
  totalBalance: 0,
  todayReservations: 0,
  monthRevenue: 0
})

const recentReservations = ref<any[]>([])
const recentTransactions = ref<any[]>([])
const revenueData = ref<any[]>([])
const reservationStats = ref<any[]>([])

const formatMoney = (val: number) => {
  return (val || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatTime = (time: string) => {
  if (!time) return ''
  return time.replace('T', ' ').slice(0, 16)
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    '待使用': 'warning',
    '已完成': 'success',
    '已取消': 'info'
  }
  return map[status] || 'info'
}

const revenueChartOption = computed(() => ({
  grid: { top: 20, right: 20, bottom: 30, left: 60 },
  xAxis: {
    type: 'category',
    data: revenueData.value.map(d => d.date),
    axisLine: { lineStyle: { color: '#E5E5EA' } },
    axisLabel: { color: '#86868B', fontSize: 12 }
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    splitLine: { lineStyle: { color: '#F2F2F7' } },
    axisLabel: { color: '#86868B', fontSize: 12, formatter: (v: number) => `¥${v}` }
  },
  tooltip: { trigger: 'axis' },
  series: [{
    type: 'line',
    data: revenueData.value.map(d => d.amount),
    smooth: true,
    lineStyle: { color: '#007AFF', width: 2 },
    areaStyle: { color: 'rgba(0, 122, 255, 0.1)' },
    itemStyle: { color: '#007AFF' }
  }]
}))

const reservationChartOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { color: '#86868B', fontSize: 12 } },
  series: [{
    type: 'pie',
    radius: ['50%', '70%'],
    center: ['50%', '45%'],
    data: reservationStats.value,
    label: { show: false },
    itemStyle: {
      borderRadius: 4,
      borderColor: '#fff',
      borderWidth: 2
    }
  }]
}))

const loadStats = async () => {
  try {
    const [membersRes, reservationsRes, transactionsRes] = await Promise.all([
      http.get('/members', { params: { page_size: 1000 } }),
      http.get('/court-reservations'),
      http.get('/member-transactions', { params: { page_size: 100 } })
    ])

    const members = membersRes.data?.items || membersRes.data || []
    const memberTotal = membersRes.data?.total ?? members.length
    const reservations = reservationsRes.data || []
    const transactions = transactionsRes.data?.items || transactionsRes.data || []

    // Stats
    stats.value.memberCount = memberTotal
    stats.value.totalBalance = members.reduce((sum: number, m: any) => sum + (m.balance || 0), 0)
    
    const today = new Date().toISOString().slice(0, 10)
    stats.value.todayReservations = reservations.filter((r: any) => 
      r.start_time?.startsWith(today) && r.status === '待使用'
    ).length

    const currentMonth = new Date().toISOString().slice(0, 7)
    stats.value.monthRevenue = transactions
      .filter((t: any) => t.created_at?.startsWith(currentMonth) && t.amount > 0)
      .reduce((sum: number, t: any) => sum + (t.amount || 0), 0)

    // Recent reservations
    recentReservations.value = reservations.slice(0, 5)

    // Recent transactions
    recentTransactions.value = transactions.slice(0, 5)

    // Reservation stats for pie chart
    const statusCount: Record<string, number> = {}
    reservations.forEach((r: any) => {
      statusCount[r.status] = (statusCount[r.status] || 0) + 1
    })
    reservationStats.value = Object.entries(statusCount).map(([name, value]) => ({
      name,
      value,
      itemStyle: { color: name === '待使用' ? '#FF9500' : name === '已完成' ? '#34C759' : '#86868B' }
    }))

    // Revenue trend (last 7 days)
    const last7Days: any[] = []
    for (let i = 6; i >= 0; i--) {
      const d = new Date()
      d.setDate(d.getDate() - i)
      const dateStr = d.toISOString().slice(0, 10)
      const dayTotal = transactions
        .filter((t: any) => t.created_at?.startsWith(dateStr) && t.amount > 0)
        .reduce((sum: number, t: any) => sum + (t.amount || 0), 0)
      last7Days.push({ date: dateStr.slice(5), amount: dayTotal })
    }
    revenueData.value = last7Days

  } catch (e) {
    console.error('Failed to load dashboard data:', e)
  }
}

const refreshAll = () => {
  loading.value = true
  loadStats().finally(() => { loading.value = false })
}

const goReservations = () => router.push('/court-reservations')
const goTransactions = () => router.push('/member-transactions')

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.dashboard {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Page Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #1D1D1F;
  margin: 0;
}

.subtitle {
  margin: 4px 0 0;
  font-size: 15px;
  color: #86868B;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* Stats Section */
.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

@media (max-width: 1200px) {
  .stats-section {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .stats-section {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.stat-label {
  font-size: 13px;
  color: #86868B;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 4px;
}

.stat-desc {
  font-size: 12px;
  color: #AEAEB2;
}

/* Charts Section */
.charts-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

@media (max-width: 900px) {
  .charts-section {
    grid-template-columns: 1fr;
  }
}

.chart-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h3 {
  font-size: 17px;
  font-weight: 600;
  color: #1D1D1F;
  margin: 0;
}

.badge {
  font-size: 12px;
  color: #007AFF;
  background: #E6F2FF;
  padding: 4px 10px;
  border-radius: 12px;
}

.chart-container {
  height: 240px;
}

.loading-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #86868B;
}

/* Activity Section */
.activity-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

@media (max-width: 900px) {
  .activity-section {
    grid-template-columns: 1fr;
  }
}

.activity-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #F9F9F9;
  border-radius: 8px;
}

.activity-time {
  font-size: 12px;
  color: #86868B;
  min-width: 100px;
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-title {
  font-size: 14px;
  font-weight: 500;
  color: #1D1D1F;
}

.activity-sub {
  font-size: 12px;
  color: #86868B;
  margin-top: 2px;
}

.transaction-amount {
  font-size: 14px;
  font-weight: 600;
}

.transaction-amount.positive {
  color: #34C759;
}

.transaction-amount.negative {
  color: #FF3B30;
}

.empty-state {
  text-align: center;
  padding: 32px;
  color: #86868B;
  font-size: 14px;
}
</style>
