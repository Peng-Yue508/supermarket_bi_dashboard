# Power BI DAX 度量清单（Supermarket BI 看板）

> 在 Power BI Desktop 中：进入「数据视图」→ 选中 fact_sales 表 → 「新建度量值」，逐条粘贴。
> 前提：已按 star_schema.sql 建好 6 张表，并在 Power BI 里建好表间关系。

---

## 一、核心 KPI

```dax
-- 总销售额（净销售额）
总销售额 = SUM(fact_sales[net_sales])

-- 总毛利
总毛利 = SUM(fact_sales[gross_profit])

-- 毛利率
毛利率 = DIVIDE([总毛利], [总销售额])

-- 销售数量
总销量 = SUM(fact_sales[quantity])

-- 订单数（去重）
订单数 = DISTINCTCOUNT(fact_sales[transaction_id])

-- 交易行数
交易行数 = COUNTROWS(fact_sales)

-- 客单价
客单价 = DIVIDE([总销售额], [订单数])

-- 平均交易金额
平均交易金额 = DIVIDE([总销售额], [交易行数])
```

## 二、时间智能（同比 / 环比 / YTD）

```dax
-- 上年同期销售额
上年同期销售额 = CALCULATE([总销售额], SAMEPERIODLASTYEAR('dim_date'[full_date]))

-- 同比增长率
同比增长率 = DIVIDE([总销售额] - [上年同期销售额], [上年同期销售额])

-- 上月销售额
上月销售额 = CALCULATE([总销售额], DATEADD('dim_date'[full_date], -1, MONTH))

-- 环比增长率
环比增长率 = DIVIDE([总销售额] - [上月销售额], [上月销售额])

-- 年初至今销售额（YTD）
YTD销售额 = TOTALYTD([总销售额], 'dim_date'[full_date])

-- 上年同期 YTD
上年YTD = TOTALYTD([上年同期销售额], 'dim_date'[full_date])

-- YTD 同比
YTD同比 = DIVIDE([YTD销售额] - [上年YTD], [上年YTD])
```

## 三、排名 / 占比

```dax
-- 品类销售额排名
品类销售排名 = RANKX(ALL(dim_product[product_category]), [总销售额])

-- 门店销售额排名
门店销售排名 = RANKX(ALL(dim_store[store_id]), [总销售额])

-- 各品类销售额占比
品类占比 = DIVIDE([总销售额], CALCULATE([总销售额], ALL(dim_product[product_category])))

-- Top N 品类（动态筛选用）
TopN品类销售额 =
VAR TopN = SELECTEDVALUE('参数表'[N], 5)
RETURN
CALCULATE([总销售额],
    TOPN(TopN, ALL(dim_product[product_category]), [总销售额], DESC))

-- 会员 vs 普通客户销售额
会员销售额 = CALCULATE([总销售额], dim_customer[customer_membership_status] = "Member")
普通客户销售额 = CALCULATE([总销售额], dim_customer[customer_membership_status] = "Normal")
会员占比 = DIVIDE([会员销售额], [总销售额])
```

## 四、客户 / 运营指标

```dax
-- 客户数
客户数 = DISTINCTCOUNT(fact_sales[customer_id])

-- 复购率（有重复交易的客户占比）
复购率 =
VAR 客户交易次数 = SUMMARIZE(fact_sales, fact_sales[customer_id], "次数", COUNTROWS(fact_sales))
RETURN DIVIDE(COUNTROWS(FILTER(客户交易次数, [次数] > 1)), COUNTROWS(客户交易次数))

-- 平均折扣率
平均折扣率 = AVERAGE(fact_sales[discount_percent])

-- 支付方式占比（动态）
支付方式占比 = DIVIDE([总销售额], CALCULATE([总销售额], ALL(dim_payment[payment_method])))
```

## 五、建议看板页面结构

| 页面 | 视觉对象 |
|---|---|
| 总览 Dashboard | KPI 卡片（总销售额/毛利/毛利率/订单数/客单价）+ 月度趋势折线 + 区域柱状图 |
| 品类分析 | Top10 品类条形图 + 品类占比饼图 + 品类排名表 |
| 客户分析 | 会员vs普通对比 + 客户分层漏斗 + RFM 散点图 |
| 门店对比 | 门店排名条形图 + 区域地图（可选）+ 门店评分 |
| 时间分析 | YoY 折线 + 月度环比柱状 + 时段热力图 |
