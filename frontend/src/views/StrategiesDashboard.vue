<template>
  <div class="container">
    <div class="header">
      <div>
        <h1 style="font-size: 22px; font-weight: 600; color: var(--primary-color);">
          <span style="margin-right: 8px;">📊</span>策略工作台
        </h1>
        <div class="header-info">管理您的量化交易策略</div>
      </div>
      <el-button type="primary" size="large" @click="openCreateDialog" class="btn-create">
        <span style="margin-right: 4px;">+</span>创建新策略
      </el-button>
    </div>

    <div v-loading="loading" style="min-height: 400px;">
      <el-row :gutter="20" v-if="!loading && strategies.length > 0">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" :xl="6" v-for="strategy in strategies" :key="strategy.name">
          <div class="strategy-card" @click="goToStrategy(strategy.name)">
            <div class="card-header">
              <div class="strategy-name">
                <span style="margin-right: 6px; opacity: 0.7;">📝</span>{{ strategy.name }}
              </div>
              <el-button
                 type="danger"
                 circle
                 class="delete-btn"
                 @click.stop="deleteStrategy(strategy.name)"
               >
                 <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
               </el-button>
            </div>
            <div class="card-body">
              <div class="card-info-item">
                <span class="info-label">创建时间</span>
                <span class="info-value">{{ formatDate(strategy.created_at) }}</span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-empty v-if="!loading && strategies.length === 0" description="暂无策略，点击右上角创建您的第一个策略" />
    </div>

    <!-- 创建策略弹窗 -->
    <el-dialog v-model="createDialogVisible" title="创建新策略" width="30%">
      <el-form :model="createForm" ref="createFormRef">
        <el-form-item label="策略名称" prop="name" :rules="[
          { required: true, message: '请输入策略名称' }
        ]">
          <el-input
            v-model="createForm.name"
            placeholder="例如：测试策略 或 my_first_strategy"
            @keyup.enter="handleCreateStrategy"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleCreateStrategy" :loading="createLoading">
            创建
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import apiClient from '../api/axios';
import { ElMessage, ElMessageBox } from 'element-plus';

const router = useRouter();
const loading = ref(true);
const strategies = ref([]);

// 获取策略列表
const fetchStrategies = async () => {
  loading.value = true;
  try {
    const response = await apiClient.get('/strategies');
    strategies.value = response.data.strategies;
  } catch (error) {
    ElMessage.error('获取策略列表失败');
  } finally {
    loading.value = false;
  }
};

onMounted(fetchStrategies);

// 格式化日期
const formatDate = (timestamp) => {
  const date = new Date(timestamp * 1000);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 跳转到策略详情页
const goToStrategy = (strategyName) => {
  router.push({ name: 'StrategyEditor', params: { strategy_name: strategyName } });
};

// 创建策略弹窗逻辑
const createDialogVisible = ref(false);
const createLoading = ref(false);
const createForm = ref({ name: '' });
const createFormRef = ref(null);

const openCreateDialog = () => {
  createForm.value.name = '';
  createDialogVisible.value = true;
};

const handleCreateStrategy = async () => {
  if (!createFormRef.value) return;
  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      createLoading.value = true;
      try {
        await apiClient.post('/strategies', { name: createForm.value.name });
        ElMessage.success('策略创建成功');
        createDialogVisible.value = false;
        await fetchStrategies(); // 重新加载列表
      } catch (error) {
        const message = error.response?.data?.message || '创建失败';
        ElMessage.error(message);
      } finally {
        createLoading.value = false;
      }
    }
  });
};

// 删除策略
const deleteStrategy = async (strategyName) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除策略 "${strategyName}" 吗？此操作将永久删除策略及其所有运行数据，无法恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    );

    await apiClient.delete(`/strategies/${strategyName}`);
    ElMessage.success(`策略 "${strategyName}" 已删除`);
    await fetchStrategies(); // 重新加载列表
  } catch (error) {
    if (error !== 'cancel') {
      const message = error.response?.data?.message || '删除失败';
      ElMessage.error(message);
    }
  }
};
</script>

<style scoped>
/* Header */
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

.btn-create {
  font-size: 14px;
  padding: 10px 20px;
}

/* Strategy Cards */
.strategy-card {
  background: var(--card-bg);
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.strategy-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
  border-color: var(--primary-color);
}

.card-header {
  background: var(--table-header-bg);
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.delete-btn {
   width: 28px;
   height: 28px;
   min-height: 28px;
}

.strategy-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-body {
  padding: 16px;
}

.card-info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.info-label {
  color: var(--header-info-color);
}

.info-value {
  color: var(--text-primary);
  font-weight: 500;
}

/* Dialog */
:deep(.el-dialog) {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
}

:deep(.el-dialog__header) {
  border-bottom: 1px solid var(--border-color);
  padding: 16px 20px;
}

:deep(.el-dialog__title) {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-form-item__label) {
  color: var(--text-primary);
}

/* Empty State */
:deep(.el-empty__description) {
  color: var(--header-info-color);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
  }

  .header h1 {
    font-size: 18px !important;
  }

  .header-info {
    font-size: 12px;
  }

  .btn-create {
    width: 100%;
    font-size: 14px;
    padding: 10px 16px;
  }

  .strategy-card {
    margin-bottom: 12px;
  }

  .card-header {
    padding: 12px;
  }

  .strategy-name {
    font-size: 14px;
  }

  .card-body {
    padding: 12px;
  }

  .card-info-item {
    font-size: 12px;
  }

  :deep(.el-dialog) {
    width: 90% !important;
    margin: 20px auto !important;
  }
}
</style>
