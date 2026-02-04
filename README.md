# MyQuant 🧩📊

> MyQuant 是一个面向 **QTrader** 的 WebUI：把策略开发、运行与回测产物管理做成“可视化工作台”。

- 🔗 **和 QTrader 的关系**：MyQuant 负责 UI/平台能力；回测/模拟执行由 QTrader 引擎完成
- 🔌 **数据接入方式**：通过 QTrader 的 `DataProvider`（数据合约）接入任意数据源
- 🧱 **可扩展**：内置“平台库管理”（在线安装/卸载第三方 Python 包），把研究环境做成可控的“插件化工具箱”

---

## 功能一览 ✨

- 🗂️ 策略管理：创建/删除策略项目
- ✍️ 在线编辑：`strategy.py` / `config.yaml` / `data_provider.py`
- ▶️ 一键运行：回测 / 模拟盘
- ⏸️ 控制：暂停 / 继续 / 停止
- 🖥️ 监控：自动分配端口并嵌入 QTrader 内置监控页
- 📦 产物管理：报告、日志、workspace 文件浏览与下载
- 🧩 平台库管理（插件化）：WebUI 一键安装/卸载第三方 Python 库（带 pip 输出实时回传）

---

## 截图 🖼️

![MyQuant Screenshot 1](screenshot/sc1.png)
![MyQuant Screenshot 2](screenshot/sc2.png)
![MyQuant Screenshot 3](screenshot/sc3.png)
![MyQuant Screenshot 4](screenshot/sc4.png)
![MyQuant Screenshot 5](screenshot/sc5.png)

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

# 安装 qtrader（回测/模拟引擎）
pip install -e ../pqtrader
```

前端：

```bash
cd frontend
npm install
```

### 3）配置

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

## 运行一个回测（平台内）✅

1. 打开 MyQuant → 新建策略
2. 策略目录会生成 3 个核心文件：
   - `strategy.py`：策略逻辑（生命周期钩子）
   - `config.yaml`：回测/模拟参数（频率、日期、费用、监控端口等）
   - `data_provider.py`：数据提供者（实现数据合约）
3. 点击运行（Backtest / Simulation）

---

## DataProvider（数据合约）🔌

MyQuant 不关心数据来自哪里，它只要求你兑现 QTrader 的数据合约（接口见 `qtrader.data.interface.AbstractDataProvider`）。

必须实现 3 个方法：

- `get_trading_calendar(start, end)`：交易日历
- `get_current_price(symbol, dt)`：某时刻价格快照（至少包含 `current_price`）
- `get_symbol_info(symbol, date)`：标的静态信息（名称、是否停牌）

仓库提供了一个可直接改造的 Mock 模板：`templates/data_provider.py`。

---

## 平台库管理（插件化能力）🧩

MyQuant 内置了“平台库管理”页面，用来把研究环境做成可控的插件系统：

- 📦 **内置库清单**：展示平台核心依赖（以及版本/说明）
- 🔧 **自定义库安装/卸载**：在 WebUI 里输入包名（PyPI），平台用 pip 执行安装/卸载
- 📝 **安装日志可视化**：pip 输出通过 SocketIO 实时回传到页面，便于排错
- 🔐 **权限控制**：安装/卸载需要管理密码（配置在 `myquant_config.json`）

对应后端 API：

- `GET /api/libraries` 获取库列表
- `POST /api/libraries/install` 安装库
- `POST /api/libraries/uninstall` 卸载库

对应前端页面：`frontend/src/views/Libraries.vue`。

---

## 文档 📚

- 平台使用说明：`docs/user_guide.md`
- UI/UX 设计说明：`docs/MyQuant_UI_UX_Design_Guide.md`
