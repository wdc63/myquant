# MyQuant 🧩📊

> 一个给 **QTrader** 配的 WebUI 外壳：策略管理、在线编辑、运行/暂停/恢复、监控与产物下载。

- ✅ **开源版定位**：只依赖 `qtrader`（回测/模拟引擎）
- 🔌 **数据解耦**：通过 QTrader 的 `DataProvider`（数据合约）接入任何数据源
- 🔒 **隐私说明**：原项目中私有的 `stock_api_sdk` / `tdx_api_sdk` 已剥离，不在本仓库中提供

---

## 功能一览 ✨

- 🗂️ 策略管理：创建/删除策略项目
- ✍️ 在线编辑：`strategy.py` / `config.yaml` / `data_provider.py`
- ▶️ 一键运行：回测 / 模拟盘
- ⏸️ 控制：暂停 / 继续 / 停止
- 🖥️ 监控：自动分配端口并代理访问 QTrader 内置监控页
- 📦 产物：报告、日志、workspace 文件浏览与下载

---

## 快速开始 🚀

### 1）准备环境

- Python >= 3.9
- Node.js >= 20

### 2）安装依赖

后端（建议虚拟环境）：

```bash
cd myquant
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# 安装 qtrader（开源版只依赖它）
pip install -e ../pqtrader
```

前端：

```bash
cd frontend
npm install
```

### 3）配置

复制示例配置：

```bash
cp myquant_config.example.json myquant_config.json
```

### 4）启动

后端：

```bash
python backend/app.py
```

前端：

```bash
cd frontend
npm run dev
```

访问：`http://localhost:5173`

---

## 跑一个回测（平台内）✅

1. 打开 MyQuant → 新建策略
2. 在策略目录里会生成 3 个核心文件：
   - `strategy.py`
   - `config.yaml`
   - `data_provider.py`
3. 点击运行（Backtest / Simulation）

### DataProvider（数据合约）要点 🔌

只需实现 `src/qtrader/data/interface.py` 里的三个方法：

- `get_trading_calendar(start, end)`
- `get_current_price(symbol, dt)`
- `get_symbol_info(symbol, date)`

仓库提供了一个 Mock 模板：`templates/data_provider.py`，新策略默认会复制过去。

---

## 文档 📚

- MyQuant 使用说明：`docs/user_guide.md`
- UI/UX 设计说明：`docs/MyQuant_UI_UX_Design_Guide.md`

---

## 开源版与私有 SDK 的关系 🔒

你如果在私有环境里确实需要 `stock_api_sdk / tdx_api_sdk`：

- 建议在私有仓库里实现你自己的 `DataProvider`，并让策略通过 DataProvider 获取行情/交易能力
- 本仓库保留了 `myquant/backend/clients.py` 的同名导出，但它们在开源版默认不可用（会抛出明确提示）

---

## License 📄

建议使用 MIT（如果你确认要开源）。
