<template>
  <div class="run-list" ref="containerRef">
    <el-empty v-if="!runs || runs.length === 0" description="暂无记录"></el-empty>
    <el-table v-else :data="runs" stripe class="runs-table" :height="tableHeight">
      <el-table-column :label="mode === 'backtest' ? '回测时间' : '启动时间'" width="auto">
        <template #default="scope">
          <div class="time-display">
            <!-- 回测模式：优先显示起止日期 -->
            <div v-if="mode === 'backtest' && scope.row.start_date && scope.row.end_date" class="date-range">
              <div>{{ scope.row.start_date }}</div>
              <div>{{ scope.row.end_date }}</div>
            </div>
            <!-- 模拟模式或无日期数据：显示启动时间 -->
            <div v-else class="date-range">
              <div>{{ formatDate(scope.row.start_time) }}</div>
              <div class="time-second">{{ formatTime(scope.row.start_time) }}</div>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" align="center" width="auto">
        <template #default="scope">
          <div class="status-cell">
            <el-tag v-if="scope.row.status === 'running' && !scope.row.is_paused" type="primary" size="small">
              运行中
            </el-tag>
            <el-tag v-else-if="scope.row.status === 'paused' || (scope.row.status === 'running' && scope.row.is_paused)" type="warning" size="small">
              已暂停
            </el-tag>
            <el-tag v-else :type="getStatusType(scope.row.status)" size="small">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
            <div
              v-if="scope.row.status === 'finished' && scope.row.final_return !== undefined"
              class="final-return"
              :class="{ 'positive': scope.row.final_return > 0, 'negative': scope.row.final_return < 0 }"
            >
              {{ formatReturn(scope.row.final_return) }}
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="备注" align="center" width="auto">
        <template #default="scope">
          <div
            class="note-cell"
            @dblclick="startEditNote(scope.row)"
            :title="scope.row.note || '双击添加备注'"
          >
            <el-input
              v-if="editingNoteId === scope.row.run_id"
              v-model="editingNoteText"
              size="small"
              placeholder="输入备注"
              @blur="saveNote(scope.row)"
              @keyup.enter="saveNote(scope.row)"
              ref="noteInput"
              maxlength="100"
            />
            <span v-else class="note-text">
              {{ scope.row.note || '双击添加' }}
            </span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="auto">
        <template #default="scope">
          <div class="action-buttons">
            <el-button size="small" @click="viewDetails(scope.row.run_id)" :disabled="scope.row.status === 'corrupted'">
              <span class="btn-content">
                <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
                <span>查看</span>
              </span>
            </el-button>
            <el-button size="small" @click="downloadWorkspace(scope.row.run_id)" :disabled="scope.row.is_running">
              <span class="btn-content">
                <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                <span>下载</span>
              </span>
            </el-button>
            <el-button size="small" type="danger" @click="deleteWorkspace(scope.row)" :disabled="scope.row.is_running">
              <span class="btn-content">
                <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
                <span>删除</span>
              </span>
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import apiClient from '../api/axios';
import socket from '../api/socket';

const props = defineProps({
  runs: Array,
  mode: {
    type: String,
    default: 'backtest',
    validator: (value) => ['backtest', 'simulation'].includes(value)
  }
});

const emit = defineEmits(['refresh']);

// 调试：查看runs数据
if (props.runs && props.runs.length > 0) {
  console.log('RunList data:', props.runs);
}

const router = useRouter();
const containerRef = ref(null);
const tableHeight = ref(500);
const editingNoteId = ref(null);
const editingNoteText = ref('');
const noteInput = ref(null);

// 监听 Socket.IO 状态变化
const handleStatusChanged = (data) => {
  console.log('收到状态变化:', data);
  const run = props.runs?.find(r => r.run_id === data.run_id);
  if (run) {
    if (data.is_paused !== undefined) {
      run.is_paused = data.is_paused;
      run.status = data.is_paused ? 'paused' : 'running';
    }
    if (data.status) {
      run.status = data.status;
      run.is_paused = data.status === 'paused';
    }
  }
};

const updateTableHeight = () => {
  if (containerRef.value) {
    const containerHeight = containerRef.value.clientHeight;
    // 给表格设置为容器的高度,这样会自动出现滚动条
    tableHeight.value = containerHeight > 0 ? containerHeight : 500;
  }
};

onMounted(() => {
  updateTableHeight();
  window.addEventListener('resize', updateTableHeight);

  // 监听状态变化
  socket.on('run_status_changed', handleStatusChanged);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateTableHeight);

  // 移除监听
  socket.off('run_status_changed', handleStatusChanged);
});

const formatDate = (timestamp) => {
  if (!timestamp) return 'N/A';
  const date = new Date(timestamp * 1000);
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
};

const formatTime = (timestamp) => {
  if (!timestamp) return '';
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

const statusMap = {
  running: { text: '运行中', type: 'primary' },
  paused: { text: '已暂停', type: 'warning' },
  finished: { text: '已完成', type: 'success' },
  interrupted: { text: '已中断', type: 'info' },
  corrupted: { text: '数据损坏', type: 'danger' },
};

const getStatusType = (status) => statusMap[status]?.type || 'info';
const getStatusText = (status) => statusMap[status]?.text || status;

const formatReturn = (returnValue) => {
  const percentage = (returnValue * 100).toFixed(2);
  return returnValue >= 0 ? `+${percentage}%` : `${percentage}%`;
};

const viewDetails = (runId) => {
  router.push({ name: 'RunDetails', params: { run_id: runId } });
};

const downloadWorkspace = async (runId) => {
  try {
    const response = await apiClient.get(`/runs/${runId}/download-workspace`, {
      responseType: 'blob'
    });

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${runId}_workspace.zip`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    ElMessage.success('工作区下载成功');
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '下载失败');
  }
};

const deleteWorkspace = async (run) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除该运行实例吗？此操作将永久删除所有数据，无法恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    );

    await apiClient.delete(`/runs/${run.run_id}/delete`);
    ElMessage.success('删除成功');

    // 通知父组件刷新列表
    emit('refresh');
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.error || '删除失败');
    }
  }
};

const startEditNote = (run) => {
  editingNoteId.value = run.run_id;
  editingNoteText.value = run.note || '';
  // 等待DOM更新后聚焦输入框
  setTimeout(() => {
    const inputEl = document.querySelector(`input[placeholder="输入备注"]`);
    if (inputEl) {
      inputEl.focus();
      inputEl.select();
    }
  }, 50);
};

const saveNote = async (run) => {
  if (editingNoteId.value !== run.run_id) return;

  const newNote = editingNoteText.value.trim();

  try {
    await apiClient.put(`/runs/${run.run_id}/note`, { note: newNote });
    run.note = newNote;
    ElMessage.success('备注已保存');
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '保存备注失败');
  } finally {
    editingNoteId.value = null;
    editingNoteText.value = '';
  }
};
</script>

<style scoped>
.run-list {
  width: 100%;
  height: 100%;
}

/* Table Dark Mode Styles */
:deep(.el-table) {
  background-color: var(--card-bg) !important;
  color: var(--text-primary);
}

:deep(.el-table th) {
  background: var(--table-header-bg) !important;
  color: var(--header-info-color) !important;
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

.time-display {
  display: flex;
  flex-direction: column;
  line-height: 1.5;
  font-size: 13px;
}

.date-range {
  font-size: 13px;
  color: var(--text-primary);
}

.time-second {
  color: var(--header-info-color);
  font-size: 12px;
  margin-left: 4px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
}

.action-buttons .el-button {
  margin-left: 0 !important;
  width: 90px !important;
  padding: 6px 8px !important;
  box-sizing: border-box !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
}

.btn-content {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.btn-content svg {
  flex-shrink: 0;
  display: block;
}

.status-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.final-return {
  font-size: 12px;
  font-weight: 600;
  margin-top: 2px;
}

.final-return.positive {
  color: #f56c6c;
}

.final-return.negative {
  color: #67c23a;
}

.note-cell {
  cursor: pointer;
  min-height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
}

.note-text {
  color: var(--text-primary);
  font-size: 13px;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.note-cell:hover .note-text {
  color: var(--el-color-primary);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
  }

  .tabs {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    margin-top: 8px;
  }

  .tabs::-webkit-scrollbar {
    display: none;
  }

  .tab-link {
    font-size: 13px;
    padding: 8px 16px;
    white-space: nowrap;
  }

  /* 表格样式调整 */
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

  /* 按钮组 */
  .btn-content {
    gap: 4px;
  }

  .btn-content span {
    display: none;
  }

  .btn-content svg {
    margin-right: 0;
  }

  :deep(.el-button) {
    padding: 6px 8px;
    min-width: 32px;
  }

  /* 状态标签 */
  .status-badge {
    font-size: 10px;
    padding: 2px 6px;
  }

  /* 日期范围 */
  .date-range {
    font-size: 10px;
  }

  /* 收益率 */
  .final-return {
    font-size: 10px;
  }

  /* 表格容器允许横向滚动 */
  .run-list {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  /* 表格横向滚动 */
  :deep(.el-table__body-wrapper) {
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch;
  }

  :deep(.el-table) {
    width: 100%;
  }

  /* 时间列固定宽度 */
  :deep(.el-table__header-wrapper .el-table__cell:first-child),
  :deep(.el-table__body-wrapper .el-table__cell:first-child) {
    width: 35% !important;
    min-width: 100px;
  }

  /* 状态列固定宽度 */
  :deep(.el-table__header-wrapper .el-table__cell:nth-child(2)),
  :deep(.el-table__body-wrapper .el-table__cell:nth-child(2)) {
    width: 25% !important;
    min-width: 85px;
  }

  /* 操作列固定宽度 */
  :deep(.el-table__header-wrapper .el-table__cell:nth-child(3)),
  :deep(.el-table__body-wrapper .el-table__cell:nth-child(3)) {
    width: 40% !important;
    min-width: 130px;
  }
}

/* 小屏幕进一步优化 */
@media (max-width: 480px) {
  :deep(.el-table) {
    font-size: 10px;
  }

  :deep(.el-button) {
    padding: 4px 6px;
    min-width: 28px;
  }

  :deep(.el-button svg) {
    width: 12px;
    height: 12px;
  }
}
</style>