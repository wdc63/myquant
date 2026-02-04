<template>
  <div class="libraries-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">平台库管理</h1>
      <p class="page-subtitle">管理平台内置库和自定义第三方库</p>
      <div v-if="pythonVersion" class="python-version-info">
        <span class="python-icon">🐍</span>
        <span class="python-version-text">当前 Python 版本: <code>{{ pythonVersion }}</code></span>
      </div>
    </div>

    <!-- 内置库展示 -->
    <section class="section">
      <div class="section-header">
        <h2 class="section-title">
          <span class="section-icon">📦</span>
          内置库
        </h2>
        <span class="section-badge">平台核心依赖</span>
      </div>

      <div class="libraries-grid">
        <div v-for="lib in builtinLibraries" :key="lib.id" class="library-card builtin">
          <div class="library-header">
            <div class="library-info">
              <h3 class="library-name">{{ lib.name }}</h3>
              <span class="library-version">{{ lib.version }}</span>
            </div>
            <span class="library-category-badge">{{ lib.category }}</span>
          </div>
          <p class="library-description">{{ lib.description }}</p>

          <div v-if="lib.dependencies && lib.dependencies.length > 0" class="dependencies-section">
            <div class="dependencies-header" @click="toggleDeps(lib.id)">
              <span class="dependencies-title">依赖包 ({{ lib.dependencies.length }})</span>
              <span class="toggle-icon" :class="{ expanded: expandedDeps[lib.id] }">▼</span>
            </div>
            <transition name="slide-fade">
              <div v-if="expandedDeps[lib.id]" class="dependencies-list">
                <div v-for="dep in lib.dependencies" :key="dep" class="dependency-item">
                  <span class="dependency-dot">•</span>
                  <code class="dependency-name">{{ dep }}</code>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </div>
    </section>

    <!-- 自定义库管理 -->
    <section class="section">
      <div class="section-header">
        <h2 class="section-title">
          <span class="section-icon">🔧</span>
          自定义库
        </h2>
        <button class="btn-primary" @click="showInstallDialog = true">
          <span class="btn-icon">+</span>
          安装新库
        </button>
      </div>

      <div v-if="customLibraries.length === 0" class="empty-state">
        <div class="empty-icon">📚</div>
        <p class="empty-text">暂无自定义库</p>
        <p class="empty-hint">点击"安装新库"添加额外的Python库</p>
      </div>

      <div v-else class="libraries-grid">
        <div v-for="lib in customLibraries" :key="lib.name" class="library-card custom">
          <div class="library-header">
            <div class="library-info">
              <h3 class="library-name">{{ lib.name }}</h3>
              <span class="library-version">v{{ lib.version }}</span>
            </div>
            <span class="library-type-badge custom">自定义</span>
          </div>
          <p v-if="lib.description" class="library-description">{{ lib.description }}</p>
          <div class="library-actions">
            <button
              class="btn-danger-small"
              @click="confirmUninstall(lib.name)"
              :disabled="uninstalling === lib.name"
            >
              {{ uninstalling === lib.name ? '卸载中...' : '卸载' }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 安装库对话框 -->
    <el-dialog
      v-model="showInstallDialog"
      title="安装自定义库"
      width="650px"
      :close-on-click-modal="false"
    >
      <el-form :model="installForm" label-width="80px">
        <el-form-item label="库名称">
          <el-input
            v-model="installForm.libraryName"
            placeholder="例如: xgboost, lightgbm, pandas-ta"
            :disabled="installing"
          />
          <div class="form-hint">输入Python包名（如PyPI上的名称）</div>
        </el-form-item>
        <el-form-item label="库描述">
          <el-input
            v-model="installForm.description"
            type="textarea"
            :rows="2"
            placeholder="可选，简要描述该库的用途"
            :disabled="installing"
          />
          <div class="form-hint">例如：梯度提升决策树，用于因子挖掘</div>
        </el-form-item>
        <el-form-item label="管理密码">
          <el-input
            v-model="installForm.password"
            type="password"
            placeholder="请输入管理密码"
            :disabled="installing"
            @keyup.enter="handleInstall"
          />
        </el-form-item>
      </el-form>

      <!-- pip输出显示区域 -->
      <div v-if="pipOutput" class="pip-output-container">
        <div class="pip-output-header">
          <span class="pip-output-title">📝 pip 安装输出</span>
          <span v-if="installing" class="pip-running-indicator">运行中...</span>
        </div>
        <pre ref="pipOutputRef" class="pip-output">{{ pipOutput }}</pre>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeInstallDialog">{{ pipOutput ? '关闭' : '取消' }}</el-button>
          <el-button
            v-if="!pipOutput"
            type="primary"
            @click="handleInstall"
            :loading="installing"
          >
            {{ installing ? '安装中...' : '安装' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 卸载确认对话框 -->
    <el-dialog
      v-model="showUninstallDialog"
      title="确认卸载"
      width="550px"
      :close-on-click-modal="false"
    >
      <p class="confirm-message">确定要卸载 <strong>{{ libraryToUninstall }}</strong> 吗？</p>
      <el-form :model="uninstallForm" label-width="80px" style="margin-top: 20px;">
        <el-form-item label="管理密码">
          <el-input
            v-model="uninstallForm.password"
            type="password"
            placeholder="请输入管理密码"
            :disabled="uninstalling !== null"
            @keyup.enter="handleUninstall"
          />
        </el-form-item>
      </el-form>

      <!-- pip卸载输出显示区域 -->
      <div v-if="uninstallPipOutput" class="pip-output-container">
        <div class="pip-output-header">
          <span class="pip-output-title">📝 pip 卸载输出</span>
          <span v-if="uninstalling" class="pip-running-indicator">运行中...</span>
        </div>
        <pre ref="uninstallPipOutputRef" class="pip-output">{{ uninstallPipOutput }}</pre>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeUninstallDialog">{{ uninstallPipOutput ? '关闭' : '取消' }}</el-button>
          <el-button
            v-if="!uninstallPipOutput"
            type="danger"
            @click="handleUninstall"
            :loading="uninstalling !== null"
          >
            {{ uninstalling ? '卸载中...' : '确认卸载' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, reactive, nextTick } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import apiClient from '../api/axios';
import socket from '../api/socket';

const builtinLibraries = ref([]);
const customLibraries = ref([]);
const expandedDeps = ref({});
const pythonVersion = ref('');

const showInstallDialog = ref(false);
const showUninstallDialog = ref(false);
const installing = ref(false);
const uninstalling = ref(null);
const libraryToUninstall = ref('');
const pipOutput = ref('');  // pip安装输出
const uninstallPipOutput = ref('');  // pip卸载输出
const currentTaskId = ref('');  // 当前任务ID
const pipOutputRef = ref(null);  // pip输出容器ref
const uninstallPipOutputRef = ref(null);  // 卸载输出容器ref

const installForm = reactive({
  libraryName: '',
  description: '',
  password: ''
});

const uninstallForm = reactive({
  password: ''
});

// 切换依赖展开/收起
const toggleDeps = (libId) => {
  expandedDeps.value[libId] = !expandedDeps.value[libId];
};

// 加载库列表
const loadLibraries = async () => {
  try {
    const response = await apiClient.get('/libraries');
    if (response.data.success) {
      builtinLibraries.value = response.data.builtin;
      customLibraries.value = response.data.custom;

      // 初始化展开状态
      builtinLibraries.value.forEach(lib => {
        expandedDeps.value[lib.id] = false;
      });
    }
  } catch (error) {
    ElMessage.error('加载库列表失败');
    console.error('加载库列表失败:', error);
  }
};

// 加载Python版本
const loadPythonVersion = async () => {
  try {
    const response = await apiClient.get('/libraries/python_version');
    if (response.data.success) {
      pythonVersion.value = response.data.python_version;
    }
  } catch (error) {
    console.error('加载Python版本失败:', error);
    pythonVersion.value = '获取失败';
  }
};

// 安装库
const handleInstall = async () => {
  if (!installForm.libraryName.trim()) {
    ElMessage.warning('请输入库名称');
    return;
  }
  if (!installForm.password) {
    ElMessage.warning('请输入管理密码');
    return;
  }

  installing.value = true;

  // 生成唯一任务ID
  const taskId = `install_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  currentTaskId.value = taskId;

  try {
    // 先不显示pip输出，等请求成功后再显示
    const response = await apiClient.post('/libraries/install', {
      library_name: installForm.libraryName.trim(),
      description: installForm.description.trim(),
      password: installForm.password,
      task_id: taskId
    });

    if (response.data.success) {
      ElMessage.success(response.data.message);

      // 重新加载库列表（但不关闭对话框，让用户手动关闭）
      await loadLibraries();
    } else {
      ElMessage.error(response.data.message || '安装失败');
    }
  } catch (error) {
    const msg = error.response?.data?.message || '安装失败';
    ElMessage.error(msg);
  } finally {
    installing.value = false;
    currentTaskId.value = '';
  }
};

// 关闭安装对话框
const closeInstallDialog = () => {
  showInstallDialog.value = false;
  installForm.libraryName = '';
  installForm.description = '';
  installForm.password = '';
  pipOutput.value = '';
};

// 确认卸载
const confirmUninstall = (libraryName) => {
  libraryToUninstall.value = libraryName;
  uninstallForm.password = '';
  uninstallPipOutput.value = '';
  showUninstallDialog.value = true;
};

// 卸载库
const handleUninstall = async () => {
  if (!uninstallForm.password) {
    ElMessage.warning('请输入管理密码');
    return;
  }

  uninstalling.value = libraryToUninstall.value;

  // 生成唯一任务ID
  const taskId = `uninstall_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  currentTaskId.value = taskId;

  try {
    // 先不显示pip输出，等请求成功后再显示
    const response = await apiClient.post('/libraries/uninstall', {
      library_name: libraryToUninstall.value,
      password: uninstallForm.password,
      task_id: taskId
    });

    if (response.data.success) {
      // 如果有警告，显示警告信息
      if (response.data.warning) {
        ElMessage.warning(response.data.message);
      } else {
        ElMessage.success(response.data.message);
      }

      // 重新加载库列表（但不关闭对话框，让用户手动关闭）
      await loadLibraries();
    } else {
      ElMessage.error(response.data.message || '卸载失败');
    }
  } catch (error) {
    const msg = error.response?.data?.message || '卸载失败';
    ElMessage.error(msg);
  } finally {
    uninstalling.value = null;
    currentTaskId.value = '';
  }
};

// 关闭卸载对话框
const closeUninstallDialog = () => {
  showUninstallDialog.value = false;
  uninstallForm.password = '';
  uninstallPipOutput.value = '';
};

// SocketIO监听pip输出
const handlePipOutput = (data) => {
  if (data.task_id === currentTaskId.value) {
    // 根据任务ID判断是安装还是卸载
    if (data.task_id.startsWith('install_')) {
      // 第一次收到输出时，初始化pip输出区域
      if (!pipOutput.value) {
        pipOutput.value = '正在执行 pip install 命令...\n\n';
      }
      pipOutput.value += data.line;
      // 自动滚动到底部
      nextTick(() => {
        if (pipOutputRef.value) {
          pipOutputRef.value.scrollTop = pipOutputRef.value.scrollHeight;
        }
      });
    } else if (data.task_id.startsWith('uninstall_')) {
      // 第一次收到输出时，初始化pip输出区域
      if (!uninstallPipOutput.value) {
        uninstallPipOutput.value = '正在执行 pip uninstall 命令...\n\n';
      }
      uninstallPipOutput.value += data.line;
      // 自动滚动到底部
      nextTick(() => {
        if (uninstallPipOutputRef.value) {
          uninstallPipOutputRef.value.scrollTop = uninstallPipOutputRef.value.scrollHeight;
        }
      });
    }
  }
};

onMounted(() => {
  loadLibraries();
  loadPythonVersion();

  // 连接SocketIO并监听pip输出事件
  if (!socket.connected) {
    socket.connect();
  }
  socket.on('pip_output', handlePipOutput);
});

onBeforeUnmount(() => {
  // 清理监听
  socket.off('pip_output', handlePipOutput);
});
</script>

<style scoped>
.libraries-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

/* 页面头部 */
.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

.python-version-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--code-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.python-icon {
  font-size: 16px;
}

.python-version-text code {
  font-family: 'Consolas', monospace;
  color: var(--text-primary);
  background: var(--bg-primary);
  padding: 2px 6px;
  border-radius: 4px;
}

/* 分区 */
.section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-icon {
  font-size: 24px;
}

.section-badge {
  padding: 4px 12px;
  background: var(--primary-color);
  color: white;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

/* 库卡片网格 */
.libraries-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

/* 库卡片 */
.library-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.library-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.library-card.builtin {
  border-left: 4px solid var(--primary-color);
}

.library-card.custom {
  border-left: 4px solid #10b981;
}

.library-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
}

.library-info {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.library-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.library-version {
  font-size: 13px;
  color: var(--text-secondary);
  font-family: 'Consolas', monospace;
}

.library-type-badge {
  padding: 3px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}

.library-type-badge.builtin {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
}

.library-type-badge.custom {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.library-category-badge {
  padding: 3px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.library-description {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 16px;
}

/* 依赖区域 */
.dependencies-section {
  border-top: 1px solid var(--border-color);
  padding-top: 12px;
}

.dependencies-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  padding: 4px 0;
}

.dependencies-header:hover {
  opacity: 0.7;
}

.dependencies-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.toggle-icon {
  font-size: 10px;
  color: var(--text-secondary);
  transition: transform 0.2s;
}

.toggle-icon.expanded {
  transform: rotate(180deg);
}

.dependencies-list {
  margin-top: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.dependency-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.dependency-dot {
  color: var(--primary-color);
  font-size: 12px;
}

.dependency-name {
  font-size: 12px;
  font-family: 'Consolas', monospace;
  color: var(--text-primary);
  background: var(--code-bg);
  padding: 2px 6px;
  border-radius: 4px;
}

/* 动画 */
.slide-fade-enter-active {
  transition: all 0.2s ease;
}

.slide-fade-leave-active {
  transition: all 0.15s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

/* 库操作 */
.library-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: var(--card-bg);
  border: 2px dashed var(--border-color);
  border-radius: 12px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 按钮 */
.btn-primary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-icon {
  font-size: 16px;
}

.btn-danger-small {
  padding: 6px 14px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-danger-small:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-danger-small:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 表单提示 */
.form-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.confirm-message {
  font-size: 14px;
  color: var(--text-primary);
}

.confirm-message strong {
  color: var(--primary-color);
}

/* 滚动条样式 */
.dependencies-list::-webkit-scrollbar {
  width: 6px;
}

.dependencies-list::-webkit-scrollbar-track {
  background: var(--bg-primary);
  border-radius: 3px;
}

.dependencies-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.dependencies-list::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}

/* pip输出显示区域 */
.pip-output-container {
  margin-top: 20px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-primary);
}

.pip-output-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--table-header-bg);
  border-bottom: 1px solid var(--border-color);
}

.pip-output-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.pip-running-indicator {
  font-size: 12px;
  color: var(--primary-color);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.pip-output {
  margin: 0;
  padding: 16px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-primary);
  background: var(--code-bg);
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.pip-output::-webkit-scrollbar {
  width: 8px;
}

.pip-output::-webkit-scrollbar-track {
  background: var(--bg-primary);
  border-radius: 4px;
}

.pip-output::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

.pip-output::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .libraries-container {
    padding: 12px;
  }

  .page-header {
    padding: 16px;
  }

  .page-title {
    font-size: 20px;
  }

  .page-subtitle {
    font-size: 13px;
  }

  .python-version-info {
    font-size: 12px;
  }

  .section {
    padding: 16px;
  }

  .section-title {
    font-size: 16px;
  }

  /* 库卡片改为单列布局 */
  .libraries-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .library-card {
    padding: 16px;
  }

  .library-name {
    font-size: 15px;
  }

  .library-version {
    font-size: 11px;
  }

  .library-description {
    font-size: 13px;
  }

  .dependency-name {
    font-size: 11px;
  }

  .btn-primary {
    font-size: 13px;
    padding: 8px 16px;
  }

  .btn-danger-small {
    font-size: 12px;
    padding: 6px 12px;
  }
}

/* 小屏幕进一步优化 */
@media (max-width: 480px) {
  .libraries-container {
    padding: 10px;
  }

  .page-header {
    padding: 12px;
  }

  .page-title {
    font-size: 18px;
  }

  .page-subtitle {
    font-size: 12px;
  }

  .section {
    padding: 12px;
  }

  .section-title {
    font-size: 15px;
  }

  .library-card {
    padding: 12px;
  }

  .library-name {
    font-size: 14px;
  }

  .library-description {
    font-size: 12px;
  }
}
</style>
