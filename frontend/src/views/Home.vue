<template>
  <div class="home-container">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-text">专业量化回测平台</span>
        </div>
        <h1 class="hero-title">
          <div class="title-logo">
            <span class="logo-my">My</span><span class="logo-quant">Quant</span>
          </div>
          <span class="title-sub">量化交易平台</span>
        </h1>
        <p class="hero-description">
          基于 QTrader 框架，提供专业的量化策略回测与模拟交易环境
        </p>
        <p class="hero-subtitle">
          支持 Python 策略编写 · 实时监控 · 完整报告 · 灵活配置
        </p>

        <!-- CTA Buttons -->
        <div class="cta-buttons">
          <button class="btn-primary" @click="goToStrategies">
            <span class="btn-icon">📊</span>
            <span class="btn-text">创建策略</span>
          </button>
          <button class="btn-secondary" @click="goToDocs">
            <span class="btn-icon">📚</span>
            <span class="btn-text">查看文档</span>
          </button>
        </div>
      </div>

      <!-- Decorative Elements -->
      <div class="hero-decoration">
        <!-- K-line Background Chart -->
        <svg class="kline-background" viewBox="0 0 1200 400" preserveAspectRatio="xMidYMid slice">
          <defs>
            <linearGradient id="klineGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" :style="{ stopColor: 'var(--primary-color)', stopOpacity: 0.25 }" />
              <stop offset="100%" :style="{ stopColor: 'var(--primary-color)', stopOpacity: 0.08 }" />
            </linearGradient>
          </defs>

          <!-- Background curve -->
          <path d="M 0,250 Q 150,150 300,180 T 600,220 T 900,160 T 1200,200"
                fill="url(#klineGradient)" opacity="0.5" />
          <path d="M 0,250 Q 150,150 300,180 T 600,220 T 900,160 T 1200,200"
                fill="none" :stroke="primaryColor" stroke-width="2" opacity="0.3" />

          <!-- Candlesticks -->
          <g opacity="0.2">
            <rect x="50" y="180" width="12" height="40" :fill="positiveColor" />
            <line x1="56" y1="160" x2="56" y2="220" :stroke="positiveColor" stroke-width="1.5" />

            <rect x="100" y="200" width="12" height="30" :fill="negativeColor" />
            <line x1="106" y1="190" x2="106" y2="230" :stroke="negativeColor" stroke-width="1.5" />

            <rect x="150" y="160" width="12" height="50" :fill="positiveColor" />
            <line x1="156" y1="140" x2="156" y2="210" :stroke="positiveColor" stroke-width="1.5" />

            <rect x="200" y="190" width="12" height="35" :fill="positiveColor" />
            <line x1="206" y1="175" x2="206" y2="225" :stroke="positiveColor" stroke-width="1.5" />

            <rect x="250" y="205" width="12" height="25" :fill="negativeColor" />
            <line x1="256" y1="195" x2="256" y2="230" :stroke="negativeColor" stroke-width="1.5" />

            <rect x="300" y="175" width="12" height="45" :fill="positiveColor" />
            <line x1="306" y1="155" x2="306" y2="220" :stroke="positiveColor" stroke-width="1.5" />

            <rect x="350" y="195" width="12" height="28" :fill="negativeColor" />
            <line x1="356" y1="185" x2="356" y2="223" :stroke="negativeColor" stroke-width="1.5" />

            <rect x="400" y="210" width="12" height="32" :fill="positiveColor" />
            <line x1="406" y1="198" x2="406" y2="242" :stroke="positiveColor" stroke-width="1.5" />

            <rect x="450" y="218" width="12" height="20" :fill="negativeColor" />
            <line x1="456" y1="210" x2="456" y2="238" :stroke="negativeColor" stroke-width="1.5" />

            <rect x="500" y="200" width="12" height="38" :fill="positiveColor" />
            <line x1="506" y1="185" x2="506" y2="238" :stroke="positiveColor" stroke-width="1.5" />

            <rect x="550" y="215" width="12" height="25" :fill="positiveColor" />
            <line x1="556" y1="205" x2="556" y2="240" :stroke="positiveColor" stroke-width="1.5" />

            <rect x="600" y="205" width="12" height="35" :fill="negativeColor" />
            <line x1="606" y1="195" x2="606" y2="240" :stroke="negativeColor" stroke-width="1.5" />

            <rect x="650" y="175" width="12" height="50" :fill="positiveColor" />
            <line x1="656" y1="160" x2="656" y2="225" :stroke="positiveColor" stroke-width="1.5" />

            <rect x="700" y="190" width="12" height="30" :fill="negativeColor" />
            <line x1="706" y1="180" x2="706" y2="220" :stroke="negativeColor" stroke-width="1.5" />

            <rect x="750" y="165" width="12" height="45" :fill="positiveColor" />
            <line x1="756" y1="150" x2="756" y2="210" :stroke="positiveColor" stroke-width="1.5" />

            <rect x="800" y="180" width="12" height="38" :fill="positiveColor" />
            <line x1="806" y1="165" x2="806" y2="218" :stroke="positiveColor" stroke-width="1.5" />

            <rect x="850" y="195" width="12" height="28" :fill="negativeColor" />
            <line x1="856" y1="185" x2="856" y2="223" :stroke="negativeColor" stroke-width="1.5" />

            <rect x="900" y="160" width="12" height="52" :fill="positiveColor" />
            <line x1="906" y1="145" x2="906" y2="212" :stroke="positiveColor" stroke-width="1.5" />

            <rect x="950" y="175" width="12" height="40" :fill="positiveColor" />
            <line x1="956" y1="160" x2="956" y2="215" :stroke="positiveColor" stroke-width="1.5" />

            <rect x="1000" y="190" width="12" height="32" :fill="negativeColor" />
            <line x1="1006" y1="180" x2="1006" y2="222" :stroke="negativeColor" stroke-width="1.5" />

            <rect x="1050" y="185" width="12" height="35" :fill="positiveColor" />
            <line x1="1056" y1="170" x2="1056" y2="220" :stroke="positiveColor" stroke-width="1.5" />

            <rect x="1100" y="200" width="12" height="28" :fill="negativeColor" />
            <line x1="1106" y1="190" x2="1106" y2="228" :stroke="negativeColor" stroke-width="1.5" />

            <rect x="1150" y="195" width="12" height="35" :fill="positiveColor" />
            <line x1="1156" y1="180" x2="1156" y2="230" :stroke="positiveColor" stroke-width="1.5" />
          </g>
        </svg>

        <div class="floating-card card-1">
          <div class="card-header">策略收益</div>
          <div class="card-value positive">+12.5%</div>
        </div>
        <div class="floating-card card-2">
          <div class="card-header">回测速度</div>
          <div class="card-value">1000x</div>
        </div>
        <div class="floating-card card-3">
          <div class="card-header">策略数量</div>
          <div class="card-value">{{ strategiesCount }}</div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <h2 class="section-title">核心功能</h2>
      <div class="features-grid">
        <div class="feature-card" v-for="feature in features" :key="feature.title">
          <div class="feature-icon">{{ feature.icon }}</div>
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-description">{{ feature.description }}</p>
        </div>
      </div>
    </section>

    <!-- Tech Stack Section -->
    <section class="tech-section">
      <h2 class="section-title">技术栈</h2>
      <div class="tech-tags">
        <span class="tech-tag" v-for="tech in techStack" :key="tech">{{ tech }}</span>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import apiClient from '../api/axios';

const router = useRouter();
const strategiesCount = ref(0);

// Define colors for K-line chart
const primaryColor = computed(() =>
  getComputedStyle(document.documentElement).getPropertyValue('--primary-color') || '#3b82f6'
);
const positiveColor = computed(() => '#ef4444'); // Red for positive (Chinese convention)
const negativeColor = computed(() => '#10b981'); // Green for negative (Chinese convention)

const features = [
  {
    icon: '🎯',
    title: '策略编写',
    description: '基于 Python 的策略开发环境，支持完整的事件驱动框架'
  },
  {
    icon: '📊',
    title: '可视分析',
    description: '回测全过程实时曲线展示，收益、持仓、订单等多维度指标可视化'
  },
  {
    icon: '💾',
    title: '全面数据',
    description: '覆盖 2005 至今 A 股、ETF、EOF 全市场数据，支持 Tick 级别行情与完整财务数据'
  },
  {
    icon: '⚙️',
    title: '灵活配置',
    description: '支持初始资金、交易费率、滑点等多种参数的灵活配置'
  },
  {
    icon: '🔄',
    title: '暂停恢复',
    description: '支持策略运行暂停与恢复，灵活控制回测进度'
  },
  {
    icon: '🚀',
    title: '实盘对接',
    description: '无缝对接实盘交易接口，策略验证后可直接部署至真实交易环境'
  }
];

const techStack = [
  'Python',
  'QTrader',
  'Vue 3',
  'Element Plus',
  'ECharts',
  'Monaco Editor',
  'FastAPI',
  'SocketIO'
];

onMounted(async () => {
  try {
    const response = await apiClient.get('/strategies');
    strategiesCount.value = response.data.strategies.length;
  } catch (error) {
    console.error('Failed to fetch strategies count:', error);
  }
});

const goToStrategies = () => {
  router.push({ name: 'StrategiesDashboard' });
};

const goToDocs = () => {
  router.push({ name: 'Docs' });
};
</script>

<style scoped>
.home-container {
  min-height: calc(100vh - 100px);
  padding: 0;
}

/* Hero Section */
.hero-section {
  position: relative;
  padding: 100px 40px;
  background: linear-gradient(135deg,
    var(--bg-primary) 0%,
    var(--table-header-bg) 100%
  );
  overflow: hidden;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
  position: relative;
  z-index: 2;
}

.hero-badge {
  display: inline-block;
  padding: 8px 20px;
  background: var(--primary-color);
  color: white;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 32px;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.badge-text {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hero-title {
  font-size: 64px;
  font-weight: 800;
  margin-bottom: 24px;
  line-height: 1.2;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.title-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 64px;
  font-weight: 800;
  letter-spacing: -2px;
}

.title-logo .logo-my {
  color: var(--primary-color);
  font-weight: 800;
}

.title-logo .logo-quant {
  color: var(--text-primary);
  font-weight: 600;
  position: relative;
}

.title-logo .logo-quant::after {
  content: '';
  position: absolute;
  bottom: 2px;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--primary-color), transparent);
  opacity: 0.6;
}

.title-sub {
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 2px;
}

.hero-description {
  font-size: 20px;
  color: var(--text-primary);
  margin-bottom: 16px;
  font-weight: 500;
}

.hero-subtitle {
  font-size: 16px;
  color: var(--header-info-color);
  margin-bottom: 48px;
}

.cta-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-primary,
.btn-secondary {
  padding: 16px 32px;
  font-size: 18px;
  font-weight: 600;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
}

.btn-secondary {
  background: var(--card-bg);
  color: var(--text-primary);
  border: 2px solid var(--border-color);
}

.btn-secondary:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.btn-icon {
  font-size: 24px;
}

/* Floating Cards and K-line Background */
.hero-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1;
}

.kline-background {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  opacity: 0.7;
  pointer-events: none;
}

.floating-card {
  position: absolute;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px 24px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  animation: float 6s ease-in-out infinite;
}

.card-header {
  font-size: 12px;
  color: var(--header-info-color);
  margin-bottom: 8px;
  font-weight: 500;
}

.card-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.card-value.positive {
  color: var(--positive-color);
}

.card-1 {
  top: 15%;
  left: 10%;
  animation-delay: 0s;
}

.card-2 {
  top: 60%;
  right: 8%;
  animation-delay: 2s;
}

.card-3 {
  bottom: 15%;
  left: 15%;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-20px);
  }
}

/* Features Section */
.features-section {
  padding: 80px 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.section-title {
  font-size: 36px;
  font-weight: 700;
  text-align: center;
  margin-bottom: 60px;
  color: var(--text-primary);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 32px;
}

.feature-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 32px;
  transition: all 0.3s ease;
  cursor: default;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  border-color: var(--primary-color);
}

.feature-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.feature-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.feature-description {
  font-size: 15px;
  color: var(--header-info-color);
  line-height: 1.6;
}

/* Tech Stack Section */
.tech-section {
  padding: 60px 40px 100px;
  max-width: 1200px;
  margin: 0 auto;
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: center;
  margin-top: 40px;
}

.tech-tag {
  padding: 12px 24px;
  background: var(--table-header-bg);
  color: var(--text-primary);
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.tech-tag:hover {
  background: var(--primary-color);
  color: white;
  transform: scale(1.05);
  border-color: var(--primary-color);
}

/* Responsive */
@media (max-width: 768px) {
  .hero-section {
    padding: 60px 20px;
  }

  .hero-title {
    font-size: 42px;
  }

  .title-logo {
    font-size: 42px;
  }

  .title-sub {
    font-size: 24px;
  }

  .floating-card {
    display: none;
  }

  .cta-buttons {
    flex-direction: column;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
    justify-content: center;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }
}
</style>
