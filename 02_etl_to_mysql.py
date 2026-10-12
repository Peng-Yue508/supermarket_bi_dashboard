# -*- coding: utf-8 -*-
"""
ETL: supermarket_large_dataset.csv → MySQL 星型模型
用法: 先在 config.py 里填好 MySQL root 密码, 然后 python etl_to_mysql.py
"""
import pandas as pd
import pymysql
import numpy as np
import config

CSV_PATH = r"D:\2026年求职作品集相关文件\原始数据集-解压缩得到\supermarket_large_dataset.csv"

# ---------- 维度列映射 (CSV列名 → 表里的列) ----------
DIM_DATE = ["transaction_date","year","quarter","month","month_name",
            "day_of_week","day_name","is_weekend","is_holiday","season"]
DIM_CUST = ["customer_id","customer_age","customer_gender","customer_marital_status",
            "customer_education","customer_occupation","customer_income","household_size",
            "number_of_children","customer_segment","customer_region","customer_city",
            "customer_area_type","urban_rural","customer_membership_status","membership_tier",
            "customer_since_year","customer_tenure_months","loyalty_program_member",
            "loyalty_tier","customer_visit_frequency","average_monthly_visits",
            "average_transaction_value","customer_lifetime_value","customer_retention_score",
            "customer_churn_risk","customer_engagement_score"]
DIM_PROD = ["product_id","product_name","product_category","product_subcategory",
            "product_department","brand","brand_type","product_type","product_size",
            "unit_of_measure","package_quantity","package_weight","product_perishable",
            "product_status","country_of_origin","product_segment","unit_cost",
            "regular_price","selling_price","wholesale_price","supplier_price"]
DIM_STORE = ["store_id","store_size_sqft","store_type","store_format","store_age_years",
             "store_region","store_city","store_area_type","number_of_employees",
             "number_of_checkout_counters","number_of_self_checkout_counters",
             "parking_spaces","daily_customer_capacity","store_rating","store_operational_status"]
DIM_PROMO = ["promotion_id","promotion_type","promotion_duration_days","promotion_channel",
             "promotion_discount_percent","campaign_id","campaign_exposure",
             "email_campaign","sms_campaign","mobile_app_notification",
             "social_media_exposure","coupon_used","loyalty_discount","seasonal_promotion"]

FACT_COLS = ["transaction_line_id","transaction_id","basket_id","customer_id","store_id",
             "product_id","promotion_id","employee_id","supplier_id","transaction_time",
             "shopping_hour","shopping_period","quantity","unit_price","gross_sales",
             "net_sales","total_amount","cost_of_goods_sold","gross_profit",
             "profit_margin_percent","discount_amount","discount_percent","tax_amount",
             "payment_method","payment_channel","loyalty_points_earned",
             "loyalty_points_redeemed","basket_size","number_of_items",
             "number_of_unique_products","repeat_purchase","stock_before_transaction",
             "quantity_sold","stock_after_transaction"]

def get_conn():
    return pymysql.connect(host="localhost", user="root", password=config.MYSQL_PWD,
                           database="supermarket_bi", charset="utf8mb4")

def load_dim(conn, df, table, id_col):
    """去重后插入维度表, 跳过已存在的 id"""
    df_d = df.drop_duplicates(subset=[id_col]).dropna(subset=[id_col])
    df_d = df_d.astype(object).where(pd.notnull(df_d), None)  # NaN → None
    cols = list(df_d.columns)
    placeholders = ",".join(["%s"] * len(cols))
    sql = f"INSERT IGNORE INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
    rows = [tuple(r) for r in df_d[cols].itertuples(index=False, name=None)]
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()
    print(f"  {table}: {len(df_d)} 条")

def main():
    print("读取 CSV (分块)...")
    chunks = pd.read_csv(CSV_PATH, chunksize=50000, low_memory=False)
    all_fact = []
    date_seen = set()
    dim_dfs = {"cust": [], "prod": [], "store": [], "promo": []}

    for i, chunk in enumerate(chunks):
        print(f"  块 {i+1}: {len(chunk)} 行")
        # 自动过滤: 只取 CSV 里实际存在的列
        avail = set(chunk.columns)
        def pick(cols): return [c for c in cols if c in avail]

        # 日期维度: 只取不重复的日期
        dt = pd.to_datetime(chunk["transaction_date"])
        chunk["date_id"] = dt.dt.strftime("%Y%m%d").astype(int)
        chunk["day"] = dt.dt.day  # CSV 里没有 day 列, 从日期提取
        dim_date_cols = ["date_id"] + pick(DIM_DATE) + ["day"]
        dim_date = chunk[dim_date_cols].copy()
        dim_date["full_date"] = pd.to_datetime(dim_date["transaction_date"])
        dim_date = dim_date.drop(columns=["transaction_date"])
        # 过滤已见日期
        new_mask = ~dim_date["date_id"].isin(date_seen)
        if new_mask.any():
            new_dates = dim_date[new_mask].astype(object).where(pd.notnull(dim_date[new_mask]), None)
            with get_conn() as conn:
                cols = list(new_dates.columns)
                ph = ",".join(["%s"] * len(cols))
                sql = f"INSERT IGNORE INTO dim_date ({','.join(cols)}) VALUES ({ph})"
                with conn.cursor() as cur:
                    cur.executemany(sql, [tuple(r) for r in new_dates[cols].itertuples(index=False, name=None)])
                conn.commit()
            date_seen.update(new_dates["date_id"].tolist())
            print(f"  dim_date: +{len(new_dates)} 天 (累计 {len(date_seen)})")

        dim_dfs["cust"].append(chunk[pick(DIM_CUST)])
        dim_dfs["prod"].append(chunk[pick(DIM_PROD)])
        dim_dfs["store"].append(chunk[pick(DIM_STORE)])
        dim_dfs["promo"].append(chunk[pick(DIM_PROMO)])
        all_fact.append(chunk[["date_id"] + pick(FACT_COLS)])

    print("\n写入维度表...")
    with get_conn() as conn:
        load_dim(conn, pd.concat(dim_dfs["cust"]),  "dim_customer", "customer_id")
        load_dim(conn, pd.concat(dim_dfs["prod"]),  "dim_product", "product_id")
        load_dim(conn, pd.concat(dim_dfs["store"]), "dim_store",   "store_id")
        load_dim(conn, pd.concat(dim_dfs["promo"]), "dim_promotion","promotion_id")
        # 补一条 NONE 默认记录, 供无促销的事实行引用
        with conn.cursor() as cur:
            cur.execute("INSERT IGNORE INTO dim_promotion (promotion_id) VALUES ('NONE')")
        conn.commit()

    print("\n写入事实表...")
    fact = pd.concat(all_fact, ignore_index=True)
    fact["promotion_id"] = fact["promotion_id"].fillna("NONE")
    fact = fact.astype(object).where(pd.notnull(fact), None)
    cols = list(fact.columns)
    ph = ",".join(["%s"] * len(cols))
    sql = f"INSERT IGNORE INTO fact_sales ({','.join(cols)}) VALUES ({ph})"
    # 分批插入
    batch = 5000
    with get_conn() as conn:
        with conn.cursor() as cur:
            for s in range(0, len(fact), batch):
                batch_rows = [tuple(r) for r in fact.iloc[s:s+batch][cols].itertuples(index=False, name=None)]
                cur.executemany(sql, batch_rows)
                conn.commit()
                print(f"  fact_sales: {min(s+batch, len(fact))}/{len(fact)}")
    print("\n✅ ETL 完成!")

if __name__ == "__main__":
    main()
