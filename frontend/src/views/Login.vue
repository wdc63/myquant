<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <span>MyQuant 平台登录</span>
        </div>
      </template>
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="请输入密码"
            show-password
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            @click="handleLogin"
            :loading="loading"
            class="login-button"
            size="large"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import apiClient from '../api/axios';

const password = ref('');
const loading = ref(false);
const router = useRouter();

// Apply saved theme on mount
onMounted(() => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
    document.body.classList.add('dark-mode');
  } else {
    document.body.classList.remove('dark-mode');
  }
});

const handleLogin = async () => {
  if (!password.value) {
    ElMessage.warning('请输入密码');
    return;
  }
  loading.value = true;
  try {
    await apiClient.post('/login', { password: password.value });
    ElMessage.success('登录成功');
    // 跳转到策略工作台
    router.push({ name: 'StrategiesDashboard' });
  } catch (error) {
    const message = error.response?.data?.message || '登录失败，请重试';
    ElMessage.error(message);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: var(--bg-primary);
  transition: background 0.3s ease;
}

.login-card {
  width: 400px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
}

.card-header {
  text-align: center;
  font-size: 20px;
  font-weight: bold;
  color: var(--text-primary);
}

.login-button {
  width: 100%;
}

/* Dark mode specific adjustments */
:deep(.el-input__wrapper) {
  background-color: var(--card-bg);
  border-color: var(--border-color);
}

:deep(.el-input__inner) {
  color: var(--text-primary);
}
</style>