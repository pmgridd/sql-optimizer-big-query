input_samples = [
    """SELECT
  d.d_year,
  ROUND(SUM(cs.cs_net_profit) / 1e6, 2) AS profit_millions
FROM
  `gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.catalog_sales` cs
JOIN
  `gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.date_dim` d
ON
  cs.cs_sold_date_sk = d.d_date_sk
GROUP BY
  d.d_year
ORDER BY
  d.d_year;""",
    """SELECT
  cr.cr_catalog_page_sk AS page_sk,
  COUNT(cr.cr_order_number) AS return_count
FROM
  `gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.catalog_returns` cr
WHERE
  cr.cr_catalog_page_sk IS NOT NULL
GROUP BY
  cr.cr_catalog_page_sk
HAVING
  COUNT(cr.cr_order_number) > 10
ORDER BY
  return_count DESC;""",
    """SELECT
  cp.cp_catalog_page_id,
  COUNT(DISTINCT cs.cs_bill_customer_sk) AS unique_customers
FROM
  `gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.catalog_sales` cs
JOIN
  `gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.catalog_page` cp
ON
  cs.cs_catalog_page_sk = cp.cp_catalog_page_sk
GROUP BY
  cp.cp_catalog_page_id
ORDER BY
  unique_customers DESC
LIMIT 10;""",
    """SELECT
  p.p_promo_name,
  COUNT(DISTINCT cs.cs_order_number) AS orders
FROM
  `gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.catalog_sales` cs
JOIN
  `gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.promotion` p
ON
  cs.cs_promo_sk = p.p_promo_sk
WHERE
  p.p_cost > 10
GROUP BY
  p.p_promo_name
ORDER BY
  orders DESC;""",
    """SELECT
  d.d_date,
  sr.sr_net_loss
FROM
  `gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.store_returns` sr
JOIN
  `gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.date_dim` d
  ON CAST(sr.sr_returned_date_sk AS STRING) = CAST(d.d_date_sk AS STRING)
WHERE
  sr.sr_net_loss > 0
LIMIT 100;""",
]
