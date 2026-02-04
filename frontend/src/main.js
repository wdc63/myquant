import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import 'element-plus/dist/index.css'
import './theme.css'
import './style.css'

// Apply dark mode theme if saved
if (localStorage.getItem('theme') === 'dark') {
  document.body.classList.add('dark-mode');
}

const app = createApp(App)

app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
})

app.mount('#app')
