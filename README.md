# 零售销售数据分析看板（Supermarket BI Dashboard）

基于Kaggle公开零售数据集，完成从数据建模到可视化分析的完整BI项目链路。

## 项目架构

Kaggle CSV (12 万行，323 列)
↓ Python ETL (02_etl_to_mysql.py)
MySQL 星型模型 (6 张表)
↓
├── Power BI Desktop 交互看板
└── Python 自动生成 HTML 智能报告 (04_smart_report.py)

## 技术栈

- **数据库**：MySQL 8.0（星型模型，事实表 + 5 张维度表）
- **ETL**：Python + Pandas（CSV 分块读取、空值处理、维度去重、批量入库）
- **可视化**：Power BI Desktop（DAX 度量值、切片器、同环比分析）
- **自动报告**：Python + Pyecharts（交互式 HTML 报告，支持年份/区域筛选）

## 数据集

Kaggle: [Supermarket Dataset](https://www.kaggle.com/datasets/datascikhan/supermarket)

- 120,000 笔交易记录
- 75,799 位客户
- 200 家门店
- 5,000 个商品，45 个品类
- 时间跨度：2023.01 - 2024.12（两年完整数据）

## 核心指标

| 指标 | 数值 |
|---|---|
| 总销售额 | ¥10,454,216 |
| 总毛利 | ¥3,770,442 |
| 毛利率 | 36.1% |
| 订单数 | 120,000 |
| 客单价 | ¥87.12 |

## 文件说明

| 文件 | 说明 |
|---|---|
| `01_star_schema.sql` | MySQL 建表 SQL（星型模型 DDL） |
| `02_etl_to_mysql.py` | Python ETL 脚本：CSV → 拆表 → 入库 MySQL |
| `03_dax_measures.md` | Power BI DAX 度量值清单（KPI、同环比、排名） |
| `04_smart_report.py` | Python 自动生成交互式 HTML 分析报告 |
| `config.example.py` | 数据库配置模板（需自行填写密码） |
| `report.html` | 生成的交互式报告示例 |

## 本地运行

1. 创建 MySQL 数据库，执行 `01_star_schema.sql`
2. 复制 `config.example.py` 为 `config.py`，填入数据库密码
3. 安装依赖：`pip install pandas pymysql pyecharts`
4. 运行 ETL：`python 02_etl_to_mysql.py`
5. 运行报告：`python 04_smart_report.py`
6. 用 Power BI Desktop 连接 MySQL，加载 6 张表，建立关系

## 看板功能

- KPI 卡片：总销售额、总毛利、毛利率、订单数、客单价、同比/环比增长率
- 月度销售趋势折线图
- Top10 品类销售排行
- 区域销售对比
- 支付方式占比
- 购物时段分布
- 年份/区域切片器联动筛选

## 项目亮点

- **完整链路**：从原始 CSV 到最终可视化，覆盖数据工程师 + BI 分析师全流程
- **数据建模**：323 列宽表拆分为星型模型，消除冗余，支持多维度分析
- **自动化**：Python 脚本一键完成 ETL 和报告生成，可复用到其他数据集
- **交互设计**：Power BI 看板和 HTML 报告均支持筛选联动
