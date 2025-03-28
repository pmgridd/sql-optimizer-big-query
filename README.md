# big-query-agent-optimizer

## Development Setup

* Install a local Python version (see `.python-version` 3.11.10)
  e.g. with pyenv: `pyenv install 3.11.10`, `pyenv global 3.11.10`
* Run `make dev-setup`

## Code quality

`make dev-setup` command defined in the `Makefile` is installing several automatic code quality
tools, configuration and definitions for which could be found in the `.pre-commit-config.yaml`
file.

Pre-commit hooks will be executed automatically on any invocation of the `git commit` command or
could manually be run via `make pre-commit`.

## Testing

Unit tests for the source code are located under `tests/src`, run

`make unit-tests`

in order to execute them with pytest.

## Dependency management

This project uses Pipenv for dependency management. To reinstall all dependencies
listed in the `Pipfile` execute:

```bash
pipenv install --dev
```

Note, that "[packages]" section contains the dependencies needed for the actual runtime
execution
of the code scheduling the pipelines or executing at pipeline runtime environment

"[dev-packages]" section contains the rest of the dependencies necessary to work with the
repository automation: code quality tools, unit test libraries, etc.

After installing or updating packages, please don't forget to commit the updated
lock file (`Pipfile.lock`) to the repository

```bash
pipenv lock
git add Pipfile.lock
```

## Queries to test

### 1. Not Optimized query 1 (subqueries instead of window function)

```sql
SELECT
    c.c_customer_sk,
    s.cs_sold_date_sk,
    s.cs_net_paid,
    (SELECT SUM(cs_net_paid)
     FROM `gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.catalog_sales` AS inner_s
     WHERE inner_s.cs_ship_customer_sk = c.c_customer_sk AND inner_s.cs_sold_date_sk <= s.cs_sold_date_sk) AS cumulative_spending,
    (SELECT MAX(cs_sold_date_sk)
     FROM `gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.catalog_sales` AS lag_s
     WHERE lag_s.cs_ship_customer_sk = c.c_customer_sk AND lag_s.cs_sold_date_sk < s.cs_sold_date_sk) AS prev_purchase_date
FROM
    `gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.customer` AS c
INNER JOIN
    `gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.catalog_sales` AS s
ON
    c.c_customer_sk = s.cs_ship_customer_sk
LIMIT 1
```

### 2. Not Optimized query 2 (cross join)
```sql
select * from gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.customer c CROSS join gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.catalog_sales s WHERE c.c_customer_sk = s.cs_ship_customer_sk limit 1
```

### 3. Not Optimized query 3 (cross join)
```sql
select * from gd-gcp-rnd-analytical-platform.adp_rnd_dwh_performance.customer limit 1
```
