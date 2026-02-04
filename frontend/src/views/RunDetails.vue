<template>
  <div class="run-details-page" v-loading="loading">
    <!-- Floating Back Button -->
    <el-tooltip
      v-if="strategyName"
      :content="`返回策略: ${strategyName}`"
      placement="right"
    >
      <button @click="backToStrategy" class="floating-back-button">
        ←
      </button>
    </el-tooltip>

    <template v-if="runStatus">
      <!-- Live Monitoring View (for running and paused status) -->
      <MonitoringView
        v-if="runStatus === 'running' || runStatus === 'paused'"
        :run-id="run_id"
        :initial-status="runStatus"
      />
      <!-- Static Report View -->
      <ReportView v-else :run-id="run_id" />
    </template>
    <el-empty v-else-if="!loading" description="无法加载运行实例详情"></el-empty>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import apiClient from '../api/axios';
import { ElMessage } from 'element-plus';
import ReportView from '../components/ReportView.vue';
import MonitoringView from '../components/MonitoringView.vue';
import socket from '../api/socket';

const route = useRoute();
const router = useRouter();
const run_id = ref(route.params.run_id);
const loading = ref(true);
const runStatus = ref(null);

// 心跳定时器
let heartbeatTimer = null;

// 从 run_id 解析出策略名称
// run_id 格式: {strategy_name}_{mode}_{timestamp}_{time}
const strategyName = computed(() => {
  const parts = run_id.value.split('_');
  if (parts.length >= 4) {
    // 去掉最后3部分 (mode, date, time)
    return parts.slice(0, -3).join('_');
  }
  return null;
});

const fetchStatus = async () => {
  loading.value = true;
  try {
    const response = await apiClient.get(`/runs/${run_id.value}/status`);
    runStatus.value = response.data.status;
  } catch (error) {
    ElMessage.error('获取运行状态失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const backToStrategy = () => {
  if (strategyName.value) {
    router.push({ name: 'StrategyEditor', params: { strategy_name: strategyName.value } });
  }
};

onMounted(() => {
  fetchStatus();

  // 启动心跳定时器（每30秒发送一次）
  heartbeatTimer = setInterval(() => {
    socket.emit('run_heartbeat', { run_id: run_id.value });
  }, 30000);
});

onBeforeUnmount(() => {
  // 清除心跳定时器
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }
});
</script>

<style scoped>
.run-details-page {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  position: relative;
}

.page-header {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 20px;
  z-index: 50;
  text-align: center;
}

.strategy-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--header-info-color);
}

.floating-back-button {
  position: fixed;
  top: 65px;
  left: 9px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  z-index: 100;
}

.floating-back-button:hover {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
  transform: translateX(-3px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.floating-back-button:active {
  transform: translateX(-3px) scale(0.95);
}
</style>