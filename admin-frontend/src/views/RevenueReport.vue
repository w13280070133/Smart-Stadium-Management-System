<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2>收益报表</h2>
        <p class="sub-title">汇总场地预约与商品售卖的收入，快速查看趋势</p>
      </div>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="label">今日总收入</div>
          <div class="value">¥ {{ formatMoney(overview.today_income) }}</div>
          <div class="sub">包含场地、商品等</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="label">本月总收入</div>
          <div class="value">¥ {{ formatMoney(overview.month_income) }}</div>
          <div class="sub">自然月内已入账总额</div>
        </div>
      </el-col>
    </el-row>

    <!-- 整体收入趋势，只保留场地 + 商品 + 总收入 -->
    <el-card class="chart-card" shadow="hover">
      <div class="chart-header">
        <div>
          <h3 class="chart-title">整体收入趋势</h3>
          <p class="chart-sub">近 {{ revenueDays }} 天场地/商品与总收入走势（退款为负）</p>
        </div>
        <div class="chart-tools">
          <el-radio-group v-model="revenueDays" size="small" @change="loadRevenueDaily">
            <el-radio-button :label="7">近 7 天</el-radio-button>
            <el-radio-button :label="30">近 30 天</el-radio-button>
            <el-radio-button :label="90">近 90 天</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div ref="revenueChartRef" class="chart-body"></div>
      <div v-if="!revenueDaily.dates.length" class="empty-text">近期暂无收入数据</div>
    </el-card>

    <!-- 原来的“培训报名收入趋势”整体移除；后续重做教培模块时再加回来 -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";
import * as echarts from "echarts";
import { ElMessage } from "element-plus";
import http from "../utils/http";

interface Overview {
  today_income: number;
  month_income: number;
}

interface RevenueDailyResp {
  date: string;
  reservation_amount: number;
  goods_amount: number;
  product_amount?: number;
  total_amount: number;
}

const overview = ref<Overview>({ today_income: 0, month_income: 0 });

const revenueDays = ref(30);
const revenueDaily = ref({
  dates: [] as string[],
  reservation: [] as number[],
  goods: [] as number[],
  total: [] as number[],
});

const revenueChartRef = ref<HTMLDivElement | null>(null);
let revenueChart: echarts.ECharts | null = null;

const formatMoney = (val: unknown) => {
  const n = Number(val);
  if (Number.isNaN(n)) return "0.00";
  return n.toFixed(2);
};

const loadOverview = async () => {
  try {
    const res = await http.get<any>("/reports/overview");
    const data = (res as any).data || {};
    overview.value.today_income = data.today_income || 0;
    overview.value.month_income = data.month_income || 0;
  } catch (err) {
    console.error(err);
    ElMessage.error("获取整体收入概况失败");
  }
};

const renderRevenueChart = () => {
  if (!revenueChartRef.value) return;
  if (!revenueChart) {
    revenueChart = echarts.init(revenueChartRef.value);
    window.addEventListener("resize", resizeCharts);
  }
  const option: echarts.EChartsCoreOption = {
    tooltip: {
      trigger: "axis",
      formatter: (params: any[]) => {
        const lines = params
          .map((p) => `${p.marker} ${p.seriesName}：¥${formatMoney(p.data)}`)
          .join("<br/>");
        return `${params[0]?.axisValue || ""}<br/>${lines}`;
      },
    },
    grid: { left: 40, right: 24, top: 40, bottom: 40 },
    legend: { top: 8 },
    xAxis: {
      type: "category",
      data: revenueDaily.value.dates,
      axisLabel: {
        formatter: (value: string) =>
          revenueDaily.value.dates.length > 15 ? value.slice(5) : value,
      },
    },
    yAxis: {
      type: "value",
      axisLabel: { formatter: (v: number) => `¥${v}` },
      splitLine: { lineStyle: { type: "dashed" } },
    },
    series: [
      {
        name: "场地收入",
        type: "line",
        smooth: true,
        data: revenueDaily.value.reservation,
        areaStyle: {},
      },
      {
        name: "商品收入",
        type: "line",
        smooth: true,
        data: revenueDaily.value.goods,
        areaStyle: {},
      },
      {
        name: "总收入",
        type: "line",
        smooth: true,
        data: revenueDaily.value.total,
        areaStyle: {},
        emphasis: { focus: "series" },
      },
    ],
  };
  revenueChart.setOption(option);
};

const resizeCharts = () => {
  if (revenueChart) revenueChart.resize();
};

const loadRevenueDaily = async () => {
  try {
    const res = await http.get<any>("/reports/revenue-daily", {
      params: { days: revenueDays.value },
    });
    const arr: RevenueDailyResp[] = (res as any).data || [];
    revenueDaily.value.dates = [];
    revenueDaily.value.reservation = [];
    revenueDaily.value.goods = [];
    revenueDaily.value.total = [];
    arr.forEach((item) => {
      revenueDaily.value.dates.push(item.date);
      revenueDaily.value.reservation.push(item.reservation_amount || 0);
      revenueDaily.value.goods.push(
        item.goods_amount ?? item.product_amount ?? 0
      );
      revenueDaily.value.total.push(item.total_amount || 0);
    });
    renderRevenueChart();
  } catch (err) {
    console.error(err);
    ElMessage.error("获取整体收入趋势失败");
  }
};

onMounted(async () => {
  await loadOverview();
  await loadRevenueDaily();
});

onBeforeUnmount(() => {
  if (revenueChart) {
    revenueChart.dispose();
    revenueChart = null;
  }
  window.removeEventListener("resize", resizeCharts);
});
</script>

<style scoped>
.page {
  padding: 16px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #F2F2F7;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sub-title {
  margin: 4px 0 0;
  font-size: 13px;
  color: #86868B;
}
.stat-row {
  margin-top: 8px;
}
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.stat-card.small {
  background: #fff;
}
.stat-card .label {
  font-size: 13px;
  color: #86868B;
}
.stat-card .value {
  margin-top: 6px;
  font-size: 22px;
  font-weight: 600;
  color: #1D1D1F;
}
.stat-card .sub {
  margin-top: 4px;
  font-size: 12px;
  color: #AEAEB2;
}
.chart-card {
  margin-top: 8px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.chart-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
}
.chart-sub {
  margin: 2px 0 0;
  font-size: 12px;
  color: #86868B;
}
.chart-body {
  width: 100%;
  height: 360px;
}
.empty-text {
  padding: 12px;
  text-align: center;
  font-size: 12px;
  color: #86868B;
}
</style>
