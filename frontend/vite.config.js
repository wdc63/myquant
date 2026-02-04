import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import monacoEditorPlugin from 'vite-plugin-monaco-editor';
import fs from 'fs';
import path from 'path';

// 从全局配置读取端口
// vite.config.js is in myquant/frontend, so we go up one level to myquant/
const configPath = path.resolve(__dirname, '../myquant_config.json');
console.log(`[Vite Config] Trying to load config from: ${configPath}`);

const myquantConfig = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
const vitePort = myquantConfig.frontend_dev?.vite_port || 5173;
const backendPort = myquantConfig.server?.port || 5000;
const backendTarget = `http://127.0.0.1:${backendPort}`;

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
    vue(),
    monacoEditorPlugin.default({}),
  ],
  server: {
    port: vitePort,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/socket.io': {
        target: backendTarget,
        ws: true,
      },
    }
  }
})
