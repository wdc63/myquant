import { createRouter, createWebHistory } from 'vue-router';
import Login from '../views/Login.vue';
import MainLayout from '../layouts/MainLayout.vue';

// 稍后我们将创建这些组件
import Home from '../views/Home.vue';
import StrategiesDashboard from '../views/StrategiesDashboard.vue';
import StrategyEditor from '../views/StrategyEditor.vue';
import RunDetails from '../views/RunDetails.vue';
import Docs from '../views/Docs.vue';
import Libraries from '../views/Libraries.vue';
import ReportView from '../components/ReportView.vue';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/home',
    children: [
      {
        path: 'home',
        name: 'Home',
        component: Home,
        meta: { title: '首页' }
      },
      {
        path: 'strategies',
        name: 'StrategiesDashboard',
        component: StrategiesDashboard,
        meta: { title: '策略工作台' }
      },
      {
        path: 'strategies/:strategy_name',
        name: 'StrategyEditor',
        component: StrategyEditor,
        props: true,
        meta: { title: '策略编辑' }
      },
      {
        path: 'runs/:run_id',
        name: 'RunDetails',
        component: RunDetails,
        props: true,
        meta: { title: '运行详情' }
      },
      {
        path: 'docs',
        name: 'Docs',
        component: Docs,
        meta: { title: '开发文档' }
      },
      {
        path: 'libraries',
        name: 'Libraries',
        component: Libraries,
        meta: { title: '库管理' }
      },
      {
        path: 'reports/:runId',
        name: 'ReportView',
        component: ReportView,
        props: true,
        meta: { title: '回测报告' }
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

import apiClient from '../api/axios';

// 导航守卫
router.beforeEach(async (to, from, next) => {
  // 更新页面标题
  const baseTitle = 'MyQuant 量化交易平台';
  if (to.meta.title) {
    document.title = `${to.meta.title} - ${baseTitle}`;
  } else {
    document.title = baseTitle;
  }

  // 检查是否是公共页面
  const isPublicPage = to.name === 'Login';

  try {
    // 尝试从后端获取真实登录状态
    const response = await apiClient.get('/check-auth');
    const isLoggedIn = response.data.logged_in;

    if (isLoggedIn) {
      // 如果用户已登录
      if (isPublicPage) {
        // 但想访问登录页，则重定向到首页
        next({ name: 'Home' });
      } else {
        // 访问其他页面，正常放行
        next();
      }
    } else {
      // 如果用户未登录
      if (isPublicPage) {
        // 访问的是登录页，正常放行
        next();
      } else {
        // 访问其他页面，重定向到登录页
        next({ name: 'Login' });
      }
    }
  } catch (error) {
    // 如果检查auth状态的API调用失败（例如网络错误或后端服务关闭）
    // 阻止所有导航，并重定向到登录页以避免循环
    console.error('Auth check failed:', error);
    if (!isPublicPage) {
      next({ name: 'Login' });
    } else {
      next();
    }
  }
});

export default router;