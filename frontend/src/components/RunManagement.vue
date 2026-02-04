<template>
  <div class="run-management" v-loading="loading">
    <div class="actions">
      <el-button type="primary" size="large" @click="startRun('backtest')" :loading="startingRun === 'backtest'">
        启动回测
      </el-button>
      <el-button type="success" size="large" @click="startRun('simulation')" :loading="startingRun === 'simulation'">
        启动模拟
      </el-button>
    </div>

    <el-tabs v-model="activeTab" class="run-tabs">
      <el-tab-pane label="历史回测" name="backtest">
        <RunList :runs="runs.backtest" mode="backtest" @refresh="fetchRuns" />
      </el-tab-pane>
      <el-tab-pane label="历史模拟" name="simulation">
        <RunList :runs="runs.simulation" mode="simulation" @refresh="fetchRuns" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import apiClient from '../api/axios';
import { ElMessage } from 'element-plus';
import socket, { connectSharedSocket, disconnectSharedSocket } from '../api/socket';
import RunList from './RunList.vue';

const props = defineProps({
  strategyName: String,
});

const router = useRouter();
const emit = defineEmits(['refresh', 'starting-run']);
const loading = ref(true);
const startingRun = ref(null); // 'backtest' or 'simulation'
const activeTab = ref('backtest');
const runs = ref({ backtest: [], simulation: [] });

// Fetch runs
const fetchRuns = async () => {
  loading.value = true;
  try {
    const response = await apiClient.get(`/strategies/${props.strategyName}/runs`);
    runs.value = response.data.runs;
  } catch (error) {
    ElMessage.error('获取运行列表失败');
  } finally {
    loading.value = false;
  }
};

// Socket event handler
const dashboardUpdateHandler = (data) => {
  // Only refresh if the update is for the current strategy
  if (data && data.strategy_name === props.strategyName) {
    console.log(`Dashboard update event received for ${props.strategyName}`);
    // Add a delay to allow backend to finalize files
    setTimeout(() => {
      fetchRuns();
    }, 1500);
  }
};

onMounted(() => {
  fetchRuns();
  connectSharedSocket();
  socket.on('dashboard_update', dashboardUpdateHandler);
});

onBeforeUnmount(() => {
  socket.off('dashboard_update', dashboardUpdateHandler);
  disconnectSharedSocket();
});

// Start a new run
const startRun = async (mode) => {
  startingRun.value = mode;
  emit('starting-run', { starting: true, mode });
  try {
    const response = await apiClient.post(`/strategies/${props.strategyName}/runs`, { mode });
    const runId = response.data.run_id;
    // Jump to the details page of the new run
    router.push({ name: 'RunDetails', params: { run_id: runId } });
  } catch (error) {
    const message = error.response?.data?.error || '启动失败';
    ElMessage.error(message);
  } finally {
    startingRun.value = null;
    emit('starting-run', { starting: false, mode });
  }
};
</script>

<style scoped>
.run-management {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.actions {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.actions .el-button {
  flex-grow: 1;
}
.run-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
:deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}
:deep(.el-tab-pane) {
  height: 100%;
}
</style>