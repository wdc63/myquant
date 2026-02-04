<template>
  <div class="strategy-editor-layout" v-loading="loading">
    <!-- Starting Overlay -->
    <div v-if="startingInfo.isStarting" class="starting-overlay">
      <div class="starting-content">
        <div class="spinner"></div>
        <p>{{ startingInfo.message }}</p>
      </div>
    </div>

    <div class="editor-container">
      <div class="editor-pane">
        <el-card class="editor-card">
          <template #header>
            <div class="header-content">
              <span><span style="margin-right: 6px;">💻</span>策略: {{ strategy_name }}</span>
              <el-button type="primary" @click="saveFile(true)" :loading="isSaving">
                保 存
              </el-button>
            </div>
          </template>
          <el-tabs v-model="activeTab" type="border-card" class="file-tabs">
            <el-tab-pane label="strategy.py" name="strategy.py">
              <Editor
                v-if="activeTab === 'strategy.py'"
                v-model="files['strategy.py']"
                language="python"
                :theme="editorTheme"
              />
            </el-tab-pane>
            <el-tab-pane label="config.yaml" name="config.yaml">
              <Editor
                v-if="activeTab === 'config.yaml'"
                v-model="files['config.yaml']"
                language="yaml"
                :theme="editorTheme"
              />
            </el-tab-pane>
            <el-tab-pane label="stock_api_provider.py" name="stock_api_provider.py">
              <Editor
                v-if="activeTab === 'stock_api_provider.py'"
                v-model="files['stock_api_provider.py']"
                language="python"
                :theme="editorTheme"
              />
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </div>
      <div class="run-management-pane">
        <el-card>
          <template #header>
            <span><span style="margin-right: 6px;">⚙️</span>运行管理</span>
          </template>
          <RunManagement :strategy-name="strategy_name" @starting-run="handleStartingRun" />
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRoute } from 'vue-router';
import apiClient from '../api/axios';
import { ElMessage } from 'element-plus';
import Editor from '../components/Editor.vue';
import RunManagement from '../components/RunManagement.vue';

const route = useRoute();
const strategy_name = ref(route.params.strategy_name);
const loading = ref(true);
const isSaving = ref(false);
const activeTab = ref('strategy.py');
const startingInfo = ref({ isStarting: false, message: '' });

const handleStartingRun = ({ starting, mode }) => {
  startingInfo.value.isStarting = starting;
  if (starting) {
    const modeText = mode === 'backtest' ? '回测' : '模拟';
    startingInfo.value.message = `正在启动${modeText}引擎...`;
  }
};

// Theme support
const isDark = ref(document.body.classList.contains('dark-mode'));
const editorTheme = computed(() => isDark.value ? 'vs-dark' : 'vs');

const themeObserver = new MutationObserver(() => {
  isDark.value = document.body.classList.contains('dark-mode');
});

const files = ref({
  'strategy.py': '',
  'config.yaml': '',
  'stock_api_provider.py': '',
});

const fetchFiles = async () => {
  loading.value = true;
  try {
    const response = await apiClient.get(`/strategies/${strategy_name.value}/files`);
    files.value = response.data.files;
  } catch (error) {
    ElMessage.error('获取策略文件失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchFiles();
  themeObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] });
  window.addEventListener('keydown', handleKeyDown);
});

onBeforeUnmount(() => {
  themeObserver.disconnect();
  window.removeEventListener('keydown', handleKeyDown);
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer);
  }
});

let autoSaveTimer = null;

const saveFile = async (manual = false) => {
  if (isSaving.value) return; // Prevent concurrent saves

  const filename = activeTab.value;
  const content = files.value[filename];

  // Do not save if content is undefined or null (e.g., during initial load)
  if (content === undefined || content === null) {
    return;
  }

  isSaving.value = true;
  try {
    await apiClient.put(`/strategies/${strategy_name.value}/files/${filename}`, { content });
    if (manual) {
      ElMessage.success(`文件 ${filename} 已保存`);
    } else {
      // For auto-save, we can use a more subtle notification or just log it.
      // Using ElMessage for now for visibility.
      ElMessage.success({
        message: `文件 ${filename} 已自动保存`,
        type: 'success',
        duration: 1500,
      });
    }
  } catch (error) {
    ElMessage.error('文件保存失败');
    console.error(error);
  } finally {
    isSaving.value = false;
  }
};

const handleKeyDown = (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 's') {
    event.preventDefault();
    saveFile(true); // Trigger manual save
  }
};

// Watch for changes in files and auto-save
watch(files, (newValue, oldValue) => {
  // Simple check to avoid saving on initial load when files are populated.
  const isInitialPopulation = Object.values(oldValue).every(v => v === '');
  if (isInitialPopulation && newValue) {
    return;
  }

  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer);
  }
  autoSaveTimer = setTimeout(() => {
    saveFile(false); // Trigger auto-save
  }, 2500); // Auto-save after 2.5 seconds of inactivity
}, { deep: true });
</script>

<style scoped>
.strategy-editor-layout {
  height: 100%;
  width: 100%;
}

.editor-container {
  display: flex;
  height: 100%;
  width: 100%;
  gap: 20px;
}

.editor-pane {
  flex: 0 0 60%;
  height: 100%;
  min-width: 0;
}

.run-management-pane {
  flex: 1;
  height: 100%;
  min-width: 0;
}

.editor-card, .run-management-pane .el-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.editor-card > .el-card__body) {
  flex-grow: 1;
  padding: 0;
  display: flex;
  flex-direction: column;
}

:deep(.run-management-pane .el-card > .el-card__body) {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.file-tabs {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

:deep(.file-tabs > .el-tabs__content) {
  flex-grow: 1;
  padding: 0;
}

:deep(.el-tab-pane) {
  height: 100%;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Dark Mode Support for Tabs */
:deep(.el-tabs--border-card) {
  background-color: var(--card-bg);
  border-color: var(--border-color);
}

:deep(.el-tabs--border-card > .el-tabs__header) {
  background-color: var(--table-header-bg);
  border-bottom-color: var(--border-color);
}

:deep(.el-tabs__item) {
  color: var(--header-info-color);
  border-color: var(--border-color);
}

:deep(.el-tabs__item.is-active) {
  color: var(--primary-color);
  background-color: var(--card-bg);
}

:deep(.el-tabs__item:hover) {
  color: var(--primary-color);
}

:deep(.el-tabs--border-card > .el-tabs__content) {
  background-color: var(--card-bg);
}

/* Starting Overlay */
.starting-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(36, 40, 48, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 3000; /* Higher than other elements */
  color: white;
  flex-direction: column;
  backdrop-filter: blur(5px);
}

.starting-content {
  text-align: center;
}

.starting-content p {
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

/* 移动端适配 */
@media (max-width: 768px) {
  .editor-container {
    flex-direction: column;
    gap: 16px;
  }

  .editor-pane {
    flex: 0 0 auto;
    height: 50vh;
    width: 100%;
    min-height: 400px;
  }

  .run-management-pane {
    flex: 0 0 auto;
    height: auto;
    min-height: 500px;
    width: 100%;
  }

  /* 确保卡片内容可以正常滚动 */
  .editor-card, .run-management-pane .el-card {
    height: 100%;
    overflow: hidden;
  }

  /* 调整按钮和头部 */
  .header-content {
    font-size: 14px;
  }

  .header-content span {
    font-size: 14px;
  }

  :deep(.el-button) {
    font-size: 13px;
    padding: 8px 12px;
  }

  /* 标签栏优化 */
  :deep(.el-tabs__item) {
    font-size: 12px;
    padding: 0 12px;
  }

  /* 确保run management中的表格可以横向滚动 */
  :deep(.run-management) {
    overflow: visible;
  }

  :deep(.run-tabs) {
    overflow: visible;
  }

  :deep(.el-tabs__content) {
    overflow: visible;
  }
}

/* 小屏幕进一步优化 */
@media (max-width: 480px) {
  .editor-pane {
    min-height: 350px;
    height: 45vh;
  }

  .run-management-pane {
    min-height: 450px;
  }

  .header-content {
    font-size: 13px;
  }

  .header-content span {
    font-size: 13px;
  }

  :deep(.el-button) {
    font-size: 12px;
    padding: 6px 10px;
  }

  :deep(.el-tabs__item) {
    font-size: 11px;
    padding: 0 10px;
  }
}
</style>