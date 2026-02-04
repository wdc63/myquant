<template>
  <div class="main-layout">
    <header class="header">
      <div class="header-content">
        <router-link to="/home" class="logo-link">
          <div class="logo">
            <span class="logo-my">My</span><span class="logo-quant">Quant</span>
          </div>
        </router-link>

        <!-- 移动端汉堡菜单按钮 -->
        <button class="hamburger-btn" @click="mobileMenuOpen = !mobileMenuOpen">
          <svg v-if="!mobileMenuOpen" viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
          <svg v-else viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>

        <!-- 桌面端导航 -->
        <nav class="tabs desktop-nav">
          <router-link to="/home" class="tab-link">
            <svg class="tab-icon" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
              <polyline points="9 22 9 12 15 12 15 22"></polyline>
            </svg>
            首页
          </router-link>
          <router-link to="/strategies" class="tab-link">
            <svg class="tab-icon" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
            策略工作台
          </router-link>
          <router-link to="/docs" class="tab-link">
            <svg class="tab-icon" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            API 文档
          </router-link>
          <router-link to="/libraries" class="tab-link">
            <svg class="tab-icon" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
              <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
              <line x1="12" y1="22.08" x2="12" y2="12"></line>
            </svg>
            库管理
          </router-link>
        </nav>

        <div class="spacer"></div>
        <div class="header-right">
          <button @click="toggleTheme" class="icon-btn" :title="isDark ? '切换到亮色模式' : '切换到暗色模式'">
            <!-- 太阳图标 (亮色模式) -->
            <svg v-if="isDark" viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
            <!-- 月亮图标 (暗色模式) -->
            <svg v-else viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
          </button>
          <button class="icon-btn desktop-only" @click="handleLogout" title="退出登录">
            <!-- 退出图标 -->
            <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- 移动端导航菜单 -->
    <nav v-if="mobileMenuOpen" class="mobile-nav" @click="mobileMenuOpen = false">
      <router-link to="/home" class="mobile-nav-link">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
          <polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>
        <span>首页</span>
      </router-link>
      <router-link to="/strategies" class="mobile-nav-link">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
        </svg>
        <span>策略工作台</span>
      </router-link>
      <router-link to="/docs" class="mobile-nav-link">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
        <span>API 文档</span>
      </router-link>
      <router-link to="/libraries" class="mobile-nav-link">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
        </svg>
        <span>库管理</span>
      </router-link>
      <div class="mobile-nav-divider"></div>
      <button class="mobile-nav-link" @click="handleLogout">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
          <polyline points="16 17 21 12 16 7"></polyline>
          <line x1="21" y1="12" x2="9" y2="12"></line>
        </svg>
        <span>退出登录</span>
      </button>
    </nav>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import apiClient from '../api/axios';
import { ElMessage, ElMessageBox } from 'element-plus';

const router = useRouter();
const isDark = ref(false);
const mobileMenuOpen = ref(false);

const applyTheme = () => {
  if (isDark.value) {
    document.body.classList.add('dark-mode');
    localStorage.setItem('theme', 'dark');
  } else {
    document.body.classList.remove('dark-mode');
    localStorage.setItem('theme', 'light');
  }
};

const toggleTheme = () => {
  isDark.value = !isDark.value;
  applyTheme();
};

onMounted(() => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    isDark.value = savedTheme === 'dark';
    applyTheme();
  }
});

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('您确定要退出登录吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    
    await apiClient.post('/logout');
    localStorage.removeItem('myquant_logged_in');
    ElMessage.success('已成功退出');
    router.push({ name: 'Login' });
  } catch (error) {
    if (error !== 'cancel') {
        ElMessage.error('退出失败，请稍后重试');
    }
  }
};
</script>

<style scoped>
.main-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-primary);
  overflow: hidden;
}

.header {
  background: var(--card-bg);
  padding: 0 24px;
  box-shadow: var(--shadow);
  height: 60px;
  flex-shrink: 0;
  z-index: 100;
  min-width: 0;
  overflow-x: auto;
  overflow-y: visible;
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
  min-width: fit-content;
  overflow: visible;
}

/* 汉堡菜单按钮（移动端） */
.hamburger-btn {
  display: none;
  width: 40px;
  height: 40px;
  margin-left: auto;
  border: none;
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.hamburger-btn:hover {
  background: var(--table-hover-bg);
}

/* 桌面端导航 */
.desktop-nav {
  display: flex;
}

.logo-link {
  text-decoration: none;
  margin-right: 20px;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.logo-link:hover {
  transform: translateY(-1px);
}

.logo {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.5px;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.logo-my {
  color: var(--primary-color);
  font-weight: 800;
}

.logo-quant {
  color: var(--text-primary);
  font-weight: 600;
  position: relative;
}

.logo-quant::after {
  content: '';
  position: absolute;
  bottom: 2px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--primary-color), transparent);
  opacity: 0.6;
}

.tabs {
  display: flex;
  height: 100%;
  flex-shrink: 0;
}

.tab-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--tab-inactive-color);
  border-bottom: 2px solid transparent;
  text-decoration: none;
  transition: color 0.2s, border-color 0.2s;
  white-space: nowrap;
}

.tab-icon {
  flex-shrink: 0;
  opacity: 0.8;
}

.tab-link:hover {
  color: var(--tab-active-color);
}

.tab-link.router-link-exact-active {
  color: var(--tab-active-color);
  border-bottom-color: var(--tab-active-color);
}

.spacer {
  flex-grow: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  position: relative;
  overflow: visible;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s, color 0.2s;
  position: relative;
  overflow: visible;
}

.icon-btn:hover {
  background: var(--table-hover-bg);
  color: var(--primary-color);
}

.icon-btn svg {
  flex-shrink: 0;
}

.icon-btn[title]:hover::after {
  content: attr(title);
  position: fixed;
  top: 65px;
  right: 24px;
  background: rgba(255, 255, 255, 0.95);
  color: #1a1d23;
  padding: 5px 9px;
  border-radius: 4px;
  font-size: 11px;
  white-space: nowrap;
  z-index: 10000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  pointer-events: none;
}

/* 浅色模式下的tooltip */
body:not(.dark-mode) .icon-btn[title]:hover::after {
  background: rgba(0, 0, 0, 0.9);
  color: white;
}

.main-content {
  flex-grow: 1;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 20px;
  width: 100%;
  box-sizing: border-box;
  min-height: 0;
}

/* 移动端导航菜单 */
.mobile-nav {
  display: none;
  position: fixed;
  top: 60px;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--card-bg);
  z-index: 99;
  padding: 20px;
  flex-direction: column;
  gap: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  color: var(--text-primary);
  text-decoration: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  transition: background-color 0.2s, color 0.2s;
  width: 100%;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.mobile-nav-link:hover {
  background: var(--table-hover-bg);
  color: var(--primary-color);
}

.mobile-nav-link.router-link-exact-active {
  background: var(--table-hover-bg);
  color: var(--primary-color);
}

.mobile-nav-link svg {
  flex-shrink: 0;
}

.mobile-nav-divider {
  height: 1px;
  background: var(--border-color);
  margin: 12px 0;
}

.desktop-only {
  display: flex;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }

  .hamburger-btn {
    display: flex;
  }

  .desktop-nav {
    display: none;
  }

  .desktop-only {
    display: none;
  }

  .mobile-nav {
    display: flex;
  }

  .logo {
    font-size: 20px;
  }

  .main-content {
    padding: 12px;
  }

  .spacer {
    flex-grow: 0;
  }

  .header-right {
    gap: 4px;
  }

  .icon-btn {
    width: 40px;
    height: 40px;
  }
}
</style>
