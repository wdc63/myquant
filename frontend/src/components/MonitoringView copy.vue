<template>
  <div>
    <!-- Resuming Overlay -->
    <div v-if="isResuming" class="resuming-overlay">
      <div class="resuming-content">
        <div class="spinner"></div>
        <p>正在连接回测引擎...</p>
      </div>
    </div>

    <!-- Error Banner -->
    <div v-if="overview.strategy_error_today" class="error-banner">
      检测到策略代码今日运行时发生错误!请立即检查 <a href="#" @click.prevent="setActiveTab('logs')">运行日志</a> 以定位问题。
    </div>

    <!-- Header -->
    <div class="header">
      <div>
        <h1 id="main-title" style="display: inline-block; font-size: 22px; font-weight: 600; color: var(--primary-color);">
          {{ pageTitle }}
        </h1>
        <span id="real-time-clock" style="font-size: 16px; font-weight: 500; color: var(--header-info-color); margin-left: 16px;">
          {{ clockText }}
        </span>
        <div class="header-info" v-if="overview.strategy_name">
          策略: <strong>{{ overview.strategy_name }}</strong> |
          模式: <strong>{{ modeText }}</strong> |
          周期: {{ overview.start_date }} to {{ overview.end_date || 'N/A' }} |
          初始资金: <strong>{{ formatCurrency(overview.portfolio?.initial_cash) }}</strong>
        </div>
      </div>
      <div class="header-right">
        <span v-if="statusText" class="status-badge" :class="statusClass">{{ statusText }}</span>
        <div class="control-buttons" v-if="overview.is_running">
          <button class="btn" v-if="!overview.is_paused" @click="controlRun('pause')">暂停</button>
          <button class="btn" v-if="overview.is_paused" @click="controlRun('resume')">继续</button>
          <!-- 只有回测模式显示停止按钮 -->
          <button class="btn btn-danger" v-if="runMode === 'backtest'" @click="controlRun('stop')">停止</button>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <span
        v-for="tab in tabs"
        :key="tab.name"
        class="tab-link"
        :class="{ active: activeTab === tab.name }"
        @click="setActiveTab(tab.name)"
      >
        {{ tab.label }}
      </span>
    </div>

    <!-- Overview Tab -->
    <div v-show="activeTab === 'overview'" class="tab-content">
      <!-- 核心指标 -->
      <div class="section">
        <div class="section-title-container">
          <div class="section-title">核心指标</div>
        </div>
        <div class="metrics-grid" style="padding-top: 20px;">
          <div v-for="metric in overviewMetrics" :key="metric.l" class="metric-card">
            <div class="metric-label">{{ metric.l }}</div>
            <div class="metric-value" :class="metric.c">{{ metric.v }}</div>
          </div>
        </div>
      </div>

      <!-- 收益曲线 -->
      <div class="section">
        <div class="section-title-container">
          <div class="section-title">收益曲线</div>
          <div class="chart-tabs">
            <span
              class="chart-tab-link"
              :class="{ active: chartTab === 'historical' }"
              @click="switchChartTab('historical')"
            >
              历史收益
            </span>
            <span
              class="chart-tab-link"
              :class="{ active: chartTab === 'intraday' }"
              @click="switchChartTab('intraday')"
            >
              当日收益
            </span>
          </div>
        </div>

        <!-- 历史收益图表 -->
        <div v-show="chartTab === 'historical'" class="chart-tab-content">
          <div ref="equityChartRef" class="chart-container"></div>
        </div>

        <!-- 当日收益图表 -->
        <div v-show="chartTab === 'intraday'" class="chart-tab-content">
          <div ref="intradayChartRef" class="chart-container" v-show="hasIntradayData"></div>
          <div class="chart-container-placeholder" v-show="!hasIntradayData">
            当日收益曲线未启用或暂无数据
          </div>
        </div>
      </div>

      <!-- 风险指标 -->
      <div class="section">
        <div class="section-title-container">
          <div class="section-title">风险指标 (盘后更新)</div>
        </div>
        <div class="metrics-grid" style="padding-top: 20px;">
          <div v-for="metric in riskMetrics" :key="metric.key" class="metric-card">
            <div class="metric-label">{{ metric.key }}</div>
            <div class="metric-value" :class="getValueClass(metric.raw)">{{ metric.value }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Performance Tab -->
    <div v-show="activeTab === 'performance'" class="tab-content">
      <div class="section">
        <div class="section-title-container">
          <div class="section-title">交易统计</div>
        </div>
        <div class="metrics-grid" style="padding-top: 20px;">
          <div v-for="metric in tradeMetrics" :key="metric.key" class="metric-card">
            <div class="metric-label">{{ metric.key }}</div>
            <div class="metric-value" :class="getTradeMetricClass(metric)">{{ metric.value }}</div>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-title-container">
          <div class="section-title">交易对明细</div>
        </div>
        <div class="table-wrapper">
          <el-table :data="pnlPairs" stripe>
            <el-table-column prop="symbol" label="代码" />
            <el-table-column prop="symbol_name" label="名称" />
            <el-table-column prop="direction" label="方向">
              <template #default="{ row }">
                <span :class="row.direction === 'long' ? 'positive' : 'negative'">
                  {{ row.direction === 'long' ? '多头' : '空头' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="entry_time" label="开仓时间" />
            <el-table-column prop="exit_time" label="平仓时间" />
            <el-table-column prop="hold_days" label="持仓天数" />
            <el-table-column prop="entry_price" label="开仓价">
              <template #default="{ row }">{{ formatCurrency(row.entry_price) }}</template>
            </el-table-column>
            <el-table-column prop="exit_price" label="平仓价">
              <template #default="{ row }">{{ formatCurrency(row.exit_price) }}</template>
            </el-table-column>
            <el-table-column prop="amount" label="数量" />
            <el-table-column prop="total_commission" label="手续费">
              <template #default="{ row }">{{ formatCurrency(row.total_commission) }}</template>
            </el-table-column>
            <el-table-column prop="net_pnl" label="净盈亏">
              <template #default="{ row }">
                <span :class="getValueClass(row.net_pnl)">{{ formatCurrency(row.net_pnl) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="net_pnl_ratio" label="盈亏率">
              <template #default="{ row }">
                <span :class="getValueClass(row.net_pnl_ratio)">{{ formatPercent(row.net_pnl_ratio) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-pagination
          v-model:current-page="pnlCurrentPage"
          v-model:page-size="pnlPageSize"
          :total="pnlPairsAll.length"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          style="margin-top: 16px; justify-content: center;"
        />
      </div>
    </div>

    <!-- Positions Tab -->
    <div v-show="activeTab === 'positions'" class="tab-content">
      <div class="section">
        <div class="section-title-container">
          <div class="section-title">每日持仓快照</div>
        </div>
        <div class="table-wrapper">
          <el-table :data="dailyPositions" stripe>
            <el-table-column prop="date" label="日期" />
            <el-table-column prop="symbol" label="代码" />
            <el-table-column prop="symbol_name" label="名称" />
            <el-table-column prop="direction" label="方向">
              <template #default="{ row }">
                <span :class="row.direction === 'long' ? 'positive' : (row.direction === 'short' ? 'negative' : '')">
                  {{ row.direction === 'long' ? '多头' : (row.direction === 'short' ? '空头' : '-') }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="数量" />
            <el-table-column prop="close_price" label="收盘价">
              <template #default="{ row }">
                {{ row.symbol_name === '现金' ? '-' : formatCurrency(row.close_price) }}
              </template>
            </el-table-column>
            <el-table-column prop="market_value" label="市值">
              <template #default="{ row }">{{ formatCurrency(row.market_value) }}</template>
            </el-table-column>
            <el-table-column prop="daily_pnl" label="当日盈亏">
              <template #default="{ row }">
                <span :class="row.symbol_name === '现金' ? '' : getValueClass(row.daily_pnl)">
                  {{ row.symbol_name === '现金' ? '-' : formatCurrency(row.daily_pnl) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="daily_pnl_ratio" label="当日盈亏率">
              <template #default="{ row }">
                <span :class="row.symbol_name === '现金' ? '' : getValueClass(row.daily_pnl_ratio)">
                  {{ row.symbol_name === '现金' ? '-' : formatPercent(row.daily_pnl_ratio) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-pagination
          v-model:current-page="posCurrentPage"
          v-model:page-size="posPageSize"
          :total="dailyPositionsAll.length"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          style="margin-top: 16px; justify-content: center;"
        />
      </div>
    </div>

    <!-- Orders Tab -->
    <div v-show="activeTab === 'orders'" class="tab-content">
      <div class="section">
        <div class="section-title-container">
          <div class="section-title">全部订单</div>
        </div>
        <div class="table-wrapper">
          <el-table :data="ordersDisplay" stripe>
            <el-table-column prop="created_time" label="创建时间" />
            <el-table-column prop="filled_time" label="成交时间" />
            <el-table-column prop="symbol" label="代码" />
            <el-table-column prop="side" label="方向">
              <template #default="{ row }">
                <span :class="row.side === 'buy' ? 'positive' : 'negative'">
                  {{ row.side === 'buy' ? '买入' : '卖出' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" />
            <el-table-column prop="amount" label="数量" />
            <el-table-column prop="filled_price" label="成交均价">
              <template #default="{ row }">{{ formatCurrency(row.filled_price) }}</template>
            </el-table-column>
            <el-table-column prop="commission" label="手续费">
              <template #default="{ row }">{{ formatCurrency(row.commission) }}</template>
            </el-table-column>
          </el-table>
        </div>
        <el-pagination
          v-model:current-page="orderCurrentPage"
          v-model:page-size="orderPageSize"
          :total="ordersAll.length"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          style="margin-top: 16px; justify-content: center;"
        />
      </div>
    </div>

    <!-- Logs Tab -->
    <div v-show="activeTab === 'logs'" class="tab-content">
      <div class="section">
        <div class="section-title-container">
          <div class="section-title">运行日志</div>
        </div>
        <div class="logs-container" ref="logsContainerRef" style="margin-top: 20px;">
          <div v-if="logs.length === 0" class="no-data">暂无日志</div>
          <div v-for="(log, index) in logs" :key="index" class="log-entry">
            <div class="log-time-group">
              <span class="log-sim-time">Sim: {{ log.sim_time }}</span>
              <span class="log-exec-time">Exec: {{ log.exec_time }}</span>
            </div>
            <span class="log-level" :class="`log-level-${log.level}`">[{{ log.level }}]</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Snapshots Tab -->
    <div v-show="activeTab === 'snapshots'" class="tab-content">
      <div class="snapshots-container">
        <div class="section">
          <div class="section-title-container">
            <div class="section-title">策略代码</div>
          </div>
          <div class="snapshot-editor-wrapper">
            <Editor :model-value="snapshots.code" language="python" :theme="editorTheme" :read-only="true" />
          </div>
        </div>
        <div class="section">
          <div class="section-title-container">
            <div class="section-title">配置文件</div>
          </div>
          <div class="snapshot-editor-wrapper">
            <Editor :model-value="snapshots.config" language="yaml" :theme="editorTheme" :read-only="true" />
          </div>
        </div>
        <div class="section">
          <div class="section-title-container">
            <div class="section-title">数据提供者</div>
          </div>
          <div class="snapshot-editor-wrapper">
            <Editor :model-value="snapshots.data_provider" language="python" :theme="editorTheme" :read-only="true" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import apiClient from '../api/axios';
import { createSocketConnection } from '../api/socket';
import * as echarts from 'echarts';
import { ElMessage, ElMessageBox, ElTable, ElTableColumn, ElPagination } from 'element-plus';
import Editor from './Editor.vue';

// Throttle 函数：限制函数执行频率
function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

const props = defineProps({
  runId: String,
  initialStatus: String,
});

const router = useRouter();
const isUnmounting = ref(false);

// 连接状态标记
const hasReceivedData = ref(false);  // 是否已接收过数据
const isFirstConnect = ref(true);     // 是否首次连接
const runMode = ref(null);          // 运行模式(从props或URL解析)
const isResuming = ref(false);      // 新增：用于显示恢复中的加载提示

// THEME
const isDark = ref(document.body.classList.contains('dark-mode'));
const editorTheme = computed(() => isDark.value ? 'vs-dark' : 'vs');
const themeObserver = new MutationObserver(() => {
  isDark.value = document.body.classList.contains('dark-mode');
});
onMounted(() => themeObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] }));
onBeforeUnmount(() => themeObserver.disconnect());

// DATA
const currentData = ref({});
const overview = computed(() => currentData.value.overview || {});
const performance = computed(() => currentData.value.performance || {});
const positions = computed(() => currentData.value.positions || {});
const logs = computed(() => (currentData.value.logs || {}).logs || []);
const snapshots = computed(() => currentData.value.snapshots || {});

// UI STATE
const activeTab = ref('overview');
const chartTab = ref('historical');
const tabs = [
  { name: 'overview', label: '概览' },
  { name: 'performance', label: '性能分析' },
  { name: 'positions', label: '每日持仓' },
  { name: 'orders', label: '订单流水' },
  { name: 'logs', label: '运行日志' },
  { name: 'snapshots', label: '代码快照' },
];

const setActiveTab = (tabName) => {
  activeTab.value = tabName;
  if (tabName === 'overview') {
    nextTick(() => {
      if (equityChart) equityChart.resize();
      if (intradayChart) intradayChart.resize();
    });
  }
};

const switchChartTab = (tabName) => {
  chartTab.value = tabName;
  nextTick(() => {
    if (tabName === 'historical' && equityChart) {
      equityChart.resize();
    } else if (tabName === 'intraday' && intradayChart) {
      intradayChart.resize();
    }
  });
};

// COMPUTED PROPERTIES
const modeText = computed(() => {
  return overview.value.mode === 'simulation'
    ? `模拟交易 (${overview.value.market_phase || '...'})`
    : '历史回测';
});

const clockText = computed(() => {
  if (!overview.value.current_dt) return '';
  const timeLabel = overview.value.mode === 'simulation' ? '当前时间' : '回测时间';
  return `${timeLabel}: ${overview.value.current_dt}`;
});

const pageTitle = computed(() => {
  const strategyName = overview.value.strategy_name;
  const mode = overview.value.mode;

  if (!strategyName) {
    return '实时监控';
  }

  if (mode === 'simulation') {
    return `模拟交易: ${strategyName}`;
  } else {
    return `历史回测: ${strategyName}`;
  }
});

const statusText = computed(() => {
  if (!overview.value.is_running && !overview.value.is_paused) return '已结束';
  if (overview.value.is_paused) return '已暂停';
  return '运行中';
});

const statusClass = computed(() => {
  if (!overview.value.is_running && !overview.value.is_paused) return 'status-stopped';
  if (overview.value.is_paused) return 'status-paused';
  return 'status-running';
});

const formatCurrency = (n) => `¥${(n != null ? n : 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const formatPercent = (n) => `${((n || 0) * 100).toFixed(2)}%`;
const getValueClass = (n) => (n > 0) ? 'positive' : (n < 0) ? 'negative' : 'neutral-value';

const overviewMetrics = computed(() => {
  const p = overview.value.portfolio || {};
  const b = overview.value.benchmark || {};
  const alpha = p.returns - (b.returns || 0);
  return [
    { l: '账户净资产', v: formatCurrency(p.net_worth) },
    { l: '总资产', v: formatCurrency(p.total_assets) },
    { l: '账户现金', v: formatCurrency(p.cash) },
    { l: '多头市值', v: formatCurrency(p.long_positions_value) },
    { l: '空头负债', v: formatCurrency(p.short_positions_value), c: p.short_positions_value > 0 ? 'negative' : '' },
    { l: '净持仓市值', v: formatCurrency(p.net_positions_value) },
    { l: '已用保证金', v: formatCurrency(p.margin) },
    { l: '可用资金', v: formatCurrency(p.available_cash) },
    { l: '策略收益率', v: formatPercent(p.returns), c: getValueClass(p.returns) },
    { l: '基准收益率', v: formatPercent(b.returns), c: getValueClass(b.returns) },
    { l: '超额收益', v: formatPercent(alpha), c: getValueClass(alpha) },
  ];
});

const riskMetrics = computed(() => overview.value.risk_metrics || []);
const tradeMetrics = computed(() => performance.value.trade_metrics || []);

// 分页相关状态
const pnlCurrentPage = ref(1);
const pnlPageSize = ref(15);
const posCurrentPage = ref(1);
const posPageSize = ref(15);
const orderCurrentPage = ref(1);
const orderPageSize = ref(15);

// 完整数据（用于计算总数）
const pnlPairsAll = computed(() => (performance.value.pnl_pairs || []).sort((a, b) => (b.exit_time || '').localeCompare(a.exit_time || '')));
const dailyPositionsAll = computed(() => (positions.value.daily_positions || []).flatMap(s => s.positions.map(p => ({ ...p, date: s.date }))));
const ordersAll = computed(() => (currentData.value.orders || {}).orders || []);

// 分页后的数据
const pnlPairs = computed(() => {
  const start = (pnlCurrentPage.value - 1) * pnlPageSize.value;
  const end = start + pnlPageSize.value;
  return pnlPairsAll.value.slice(start, end);
});

const dailyPositions = computed(() => {
  const start = (posCurrentPage.value - 1) * posPageSize.value;
  const end = start + posPageSize.value;
  return dailyPositionsAll.value.slice(start, end);
});

const ordersDisplay = computed(() => {
  const start = (orderCurrentPage.value - 1) * orderPageSize.value;
  const end = start + orderPageSize.value;
  return ordersAll.value.slice(start, end);
});

const hasIntradayData = computed(() => {
  const intradayData = overview.value.intraday_equity;
  return intradayData && intradayData.enabled && intradayData.data && intradayData.data.returns && intradayData.data.returns.length >= 2;
});

const getTradeMetricClass = (metric) => {
  const neutralMetrics = ["总手续费", "利润因子", "总交易次数", "盈亏比", "平均持仓天数"];
  if (neutralMetrics.includes(metric.key)) return 'neutral-value';
  if (metric.key === '胜率') return metric.raw >= 0.5 ? 'positive' : 'negative';
  return getValueClass(metric.raw);
};

// API & SOCKETS
let socket = null;

const controlRun = async (action) => {
  // 回测模式下停止按钮需要二次确认
  if (action === 'stop' && overview.value.mode === 'backtest') {
    try {
      await ElMessageBox.confirm(
        '停止回测将生成最终报告,确定要停止吗?',
        '确认停止',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      );
    } catch {
      return; // 用户取消
    }
  }

  apiClient.post(`/runs/${props.runId}/control`, { action })
    .then(() => {
      const actionText = action === 'pause' ? '暂停' : action === 'resume' ? '继续' : '停止';
      ElMessage.success(`${actionText}成功`);
    })
    .catch(() => {
      const actionText = action === 'pause' ? '暂停' : action === 'resume' ? '继续' : '停止';
      ElMessage.error(`${actionText}失败`);
    });
};

const updateUI = (data) => {
  currentData.value = data;
  hasReceivedData.value = true;  // 标记已成功接收数据
  if (isResuming.value) {
    isResuming.value = false; // 收到数据后，隐藏加载提示
  }
};

const navigateToReport = () => {
  router.push({ name: 'ReportView', params: { runId: props.runId } });
};

const handleRunEnd = () => {
  if (isUnmounting.value) {
    return;
  }

  // 如果还没收到过数据,可能只是初次连接失败,静默等待重连
  if (!hasReceivedData.value) {
    console.log('Socket连接失败,等待自动重连...');
    return;
  }

  // 已经运行过,现在断开,检查是否真的结束
  const mode = runMode.value === 'simulation' ? '模拟' : '回测';
  ElMessage.info(`${mode}已结束，正在生成报告...`);

  apiClient.get(`/runs/${props.runId}/final_status`)
    .then(res => {
      if (res.data.report_ready) {
        navigateToReport();
      } else {
        ElMessage.error(`${mode}未能成功生成报告，请检查日志`);
      }
    })
    .catch(err => {
      console.error("获取最终状态失败:", err);
      ElMessage.error("连接超时或出现错误，请刷新页面查看");
    });
};

const setupSocket = (port) => {
  if (socket) socket.disconnect();

  socket = createSocketConnection(port);

  socket.on('connect', () => {
    // 只在首次连接时提示,避免重连时重复提示
    if (isFirstConnect.value) {
      const mode = overview.value.mode === 'simulation' ? '模拟' : '回测';
      ElMessage.success(`已连接${mode}引擎`);
      isFirstConnect.value = false;

      // 连接成功后再获取初始数据
      setTimeout(() => {
        fetch(`http://localhost:${port}/api/initial_data`)
          .then(response => response.json())
          .then(initialData => updateUI(initialData))
          .catch(e => console.error("获取初始数据失败:", e));
      }, 500);
    }
  });

  socket.on('update', updateUI);

  socket.on('connect_error', handleRunEnd);
  socket.on('disconnect', handleRunEnd);

  socket.connect();
};

onMounted(() => {
  // 从URL解析运行模式
  runMode.value = window.location.pathname.includes('simulation') ? 'simulation' : 'backtest';

  apiClient.get(`/runs/${props.runId}/status`)
    .then(res => {
      const { status, port } = res.data;
      if (status === 'running' && port) {
        setupSocket(port);
        // 初始数据的获取已移到 setupSocket 的 connect 事件中
      } else if (status === 'paused') {
        isResuming.value = true;
        apiClient.post(`/runs/${props.runId}/resume`, { start_paused: true })
          .then(resumeRes => {
            // 轮询状态直到获取到新端口
            const pollForStatus = (retries = 15) => {
              if (isUnmounting.value) return;
              if (retries <= 0) {
                isResuming.value = false;
                ElMessage.error("恢复超时，请刷新重试");
                return;
              }
              apiClient.get(`/runs/${props.runId}/status`)
                .then(statusRes => {
                  const newPort = statusRes.data.port;
                  if (statusRes.data.status === 'running' && newPort) {
                    setupSocket(newPort);
                  } else {
                    setTimeout(() => pollForStatus(retries - 1), 1000);
                  }
                })
                .catch(() => {
                  setTimeout(() => pollForStatus(retries - 1), 1000);
                });
            };
            pollForStatus();
          })
          .catch(e => {
            isResuming.value = false;
            const message = e.response?.data?.error || '加载暂停状态失败';
            ElMessage.error(message);
          });
      } else if (status === 'finished' || status === 'interrupted') {
        navigateToReport();
      } else {
        ElMessage.error(`无法获取运行状态或运行已损坏: ${status}`);
      }
    })
    .catch(e => {
      console.error("获取运行状态失败:", e);
      ElMessage.error("获取运行状态失败，请刷新重试")
    });
});

onBeforeUnmount(() => {
  isUnmounting.value = true;
  if (socket) {
    socket.disconnect();
  }
});

// LOGS
const logsContainerRef = ref(null);
watch(logs, async () => {
  await nextTick();
  const container = logsContainerRef.value;
  if (container) {
    const isScrolledUp = container.scrollTop + container.clientHeight < container.scrollHeight - 20;
    if (!isScrolledUp) {
      container.scrollTop = container.scrollHeight;
    }
  }
}, { deep: true });

// CHARTS
const equityChartRef = ref(null);
const intradayChartRef = ref(null);
let equityChart = null;
let intradayChart = null;

const renderEquityChart = () => {
  const data = overview.value.equity_curve;
  if (!equityChart || !data || !data.dates || data.dates.length === 0) return;

  const { dates, strategy_values, benchmark_values, initial_cash } = data;
  const benchmarkInfo = overview.value.benchmark || {};
  const benchmarkLegendName = (benchmarkInfo && benchmarkInfo.name) ? `基准 (${benchmarkInfo.name})` : '基准 (未设置)';
  const hasBenchmark = benchmark_values && benchmark_values.length > 0;

  // 计算Y轴范围
  const allValues = hasBenchmark ? [...strategy_values, ...benchmark_values] : [...strategy_values];
  const minValue = Math.min(...allValues);
  const maxValue = Math.max(...allValues);
  const valueRange = maxValue - minValue;
  const valueMargin = valueRange * 0.1;
  const yMinValue = Math.floor((minValue - valueMargin) / 1000) * 1000;
  const yMaxValue = Math.ceil((maxValue + valueMargin) / 1000) * 1000;
  const yMinReturn = ((yMinValue / initial_cash) - 1) * 100;
  const yMaxReturn = ((yMaxValue / initial_cash) - 1) * 100;

  const gridLineStyle = {
    type: 'solid',
    color: isDark.value ? 'rgba(255, 255, 255, 0.1)' : '#f0f0f0',
    width: 1,
    opacity: 0.5
  };

  const legendData = ['策略'];
  if (hasBenchmark) legendData.push(benchmarkLegendName);

  const series = [
    {
      name: '策略',
      type: 'line',
      smooth: true,
      data: strategy_values,
      yAxisIndex: 0,
      showSymbol: false,
      lineStyle: { width: 2.5, color: '#3b82f6' },
      itemStyle: { color: '#3b82f6' },
      emphasis: { focus: 'series' }
    }
  ];

  if (hasBenchmark) {
    series.push({
      name: benchmarkLegendName,
      type: 'line',
      smooth: true,
      data: benchmark_values,
      yAxisIndex: 0,
      showSymbol: false,
      lineStyle: { width: 2.5, color: '#10b981' },
      itemStyle: { color: '#10b981' },
      emphasis: { focus: 'series' }
    });
  }

  const option = {
    backgroundColor: isDark.value ? '#100c2a' : '#f8fafc',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: isDark.value ? '#242830' : '#ffffff',
      borderColor: isDark.value ? '#3d4451' : '#e2e8f0',
      textStyle: { color: isDark.value ? '#e4e6eb' : '#2c3e50' },
      formatter: function (params) {
        const date = params[0].axisValue;
        const strategy = params.find(p => p.seriesName === '策略');
        const benchmark = params.find(p => p.seriesName === benchmarkLegendName);
        let html = `<div style="padding: 8px; font-size: 13px;"><div style="margin-bottom: 6px; font-weight: 600;">${date}</div>`;
        if (strategy) {
          const strategyValue = strategy.data;
          const strategyReturn = ((strategyValue / initial_cash - 1) * 100).toFixed(2);
          const strategyColor = strategyReturn >= 0 ? '#ef4444' : '#10b981';
          html += `<div style="margin-bottom: 4px;"><span style="display:inline-block;width:10px;height:10px;background:#3b82f6;border-radius:50%;margin-right:5px;"></span><strong>策略</strong>: ${formatCurrency(strategyValue)} <span style="color: ${strategyColor};">(${strategyReturn}%)</span></div>`;
        }
        if (benchmark) {
          const benchmarkValue = benchmark.data;
          const benchmarkReturn = ((benchmarkValue / initial_cash - 1) * 100).toFixed(2);
          const benchmarkColor = benchmarkReturn >= 0 ? '#ef4444' : '#10b981';
          html += `<div><span style="display:inline-block;width:10px;height:10px;background:#10b981;border-radius:50%;margin-right:5px;"></span><strong>${benchmarkLegendName}</strong>: ${formatCurrency(benchmarkValue)} <span style="color: ${benchmarkColor};">(${benchmarkReturn}%)</span></div>`;
        }
        html += `</div>`;
        return html;
      }
    },
    legend: { data: legendData, top: 0, textStyle: { color: isDark.value ? '#e4e6eb' : '#2c3e50' } },
    grid: { left: '3%', right: '5%', bottom: '15%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLabel: {
        interval: Math.floor(dates.length / 15),
        rotate: 0,
        fontSize: 11,
        margin: 12
      },
      splitLine: { show: true, lineStyle: gridLineStyle }
    },
    yAxis: [
      {
        type: 'value',
        name: '资产(元)',
        position: 'left',
        min: yMinValue,
        max: yMaxValue,
        axisLabel: { formatter: '¥{value}', fontSize: 11 },
        splitLine: { show: true, lineStyle: gridLineStyle }
      },
      {
        type: 'value',
        name: '收益率(%)',
        position: 'right',
        min: yMinReturn.toFixed(0),
        max: yMaxReturn.toFixed(0),
        axisLabel: { formatter: '{value}%', fontSize: 11 },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', start: 0, end: 100, bottom: 5 }
    ],
    series: series
  };
  equityChart.setOption(option, true);
};

const renderIntradayChart = () => {
  const intradayData = overview.value.intraday_equity;

  if (!intradayChart) return;

  const hasData = intradayData && intradayData.enabled && intradayData.data && intradayData.data.returns && intradayData.data.returns.length >= 2;

  if (hasData) {
    const strategyReturns = intradayData.data.returns;
    const benchmarkReturns = (intradayData.benchmark_data && intradayData.benchmark_data.returns) ? intradayData.benchmark_data.returns : [];

    const allReturns = [...strategyReturns, ...benchmarkReturns];
    let yMin = Math.min(0, ...allReturns);
    let yMax = Math.max(0, ...allReturns);
    const range = yMax - yMin;
    yMin -= range * 0.1;
    yMax += range * 0.1;

    const benchmarkInfo = overview.value.benchmark || {};
    const benchmarkDisplayName = (benchmarkInfo && benchmarkInfo.name) ? `基准 (${benchmarkInfo.name})` : '基准 (未设置)';
    const hasBenchmark = benchmarkReturns.length > 0;

    const legendData = ['策略'];
    if (hasBenchmark) legendData.push(benchmarkDisplayName);

    const seriesData = [
      {
        name: '策略',
        data: strategyReturns,
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: '#3b82f6' },
        itemStyle: { color: '#3b82f6' },
        emphasis: { focus: 'series', lineStyle: { width: 2.5 } }
      }
    ];

    if (hasBenchmark) {
      seriesData.push({
        name: benchmarkDisplayName,
        data: benchmarkReturns,
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: '#f59e0b' },
        itemStyle: { color: '#f59e0b' },
        emphasis: { focus: 'series', lineStyle: { width: 2.5 } }
      });
    }

    const option = {
      backgroundColor: isDark.value ? '#100c2a' : '#f8fafc',
      title: {
        text: `当日收益 (${intradayData.current_date || ''})`,
        left: 'center',
        textStyle: { fontSize: 16, fontWeight: 'normal' }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } },
        backgroundColor: isDark.value ? '#242830' : '#ffffff',
        borderColor: isDark.value ? '#3d4451' : '#e2e8f0',
        textStyle: { color: isDark.value ? '#e4e6eb' : '#2c3e50' },
        formatter: function(params) {
          const time = params[0].axisValue;
          const dataIndex = params[0].dataIndex;
          let tooltipText = `<div style="padding: 8px; font-size: 13px;"><div style="margin-bottom: 6px; font-weight: 600;">${time}</div>`;

          const strategyParam = params.find(p => p.seriesName === '策略');
          const benchmarkParam = params.find(p => p.seriesName === benchmarkDisplayName);

          if (strategyParam) {
            const returns = strategyParam.value;
            const value = intradayData.data.values[dataIndex];
            const returnColor = returns >= 0 ? '#ef4444' : '#10b981';
            tooltipText += `<div><span style="display:inline-block;width:10px;height:10px;background:${strategyParam.color};border-radius:50%;margin-right:5px;"></span><strong>策略</strong>: <span style="color: ${returnColor}; font-weight:bold;">${returns.toFixed(2)}%</span> (${formatCurrency(value)})</div>`;
          }
          if (benchmarkParam) {
            const returns = benchmarkParam.value;
            const returnColor = returns >= 0 ? '#ef4444' : '#10b981';
            tooltipText += `<div><span style="display:inline-block;width:10px;height:10px;background:${benchmarkParam.color};border-radius:50%;margin-right:5px;"></span><strong>${benchmarkDisplayName}</strong>: <span style="color: ${returnColor}; font-weight:bold;">${returns.toFixed(2)}%</span></div>`;
          }
          tooltipText += `</div>`;
          return tooltipText;
        }
      },
      legend: { data: legendData, top: 30 },
      grid: { left: '3%', right: '3%', bottom: '3%', top: '20%', containLabel: true },
      xAxis: { type: 'category', data: intradayData.data.times },
      yAxis: {
        type: 'value',
        scale: true,
        min: yMin.toFixed(1),
        max: yMax.toFixed(1),
        axisLabel: { formatter: '{value}%', fontSize: 11 }
      },
      series: seriesData
    };
    intradayChart.setOption(option, true);
  }
};

// 创建 throttled 版本的图表渲染函数，限制更新频率为每500ms最多一次
const throttledRenderEquityChart = throttle(renderEquityChart, 500);
const throttledRenderIntradayChart = throttle(renderIntradayChart, 500);

// 监听数据变化，使用 throttled 版本来避免频繁重绘
// 使用 currentData 而不是 overview，避免深度监听
watch(currentData, () => {
  if (equityChart) throttledRenderEquityChart();
  if (intradayChart) throttledRenderIntradayChart();
});

// 监听主题变化时立即重新初始化图表（不使用 throttle）
watch(isDark, (newVal) => {
  if (equityChart) {
    equityChart.dispose();
    equityChart = echarts.init(equityChartRef.value, newVal ? 'dark' : null);
    renderEquityChart();
  }
  if (intradayChart) {
    intradayChart.dispose();
    intradayChart = echarts.init(intradayChartRef.value, newVal ? 'dark' : null);
    renderIntradayChart();
  }
});

onMounted(() => {
  if (equityChartRef.value) {
    equityChart = echarts.init(equityChartRef.value, isDark.value ? 'dark' : null);
    renderEquityChart();
    window.addEventListener('resize', () => equityChart.resize());
  }
  if (intradayChartRef.value) {
    intradayChart = echarts.init(intradayChartRef.value, isDark.value ? 'dark' : null);
    renderIntradayChart();
    window.addEventListener('resize', () => intradayChart.resize());
  }
});
</script>

<style scoped>
/* 基础样式 */
.header {
  background: var(--card-bg);
  padding: 16px 24px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info {
  font-size: 13px;
  color: var(--header-info-color);
  margin-top: 4px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 12px;
}

.status-running {
  background-color: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.status-paused {
  background-color: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.status-stopped {
  background-color: rgba(100, 116, 139, 0.1);
  color: #64748b;
}

.btn {
  padding: 6px 14px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--card-bg);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-primary);
}

.btn:hover {
  background: var(--table-hover-bg);
}

.btn-danger {
  color: #ef4444;
  border-color: #ef4444;
}

.btn-danger:hover {
  background: rgba(239, 68, 68, 0.1);
}

.control-buttons {
  display: flex;
  gap: 8px;
}

/* Tabs */
.tabs {
  display: flex;
  border-bottom: 2px solid var(--tab-border-color);
  margin-bottom: 20px;
}

.tab-link {
  padding: 10px 18px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  color: var(--tab-inactive-color);
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.tab-link.active {
  color: var(--tab-active-color);
  border-bottom-color: var(--tab-active-color);
}

.tab-content {
  display: block;
}

/* Section */
.section {
  --section-padding-inline: 24px;
  background: var(--card-bg);
  padding: 24px var(--section-padding-inline);
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
}

.section-title-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--tab-border-color);
  margin-bottom: 20px;
  padding-bottom: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.table-wrapper {
  margin: 20px calc(-1 * var(--section-padding-inline)) 0;
  padding: 0 var(--section-padding-inline) 12px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.table-wrapper:last-child {
  margin-bottom: 0;
}

/* Chart tabs */
.chart-tabs {
  display: flex;
}

.chart-tab-link {
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--tab-inactive-color);
  border-bottom: 2px solid transparent;
}

.chart-tab-link.active {
  color: var(--tab-active-color);
  border-bottom-color: var(--tab-active-color);
}

.chart-tab-content {
  display: block;
}

.chart-container-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 450px;
  color: var(--header-info-color);
  font-size: 16px;
  background-color: var(--table-header-bg);
  border-radius: 6px;
}

/* Metrics */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.metric-card {
  background: var(--table-header-bg);
  border-radius: 6px;
  padding: 12px 16px;
  border-left: 3px solid var(--primary-color);
}

.metric-label {
  font-size: 13px;
  color: var(--header-info-color);
  margin-bottom: 4px;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
}

.neutral-value {
  color: var(--text-primary) !important;
}

.positive {
  color: var(--positive-color) !important;
}

.negative {
  color: var(--negative-color) !important;
}

/* Chart */
.chart-container {
  height: 450px;
}

/* Logs */
.logs-container {
  max-height: 400px;
  overflow-y: auto;
  background: var(--bg-primary);
  padding: 12px;
  border-radius: 6px;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 12.5px;
}

.log-entry {
  display: flex;
  flex-wrap: nowrap;
  gap: 0.8rem;
  line-height: 1.5;
  margin-bottom: 2px;
}

.log-time-group {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  color: var(--header-info-color);
  white-space: nowrap;
  font-size: 11.5px;
  text-align: right;
  border-right: 1px solid var(--border-color);
  padding-right: 0.8rem;
}

.log-sim-time {
  font-weight: 500;
  color: var(--text-primary);
}

.log-exec-time {
  font-size: 10.5px;
}

.log-level {
  font-weight: 600;
  white-space: nowrap;
}

.log-message {
  flex-grow: 1;
  white-space: pre-wrap;
  word-break: break-all;
}

.log-level-INFO {
  color: var(--tab-inactive-color);
}

.log-level-WARNING {
  color: var(--warning-color);
}

.log-level-ERROR {
  color: var(--positive-color);
}

.log-level-DEBUG {
  color: var(--primary-color);
}

.no-data {
  text-align: center;
  color: var(--header-info-color);
  padding: 40px 0;
}

/* Snapshots */
.snapshots-container {
  display: flex;
  flex-direction: row;
  gap: 20px;
  align-items: stretch;
}

.snapshots-container .section {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.snapshots-container .section-title {
  flex-shrink: 0;
}

.snapshot-editor-wrapper {
  margin-top: 20px;
  height: 500px;
  max-height: 500px;
  overflow: hidden;
  border-radius: 6px;
}

/* Error Banner */
.error-banner {
  background-color: #fef2f2;
  color: #dc2626;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-weight: 500;
  border: 1px solid #fecaca;
}

.error-banner a {
  color: #b91c1c;
  font-weight: 600;
  text-decoration: underline;
}

/* Resuming Overlay */
.resuming-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(36, 40, 48, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
  color: white;
  flex-direction: column;
  backdrop-filter: blur(5px);
}

.resuming-content {
  text-align: center;
}

.resuming-content p {
  font-size: 16px;
  margin-top: 16px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.spinner {
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  border-top: 4px solid #fff;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Table Styles */
:deep(.el-table) {
  font-size: 13px;
  background-color: var(--card-bg) !important;
  color: var(--text-primary);
}

:deep(.el-table th) {
  background: var(--table-header-bg) !important;
  font-weight: 600;
  color: var(--header-info-color) !important;
  font-size: 12px;
}

:deep(.el-table th.el-table__cell) {
  background-color: var(--table-header-bg) !important;
}

:deep(.el-table td) {
  background-color: var(--card-bg) !important;
  color: var(--text-primary) !important;
  border-bottom-color: var(--border-color);
}

:deep(.el-table td.el-table__cell) {
  background-color: var(--card-bg) !important;
}

:deep(.el-table tbody tr) {
  background-color: var(--card-bg) !important;
}

:deep(.el-table tbody tr:hover) {
  background: var(--table-hover-bg) !important;
}

:deep(.el-table tbody tr:hover > td) {
  background-color: var(--table-hover-bg) !important;
}

:deep(.el-table tbody tr:hover > td.el-table__cell) {
  background-color: var(--table-hover-bg) !important;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: var(--table-header-bg) !important;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background-color: var(--table-header-bg) !important;
}

:deep(.el-table__inner-wrapper) {
  background-color: var(--card-bg);
}

:deep(.el-table__body) {
  background-color: var(--card-bg);
}

:deep(.el-table__body-wrapper)::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

:deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: var(--table-header-bg);
}

:deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

:deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: var(--header-info-color);
}

/* 移动端适配 */
@media (max-width: 768px) {
  /* 容器 */
  .container {
    padding: 8px;
  }

  /* 头部 */
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 12px;
    margin-bottom: 12px;
  }

  .header h1 {
    font-size: 18px !important;
  }

  .header-info {
    font-size: 11px;
  }

  .control-buttons {
    width: 100%;
    display: flex;
    gap: 8px;
  }

  .control-buttons button {
    flex: 1;
    font-size: 13px;
    padding: 8px 12px;
  }

  /* 选项卡 */
  .tabs {
    overflow-x: auto;
    overflow-y: hidden;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    margin-bottom: 12px;
    padding-bottom: 2px;
  }

  .tabs::-webkit-scrollbar {
    display: none;
  }

  .tab-link {
    font-size: 13px;
    padding: 0 12px;
    flex-shrink: 0;
  }

  /* 卡片 */
  .section {
    --section-padding-inline: 12px;
    padding: 12px var(--section-padding-inline);
    margin-bottom: 12px;
    border-radius: 6px;
    overflow: visible; /* 允许表格横向滚动 */
  }

  .table-wrapper {
    margin: 16px calc(-1 * var(--section-padding-inline)) 0;
    padding: 0 var(--section-padding-inline) 12px;
  }

  .section-title-container {
    margin-bottom: 12px;
    padding-bottom: 8px;
  }

  .section-title {
    font-size: 14px;
  }

  /* 指标网格 */
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }

  .metric-card {
    padding: 8px 10px;
  }

  .metric-label {
    font-size: 11px;
  }

  .metric-value {
    font-size: 15px;
  }

  /* 图表 */
  .chart-container {
    height: 300px;
  }

  .chart-tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .chart-tab-link {
    font-size: 12px;
    padding: 6px 12px;
    white-space: nowrap;
  }

  /* 表格 */
  :deep(.el-table) {
    font-size: 11px;
  }

  :deep(.el-table th) {
    font-size: 10px;
    padding: 8px 4px;
  }

  :deep(.el-table td) {
    padding: 8px 4px;
  }

  :deep(.el-table .cell) {
    padding: 0 4px;
    line-height: 1.3;
  }

  /* 分页器 */
  :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center !important;
    gap: 4px;
  }

  :deep(.el-pagination .el-pager li) {
    min-width: 28px;
    height: 28px;
    line-height: 28px;
    font-size: 12px;
  }

  :deep(.el-pagination button) {
    min-width: 28px;
    height: 28px;
    font-size: 12px;
  }

  :deep(.el-pagination .el-pagination__sizes) {
    margin: 4px 0;
  }

  :deep(.el-pagination .el-pagination__jump) {
    margin: 4px 0;
    font-size: 12px;
  }

  /* 日志容器优化 */
  .logs-container {
    max-height: 300px;
    font-size: 11px;
    padding: 8px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .log-entry {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 6px;
    align-items: start;
    min-width: max-content;
  }

  .log-time-group {
    font-size: 8px;
    display: flex;
    flex-direction: column;
    gap: 1px;
    line-height: 1.2;
    padding-right: 0.5rem;
    border-right: 1px solid var(--border-color);
    flex-shrink: 0;
  }

  .log-sim-time {
    font-size: 8px;
    white-space: nowrap;
  }

  .log-exec-time {
    display: none; /* 在移动端隐藏执行时间，节省空间 */
  }

  .log-level {
    font-size: 8px;
    white-space: nowrap;
  }

  .log-message {
    font-size: 9px;
    word-break: break-word;
    overflow-wrap: break-word;
  }

  /* 代码快照 - 改为垂直布局 */
  .snapshots-container {
    flex-direction: column;
  }

  .snapshots-container .section {
    width: 100%;
  }

  .snapshot-editor-wrapper {
    height: 300px;
    max-height: 300px;
  }

  :deep(.editor-container) {
    max-height: 300px;
  }

  /* 按钮 */
  .btn {
    font-size: 12px;
    padding: 6px 12px;
  }

  /* 对话框 */
  :deep(.el-dialog) {
    width: 95% !important;
    margin: 10px auto !important;
  }

  :deep(.el-dialog__body) {
    padding: 12px;
  }

}

/* 小屏幕（手机竖屏）进一步优化 */
@media (max-width: 480px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .chart-container {
    height: 250px;
  }

  :deep(.el-pagination) {
    font-size: 11px;
  }

  :deep(.el-pagination .el-pager li) {
    min-width: 24px;
    height: 24px;
    line-height: 24px;
  }

  :deep(.el-pagination button) {
    min-width: 24px;
    height: 24px;
  }

  /* 日志进一步优化 */
  .logs-container {
    max-height: 250px;
    font-size: 10px;
    overflow-x: auto;
  }

  .log-entry {
    gap: 0.4rem;
    margin-bottom: 5px;
    min-width: max-content;
  }

  .log-time-group {
    font-size: 7px;
    padding-right: 0.4rem;
  }

  .log-sim-time {
    font-size: 7px;
  }

  .log-level {
    font-size: 7px;
  }

  .log-message {
    font-size: 8px;
    min-width: 150px;
  }

  /* 代码快照进一步优化 */
  .snapshot-editor-wrapper {
    height: 250px;
    max-height: 250px;
  }
}
</style>
