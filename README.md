# 老人助餐补贴数据分析系统

面向民政系统的老人助餐补贴业务数据分析工具，基于 Python + pandas，覆盖补贴使用、餐品适配、配送时效、核销合规、满意度趋势五大分析维度，输出可追溯至原始记录的明细清单供复核。

## 原始需求

> 交付一套可复跑的数据分析脚本，Python pandas 足够处理老人档案、订餐流水、核销凭证和配送明细。输入数据包括老人档案、补贴等级、取餐方式、餐品营养、订餐记录、配送时间、核销凭证和满意回访。分析结果需要回答几个业务问题：哪些老人长期未使用补贴，哪些餐品不适合糖尿病或高血压老人，哪些配送路线经常超时，哪些核销记录疑似冒领代领，哪些社区食堂的满意度下降。输出不只是图表，还要有可追到原始记录的明细清单，让民政窗口能拿着结果去复核。

## 技术栈

- Python 3.11
- pandas >= 2.0
- numpy >= 1.24

## 项目结构

```
├── run_all.py                  # 主运行脚本（默认只执行分析，不覆盖输入数据）
├── requirements.txt            # Python 依赖
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── data/                       # 输入数据（CSV）
│   ├── elderly_profiles.csv    # 老人档案
│   ├── subsidy_levels.csv      # 补贴等级
│   ├── pickup_methods.csv      # 取餐方式
│   ├── meal_nutrition.csv      # 餐品营养
│   ├── order_records.csv       # 订餐记录
│   ├── delivery_times.csv      # 配送时间
│   ├── verification_vouchers.csv # 核销凭证
│   └── satisfaction_surveys.csv  # 满意回访
├── scripts/
│   ├── generate_data.py        # 模拟数据生成（需显式触发，不会自动覆盖）
│   ├── analysis_subsidy.py     # 分析1：长期未使用补贴老人筛查
│   ├── analysis_meal.py        # 分析2：餐品与慢病适配风险
│   ├── analysis_delivery.py    # 分析3：配送路线超时分析
│   ├── analysis_verify.py      # 分析4：核销记录冒领代领疑似筛查
│   └── analysis_satisfaction.py # 分析5：社区食堂满意度下降趋势
└── output/                     # 分析结果输出
    ├── 1_长期未使用补贴老人明细.csv
    ├── 2_餐品慢病风险明细.csv
    ├── 3_配送超时明细.csv
    ├── 3_路线超时统计.csv
    ├── 4_核销异常明细.csv
    ├── 5_食堂月度满意度趋势.csv
    ├── 5_满意度下降食堂明细.csv
    └── 5_下降食堂差评明细.csv
```

## 五大分析说明

| 分析编号 | 业务问题 | 筛查逻辑 | 输出明细 |
|---------|---------|---------|---------|
| 1 | 哪些老人长期未使用补贴 | 最近90天无订餐记录的生效补贴老人 | 老人ID、姓名、补贴类型、月补贴金额、最近下单日期、未使用天数 |
| 2 | 哪些餐品不适合糖尿病或高血压老人 | 糖尿病老人点糖≥10g餐品、高血压老人点钠≥1000mg餐品 | 订单ID、老人ID、慢病标签、餐品名称、糖/钠含量 |
| 3 | 哪些配送路线经常超时 | 实际送达超承诺>15分钟，按路线统计超时率 | 配送ID、路线编号、配送员、超时分钟、关联老人信息 |
| 4 | 哪些核销记录疑似冒领代领 | 堂食/自提却手工核销、同一老人2小时内多次核销、连续非人脸核销 | 核销ID、老人ID、核销方式、异常类型、异常说明 |
| 5 | 哪些社区食堂满意度下降 | 连续2月评分下降或累计降幅超30% | 食堂名称、首末月评分、变化率、差评明细 |

## 启动方式

### 前置要求

- Docker 和 Docker Compose（推荐方式）
- 或 Python 3.11+、pip

### 运行模式说明

本系统有两种运行模式：

- **分析模式（默认）**：读取 `data/` 目录中的现有 CSV 执行分析，**不会修改或覆盖输入数据**。适合日常复跑和接入真实业务数据。
- **数据生成模式**：通过 `--generate` 或 `--force-generate` 参数触发，生成模拟数据到 `data/` 目录。适合首次使用或需要重置数据时。

### 方式一：Docker 一键启动（推荐）

#### 首次使用：生成模拟数据并执行分析

```bash
docker compose up --build generate
```

此命令会生成模拟数据并执行全部分析，结果输出到 `output/` 目录。

#### 日常复跑：只执行分析（不覆盖数据）

```bash
docker compose up --build analysis
```

此命令仅读取 `data/` 目录中现有的 CSV 执行分析，不会修改输入数据。

后台运行：

```bash
docker compose up --build analysis -d
```

查看运行日志：

```bash
docker compose logs analysis
```

停止并清理：

```bash
docker compose down
```

分析结果输出在 `output/` 目录，Docker 通过卷挂载将结果写回宿主机。

### 方式二：本地 Python 运行

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 首次使用：生成模拟数据

```bash
python run_all.py --generate
```

此命令会生成模拟数据并执行全部分析。

#### 3. 日常复跑：只执行分析（不覆盖数据）

```bash
python run_all.py
```

此命令仅读取 `data/` 目录中现有的 CSV 执行分析，不会修改输入数据。

#### 4. 强制重新生成模拟数据

```bash
python run_all.py --force-generate
```

此命令会覆盖 `data/` 目录中的现有文件并执行分析。

访问地址：本项目为命令行数据分析工具，无 Web 界面。运行后查看 `output/` 目录下的 CSV 文件即为分析结果。

### 替换真实数据

1. 将 `data/` 目录下的 CSV 文件替换为实际业务数据（保持相同的列名和格式）
2. 运行 `python run_all.py` 即可执行分析
3. 分析输出的每条明细均包含原始记录ID（订单ID、老人ID、核销ID等），可直接追溯到源数据

## 数据生成安全保护

- 直接运行 `python scripts/generate_data.py` 时，如果 `data/` 目录已有 CSV 文件，会提示确认而不会直接覆盖
- 需设置环境变量 `FORCE_GENERATE=1` 才能覆盖已有数据
- 通过 `run_all.py --generate` 触发时会自动确认覆盖（仅当 data/ 为空时）
- 通过 `run_all.py --force-generate` 触发时会强制覆盖已有数据

## 分析阈值参数

各分析脚本的阈值可在对应脚本中调整：

| 参数 | 默认值 | 所在脚本 | 说明 |
|-----|-------|---------|-----|
| INACTIVE_DAYS | 90 | analysis_subsidy.py | 未使用补贴判定天数 |
| SUGAR_THRESHOLD_HIGH | 10 | analysis_meal.py | 高糖餐品阈值(g) |
| SODIUM_THRESHOLD_HIGH | 1000 | analysis_meal.py | 高钠餐品阈值(mg) |
| OVERTIME_THRESHOLD_MINUTES | 15 | analysis_delivery.py | 配送超时阈值(分钟) |
| SAME_ELDER_GAP_MINUTES | 120 | analysis_verify.py | 短时间重核阈值(分钟) |
| DECLINE_CONSECUTIVE_MONTHS | 2 | analysis_satisfaction.py | 连续下降判定月数 |
| DECLINE_RATIO_THRESHOLD | -0.3 | analysis_satisfaction.py | 显著下降变化率阈值 |
