-- ============================================================
-- Supermarket BI 星型模型建表 SQL
-- 数据库: supermarket_bi
-- 引擎: InnoDB  字符集: utf8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS supermarket_bi
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE supermarket_bi;

-- ---------- 维度表 ----------

-- 日期维度
CREATE TABLE IF NOT EXISTS dim_date (
  date_id        INT PRIMARY KEY,           -- YYYYMMDD
  full_date      DATE NOT NULL,
  year           INT NOT NULL,
  quarter        INT NOT NULL,
  month          INT NOT NULL,
  month_name     VARCHAR(20),
  day            INT NOT NULL,
  day_of_week    INT NOT NULL,
  day_name       VARCHAR(20),
  is_weekend     TINYINT DEFAULT 0,
  is_holiday     TINYINT DEFAULT 0,
  season         VARCHAR(20),
  INDEX idx_year (year),
  INDEX idx_month (year, month)
) ENGINE=InnoDB;

-- 客户维度
CREATE TABLE IF NOT EXISTS dim_customer (
  customer_id            VARCHAR(20) PRIMARY KEY,
  customer_age           INT,
  customer_gender        VARCHAR(10),
  customer_marital_status VARCHAR(20),
  customer_education     VARCHAR(50),
  customer_occupation    VARCHAR(50),
  customer_income        DECIMAL(12,2),
  household_size         INT,
  number_of_children     INT,
  customer_segment       VARCHAR(30),
  customer_region        VARCHAR(20),
  customer_city          VARCHAR(50),
  customer_area_type     VARCHAR(30),
  urban_rural            VARCHAR(20),
  customer_membership_status VARCHAR(20),
  membership_tier        VARCHAR(20),
  customer_since_year    INT,
  customer_tenure_months INT,
  loyalty_program_member TINYINT DEFAULT 0,
  loyalty_tier           VARCHAR(20),
  customer_visit_frequency VARCHAR(30),
  average_monthly_visits DECIMAL(8,2),
  average_transaction_value DECIMAL(10,2),
  customer_lifetime_value DECIMAL(12,2),
  customer_retention_score DECIMAL(5,2),
  customer_churn_risk    VARCHAR(20),
  customer_engagement_score DECIMAL(5,2),
  INDEX idx_segment (customer_segment),
  INDEX idx_region (customer_region),
  INDEX idx_loyalty (loyalty_tier)
) ENGINE=InnoDB;

-- 商品维度
CREATE TABLE IF NOT EXISTS dim_product (
  product_id          VARCHAR(20) PRIMARY KEY,
  product_name        VARCHAR(200),
  product_category   VARCHAR(50),
  product_subcategory VARCHAR(50),
  product_department  VARCHAR(50),
  brand               VARCHAR(100),
  brand_type          VARCHAR(30),
  product_type        VARCHAR(30),
  product_size        VARCHAR(30),
  unit_of_measure     VARCHAR(20),
  package_quantity    INT,
  package_weight      DECIMAL(10,2),
  product_perishable  TINYINT DEFAULT 0,
  product_status      VARCHAR(20),
  country_of_origin   VARCHAR(50),
  product_segment     VARCHAR(30),
  unit_cost           DECIMAL(10,2),
  regular_price       DECIMAL(10,2),
  selling_price       DECIMAL(10,2),
  wholesale_price     DECIMAL(10,2),
  supplier_price      DECIMAL(10,2),
  INDEX idx_category (product_category),
  INDEX idx_department (product_department),
  INDEX idx_brand (brand)
) ENGINE=InnoDB;

-- 门店维度
CREATE TABLE IF NOT EXISTS dim_store (
  store_id            VARCHAR(20) PRIMARY KEY,
  store_size_sqft     INT,
  store_type          VARCHAR(30),
  store_format        VARCHAR(30),
  store_age_years     INT,
  store_region        VARCHAR(20),
  store_city          VARCHAR(50),
  store_area_type     VARCHAR(30),
  number_of_employees  INT,
  number_of_checkout_counters INT,
  number_of_self_checkout_counters INT,
  parking_spaces      INT,
  daily_customer_capacity INT,
  store_rating        DECIMAL(3,2),
  store_operational_status VARCHAR(20),
  INDEX idx_region (store_region),
  INDEX idx_type (store_type)
) ENGINE=InnoDB;

-- 促销维度
CREATE TABLE IF NOT EXISTS dim_promotion (
  promotion_id        VARCHAR(30) PRIMARY KEY,
  promotion_type      VARCHAR(30),
  promotion_duration_days INT,
  promotion_channel   VARCHAR(50),
  promotion_discount_percent DECIMAL(5,2),
  campaign_id         VARCHAR(30),
  campaign_exposure   INT,
  email_campaign      TINYINT DEFAULT 0,
  sms_campaign        TINYINT DEFAULT 0,
  mobile_app_notification TINYINT DEFAULT 0,
  social_media_exposure INT,
  coupon_used         TINYINT DEFAULT 0,
  loyalty_discount    TINYINT DEFAULT 0,
  seasonal_promotion  TINYINT DEFAULT 0
) ENGINE=InnoDB;

-- ---------- 事实表 ----------

CREATE TABLE IF NOT EXISTS fact_sales (
  transaction_line_id  VARCHAR(30) PRIMARY KEY,
  transaction_id      VARCHAR(30),
  basket_id           VARCHAR(30),
  date_id             INT NOT NULL,
  customer_id         VARCHAR(20),
  store_id            VARCHAR(20),
  product_id          VARCHAR(20),
  promotion_id        VARCHAR(30) DEFAULT 'NONE',
  employee_id         VARCHAR(20),
  supplier_id         VARCHAR(20),
  transaction_time    TIME,
  shopping_hour       INT,
  shopping_period     VARCHAR(20),
  quantity            INT,
  unit_price          DECIMAL(10,2),
  gross_sales         DECIMAL(12,2),
  net_sales           DECIMAL(12,2),
  total_amount        DECIMAL(12,2),
  cost_of_goods_sold  DECIMAL(12,2),
  gross_profit        DECIMAL(12,2),
  profit_margin_percent DECIMAL(5,2),
  discount_amount     DECIMAL(10,2),
  discount_percent    DECIMAL(5,2),
  tax_amount          DECIMAL(10,2),
  payment_method      VARCHAR(30),
  payment_channel     VARCHAR(30),
  loyalty_points_earned DECIMAL(10,2),
  loyalty_points_redeemed DECIMAL(10,2),
  basket_size         INT,
  number_of_items     INT,
  number_of_unique_products INT,
  repeat_purchase     TINYINT DEFAULT 0,
  stock_before_transaction INT,
  quantity_sold       INT,
  stock_after_transaction INT,
  FOREIGN KEY (date_id)    REFERENCES dim_date(date_id),
  FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
  FOREIGN KEY (store_id)    REFERENCES dim_store(store_id),
  FOREIGN KEY (product_id)  REFERENCES dim_product(product_id),
  FOREIGN KEY (promotion_id) REFERENCES dim_promotion(promotion_id),
  INDEX idx_date (date_id),
  INDEX idx_customer (customer_id),
  INDEX idx_store (store_id),
  INDEX idx_product (product_id),
  INDEX idx_promo (promotion_id)
) ENGINE=InnoDB;
