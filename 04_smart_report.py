# -*- coding: utf-8 -*-
"""
智能分析报告 (交互版): MySQL预聚合 → 嵌入HTML → 前端JS筛选
"""
import pymysql
import pandas as pd
import json
import config

def get_conn():
    return pymysql.connect(host="localhost", user="root", password=config.MYSQL_PWD,
                           database="supermarket_bi", charset="utf8mb4")

def q(sql):
    with get_conn() as conn:
        return pd.read_sql(sql, conn)

def main():
    # 每个图表单独预聚合, 数据量极小
    # 1. 月度趋势
    monthly = q("""
      SELECT d.year, s.store_region,
             CONCAT(d.year, '-', LPAD(d.month, 2, '0')) AS ym,
             ROUND(SUM(f.net_sales),2) AS sales,
             ROUND(SUM(f.gross_profit),2) AS profit,
             COUNT(*) AS orders
      FROM fact_sales f
      JOIN dim_date d ON f.date_id=d.date_id
      JOIN dim_store s ON f.store_id=s.store_id
      GROUP BY d.year, s.store_region, ym
    """)

    # 2. 品类
    cat = q("""
      SELECT d.year, s.store_region, p.product_category,
             ROUND(SUM(f.net_sales),2) AS sales
      FROM fact_sales f
      JOIN dim_date d ON f.date_id=d.date_id
      JOIN dim_store s ON f.store_id=s.store_id
      JOIN dim_product p ON f.product_id=p.product_id
      GROUP BY d.year, s.store_region, p.product_category
    """)

    # 3. 区域
    region = q("""
      SELECT d.year, s.store_region,
             ROUND(SUM(f.net_sales),2) AS sales
      FROM fact_sales f
      JOIN dim_date d ON f.date_id=d.date_id
      JOIN dim_store s ON f.store_id=s.store_id
      GROUP BY d.year, s.store_region
    """)

    # 4. 支付方式
    pay = q("""
      SELECT d.year, s.store_region, f.payment_method,
             ROUND(SUM(f.net_sales),2) AS sales
      FROM fact_sales f
      JOIN dim_date d ON f.date_id=d.date_id
      JOIN dim_store s ON f.store_id=s.store_id
      GROUP BY d.year, s.store_region, f.payment_method
    """)

    # 5. 购物时段
    period = q("""
      SELECT d.year, s.store_region, f.shopping_period,
             ROUND(SUM(f.net_sales),2) AS sales
      FROM fact_sales f
      JOIN dim_date d ON f.date_id=d.date_id
      JOIN dim_store s ON f.store_id=s.store_id
      GROUP BY d.year, s.store_region, f.shopping_period
    """)

    # 6. KPI totals (按年+区域)
    kpi = q("""
      SELECT d.year, s.store_region,
             ROUND(SUM(f.net_sales),2) AS sales,
             ROUND(SUM(f.gross_profit),2) AS profit,
             COUNT(*) AS orders
      FROM fact_sales f
      JOIN dim_date d ON f.date_id=d.date_id
      JOIN dim_store s ON f.store_id=s.store_id
      GROUP BY d.year, s.store_region
    """)

    years = sorted(monthly["year"].unique().tolist())
    regions = sorted(monthly["store_region"].dropna().unique().tolist())
    year_opts = "".join(f'<option value="{y}">{y}</option>' for y in years)
    region_opts = "".join(f'<option value="{r}">{r}</option>' for r in regions)

    data = {
        "kpi": kpi.to_dict(orient="records"),
        "monthly": monthly.to_dict(orient="records"),
        "category": cat.to_dict(orient="records"),
        "region": region.to_dict(orient="records"),
        "payment": pay.to_dict(orient="records"),
        "period": period.to_dict(orient="records"),
    }
    data_json = json.dumps(data, default=str)
    print(f"数据量: kpi={len(kpi)}, monthly={len(monthly)}, category={len(cat)}")

    html = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>零售销售数据分析报告</title>
<script src="https://cdn.bootcdn.net/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI','Microsoft YaHei',sans-serif; background: #f0f2f5; color: #333; padding: 24px; }
.container { max-width: 1200px; margin: 0 auto; }
h1 { font-size: 28px; margin-bottom: 16px; }
.filters { display: flex; gap: 16px; margin-bottom: 20px; align-items: center; }
.filters label { font-size: 14px; color: #555; }
.filters select { padding: 6px 12px; border-radius: 6px; border: 1px solid #ddd; font-size: 14px; }
.kpi-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 20px; }
.kpi-card { background: #fff; border-radius: 10px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.kpi-card .label { font-size: 13px; color: #888; margin-bottom: 6px; }
.kpi-card .value { font-size: 26px; font-weight: 700; color: #1a73e8; }
.kpi-card .value.green { color: #0d9e5f; }
.alert { background: #fffbe6; border-left: 4px solid #faad14; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; font-size: 13px; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.card { background: #fff; border-radius: 10px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.chart { width: 100%; height: 320px; }
.chart-sm { width: 100%; height: 280px; }
@media (max-width: 768px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .grid-2, .grid-3 { grid-template-columns: 1fr; }
}
</style></head><body>
<div class="container">
  <h1>零售销售数据分析报告</h1>
  <div class="filters">
    <label>年份：<select id="f-year"><option value="all">全部</option>__YEAR_OPTS__</select></label>
    <label>区域：<select id="f-region"><option value="all">全部</option>__REGION_OPTS__</select></label>
  </div>
  <div class="kpi-row">
    <div class="kpi-card"><div class="label">总销售额</div><div class="value" id="kpi-sales">-</div></div>
    <div class="kpi-card"><div class="label">总毛利</div><div class="value" id="kpi-profit">-</div></div>
    <div class="kpi-card"><div class="label">毛利率</div><div class="value green" id="kpi-margin">-</div></div>
    <div class="kpi-card"><div class="label">订单数</div><div class="value" id="kpi-orders">-</div></div>
    <div class="kpi-card"><div class="label">客单价</div><div class="value" id="kpi-aov">-</div></div>
  </div>
  <div class="alert"><b>🔔 智能异常检测</b><br><span id="alert-text"></span></div>
  <div class="card" style="margin-bottom:16px;"><div id="chart-line" class="chart"></div></div>
  <div class="grid-2">
    <div class="card"><div id="chart-bar" class="chart"></div></div>
    <div class="card"><div id="chart-region" class="chart-sm"></div></div>
  </div>
  <div class="grid-3">
    <div class="card"><div id="chart-pay" class="chart-sm"></div></div>
    <div class="card"><div id="chart-period" class="chart-sm"></div></div>
    <div class="card" style="display:flex;flex-direction:column;justify-content:center;padding:20px;">
      <h3 style="font-size:15px;margin-bottom:12px;">📌 关键结论</h3>
      <ul id="conclusions" style="font-size:13px;line-height:2;color:#555;padding-left:18px;"></ul>
    </div>
  </div>
</div>
<script>
const D = __DATA_JSON__;
const charts = {};

function filterRows(rows) {
  const y = document.getElementById('f-year').value;
  const r = document.getElementById('f-region').value;
  return rows.filter(d =>
    (y === 'all' || String(d.year) === y) &&
    (r === 'all' || d.store_region === r)
  );
}

function fmtWan(v) { return '\u00a5' + (v/10000).toFixed(1) + ' \u4e07'; }

function render() {
  // KPI
  const kRows = filterRows(D.kpi);
  const sales = kRows.reduce((s,d)=>s+(+d.sales||0),0);
  const profit = kRows.reduce((s,d)=>s+(+d.profit||0),0);
  const orders = kRows.reduce((s,d)=>s+(+d.orders||0),0);
  document.getElementById('kpi-sales').textContent = fmtWan(sales);
  document.getElementById('kpi-profit').textContent = fmtWan(profit);
  document.getElementById('kpi-margin').textContent = sales ? (profit/sales*100).toFixed(1)+'%' : '-';
  document.getElementById('kpi-orders').textContent = orders.toLocaleString();
  document.getElementById('kpi-aov').textContent = orders ? '\u00a5' + (sales/orders).toFixed(1) : '-';

  // 月度趋势
  const mRows = filterRows(D.monthly);
  const mAgg = {};
  mRows.forEach(d => {
    if (!mAgg[d.ym]) mAgg[d.ym] = {sales:0, profit:0};
    mAgg[d.ym].sales += +d.sales||0;
    mAgg[d.ym].profit += +d.profit||0;
  });
  const months = Object.keys(mAgg).sort();
  if (!charts.line) charts.line = echarts.init(document.getElementById('chart-line'));
  charts.line.setOption({
    title: {text:'\u6708\u5ea6\u9500\u552e\u8d8b\u52bf\uff08\u4e07\u5143\uff09', left:'center', textStyle:{fontSize:14}},
    tooltip: {trigger:'axis'}, legend: {bottom:0},
    grid: {left:50,right:20,top:40,bottom:50},
    xAxis: {type:'category', data:months, axisLabel:{rotate:45,fontSize:10}},
    yAxis: {type:'value'},
    series: [
      {name:'\u9500\u552e\u989d', type:'line', smooth:true, data:months.map(k=>+(mAgg[k].sales/10000).toFixed(1))},
      {name:'\u6bdb\u5229', type:'line', smooth:true, data:months.map(k=>+(mAgg[k].profit/10000).toFixed(1))}
    ]
  });

  // 品类
  const cRows = filterRows(D.category);
  const cAgg = {};
  cRows.forEach(d => { cAgg[d.product_category] = (cAgg[d.product_category]||0) + (+d.sales||0); });
  const catArr = Object.entries(cAgg).map(([k,v])=>({name:k, val:v})).sort((a,b)=>b.val-a.val).slice(0,10);
  if (!charts.bar) charts.bar = echarts.init(document.getElementById('chart-bar'));
  charts.bar.setOption({
    title: {text:'Top10 \u54c1\u7c7b', left:'center', textStyle:{fontSize:14}},
    tooltip: {trigger:'axis'}, grid: {left:80,right:20,top:40,bottom:30},
    xAxis: {type:'value'},
    yAxis: {type:'category', data:catArr.map(d=>d.name).reverse(), axisLabel:{fontSize:10}},
    series: [{type:'bar', data:catArr.map(d=>+(d.val/10000).toFixed(1)).reverse()}]
  });

  // 区域
  const rRows = filterRows(D.region);
  if (!charts.region) charts.region = echarts.init(document.getElementById('chart-region'));
  charts.region.setOption({
    title: {text:'\u533a\u57df\u9500\u552e\u5bf9\u6bd4', left:'center', textStyle:{fontSize:14}},
    tooltip: {trigger:'axis'}, grid: {left:50,right:20,top:40,bottom:30},
    xAxis: {type:'category', data:rRows.map(d=>d.store_region), axisLabel:{fontSize:10}},
    yAxis: {type:'value'},
    series: [{type:'bar', data:rRows.map(d=>+(d.sales/10000).toFixed(1))}]
  });

  // 支付
  const pRows = filterRows(D.payment);
  const pAgg = {};
  pRows.forEach(d => { pAgg[d.payment_method] = (pAgg[d.payment_method]||0) + (+d.sales||0); });
  if (!charts.pay) charts.pay = echarts.init(document.getElementById('chart-pay'));
  charts.pay.setOption({
    title: {text:'\u652f\u4ed8\u65b9\u5f0f\u5360\u6bd4', left:'center', textStyle:{fontSize:14}},
    tooltip: {trigger:'item'}, legend: {bottom:0, textStyle:{fontSize:10}},
    series: [{type:'pie', radius:['30%','65%'],
      data:Object.entries(pAgg).map(([k,v])=>({name:k, value:+(v/1000).toFixed(0)})),
      label:{formatter:'{d}%', fontSize:10}}]
  });

  // 时段
  const sRows = filterRows(D.period);
  const sAgg = {};
  sRows.forEach(d => { sAgg[d.shopping_period] = (sAgg[d.shopping_period]||0) + (+d.sales||0); });
  if (!charts.period) charts.period = echarts.init(document.getElementById('chart-period'));
  charts.period.setOption({
    title: {text:'\u8d2d\u7269\u65f6\u6bb5\u5206\u5e03', left:'center', textStyle:{fontSize:14}},
    tooltip: {trigger:'item'}, legend: {bottom:0, textStyle:{fontSize:10}},
    series: [{type:'pie', radius:['30%','65%'],
      data:Object.entries(sAgg).map(([k,v])=>({name:k, value:+(v/1000).toFixed(0)})),
      label:{formatter:'{d}%', fontSize:10}}]
  });

  // 结论
  const top3 = catArr.slice(0,3).map(d=>d.name).join('\u3001');
  document.getElementById('conclusions').innerHTML =
    '<li>\u603b\u9500\u552e\u989d \u00a5' + (sales/10000).toFixed(0) + ' \u4e07\uff0c\u6bdb\u5229\u7387 ' + (sales?(profit/sales*100).toFixed(1):0) + '%</li>' +
    '<li>Top3 \u54c1\u7c7b\uff1a' + top3 + '</li>' +
    '<li>\u5171 ' + orders.toLocaleString() + ' \u7b14\u8ba2\u5355</li>' +
    '<li>\u5ba2\u5355\u4ef7 \u00a5' + (orders?(sales/orders).toFixed(1):0) + '</li>';

  // 异常检测
  const alerts = [];
  let prev = null;
  months.forEach(m => {
    const s = mAgg[m].sales;
    if (prev && Math.abs((s-prev)/prev*100) > 15) {
      alerts.push(m + ' \u73af\u6bd4 ' + ((s-prev)/prev*100 >= 0?'+':'') + ((s-prev)/prev*100).toFixed(1) + '%');
    }
    prev = s;
  });
  document.getElementById('alert-text').textContent = alerts.length ? alerts.join('\uff1b') : '\u672c\u671f\u65e0\u663e\u8457\u6ce2\u52a8';
}

document.getElementById('f-year').addEventListener('change', render);
document.getElementById('f-region').addEventListener('change', render);
window.addEventListener('resize', () => Object.values(charts).forEach(c=>c.resize()));
render();
</script>
</body></html>"""

    html = html.replace("__DATA_JSON__", data_json)
    html = html.replace("__YEAR_OPTS__", year_opts)
    html = html.replace("__REGION_OPTS__", region_opts)

    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ report.html 已生成")

if __name__ == "__main__":
    main()
