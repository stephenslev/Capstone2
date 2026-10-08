from pathlib import Path
import sqlite3

DB_PATH = Path("data/database.sqlite")
REGIONS = ("North", "South", "East", "West")
MONTHS = [f"2026-{month:02d}" for month in range(1, 13)]
BASE_REVENUE = (
    120000, 124000, 129000, 134000, 139000, 145000,
    151000, 158000, 165000, 173000, 181000, 190000,
)
REGION_FACTORS = {
    "North": 1.10,
    "South": 0.90,
    "East": 1.00,
    "West": 1.20,
}
DEPARTMENT_BASES = {
    "Engineering": 82.0,
    "Finance": 79.0,
    "Operations": 74.0,
    "Sales": 72.0,
    "Customer Success": 76.0,
    "Human Resources": 81.0,
}
POLICY_PROFILES = {
    "Hybrid Work Policy": (70.0, 5.0, 1.0),
    "Learning and Development Policy": (54.0, 7.0, 2.0),
    "Manager Feedback Policy": (62.0, 6.0, 1.5),
    "Wellbeing and Time-Off Policy": (76.0, 4.0, 1.2),
}

SCHEMA_SQL = """
CREATE TABLE monthly_revenue (
    month TEXT NOT NULL,
    region TEXT NOT NULL,
    revenue REAL NOT NULL,
    target_revenue REAL NOT NULL,
    PRIMARY KEY (month, region)
);

CREATE TABLE customer_metrics (
    month TEXT NOT NULL,
    region TEXT NOT NULL,
    active_customers INTEGER NOT NULL,
    new_customers INTEGER NOT NULL,
    churned_customers INTEGER NOT NULL,
    churn_rate REAL NOT NULL,
    nps_score REAL NOT NULL,
    PRIMARY KEY (month, region)
);

CREATE TABLE regional_performance (
    quarter TEXT NOT NULL,
    region TEXT NOT NULL,
    revenue REAL NOT NULL,
    target_revenue REAL NOT NULL,
    new_customers INTEGER NOT NULL,
    renewal_rate REAL NOT NULL,
    win_rate REAL NOT NULL,
    PRIMARY KEY (quarter, region)
);

CREATE TABLE employee_satisfaction (
    period TEXT NOT NULL,
    department TEXT NOT NULL,
    satisfaction_score REAL NOT NULL,
    industry_benchmark REAL NOT NULL,
    response_count INTEGER NOT NULL,
    PRIMARY KEY (period, department)
);

CREATE TABLE employee_policy_metrics (
    period TEXT NOT NULL,
    policy_name TEXT NOT NULL,
    adoption_rate REAL NOT NULL,
    employee_satisfaction_score REAL NOT NULL,
    industry_benchmark REAL NOT NULL,
    PRIMARY KEY (period, policy_name)
);

CREATE TABLE sales_performance (
    month TEXT NOT NULL,
    region TEXT NOT NULL,
    qualified_opportunities INTEGER NOT NULL,
    closed_won INTEGER NOT NULL,
    win_rate REAL NOT NULL,
    sales_revenue REAL NOT NULL,
    average_deal_size REAL NOT NULL,
    PRIMARY KEY (month, region)
);

CREATE TABLE customer_success_metrics (
    month TEXT NOT NULL,
    region TEXT NOT NULL,
    active_accounts INTEGER NOT NULL,
    at_risk_accounts INTEGER NOT NULL,
    renewal_rate REAL NOT NULL,
    adoption_rate REAL NOT NULL,
    avg_resolution_hours REAL NOT NULL,
    PRIMARY KEY (month, region)
);

CREATE TABLE sales (
    id INTEGER PRIMARY KEY,
    region TEXT NOT NULL,
    product TEXT NOT NULL,
    revenue REAL NOT NULL,
    date TEXT NOT NULL,
    units_sold INTEGER NOT NULL,
    qualified_opportunities INTEGER NOT NULL,
    closed_won INTEGER NOT NULL,
    win_rate REAL NOT NULL,
    renewal_rate REAL NOT NULL,
    adoption_rate REAL NOT NULL,
    at_risk_accounts INTEGER NOT NULL,
    avg_resolution_hours REAL NOT NULL
);

CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT NOT NULL,
    region TEXT NOT NULL,
    churn_date TEXT,
    satisfaction_score REAL NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    department TEXT NOT NULL,
    satisfaction_score REAL NOT NULL,
    tenure_years REAL NOT NULL,
    period TEXT NOT NULL,
    industry_benchmark REAL NOT NULL
);

CREATE VIEW monthly_revenue_trend AS
SELECT
    month,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(target_revenue), 2) AS total_target_revenue,
    ROUND(
        100.0 * SUM(revenue) / NULLIF(SUM(target_revenue), 0),
        2
    ) AS attainment_rate
FROM monthly_revenue
GROUP BY month
ORDER BY month;

CREATE VIEW customer_churn_summary AS
SELECT
    month,
    SUM(active_customers) AS active_customers,
    SUM(churned_customers) AS churned_customers,
    ROUND(
        100.0 * SUM(churned_customers)
        / NULLIF(SUM(active_customers), 0),
        2
    ) AS churn_rate
FROM customer_metrics
GROUP BY month
ORDER BY month;

CREATE VIEW q4_regional_comparison AS
SELECT
    region,
    revenue,
    target_revenue,
    ROUND(
        100.0 * revenue / NULLIF(target_revenue, 0),
        2
    ) AS attainment_rate,
    new_customers,
    renewal_rate,
    win_rate
FROM regional_performance
WHERE quarter = '2026-Q4'
ORDER BY revenue DESC;
"""


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()

    revenue_rows = []
    customer_metric_rows = []
    regional_lookup = {}
    revenue_lookup = {}
    customer_lookup = {}
    sales_lookup = {}
    success_lookup = {}
    sales_performance_rows = []
    customer_success_rows = []

    for month_number, month in enumerate(MONTHS, start=1):
        quarter_number = ((month_number - 1) // 3) + 1

        for region_index, region in enumerate(REGIONS):
            factor = REGION_FACTORS[region]
            revenue = round(
                BASE_REVENUE[month_number - 1] * factor,
                2,
            )
            target_revenue = round(revenue * 1.04, 2)

            revenue_rows.append(
                (month, region, revenue, target_revenue)
            )
            revenue_lookup[(month, region)] = (
                revenue,
                target_revenue,
            )

            active_customers = (
                300 + region_index * 45 + month_number * 7
            )
            new_customers = 14 + region_index * 3 + month_number
            churned_customers = 3 + (
                (month_number + region_index) % 4
            )
            churn_rate = round(
                100.0 * churned_customers / active_customers,
                2,
            )
            nps_score = round(
                42
                + region_index * 3
                + month_number * 0.6
                - churned_customers * 0.8,
                1,
            )

            customer_metric_rows.append(
                (
                    month,
                    region,
                    active_customers,
                    new_customers,
                    churned_customers,
                    churn_rate,
                    nps_score,
                )
            )
            customer_lookup[(month, region)] = (
                active_customers,
                new_customers,
                churned_customers,
                churn_rate,
                nps_score,
            )

            qualified_opportunities = (
                42 + region_index * 5 + month_number * 2
            )
            closed_won = 12 + region_index * 2 + month_number
            win_rate = round(
                100.0 * closed_won / qualified_opportunities,
                2,
            )
            sales_revenue = round(revenue * 0.90, 2)
            average_deal_size = round(
                sales_revenue / closed_won,
                2,
            )

            sales_performance_rows.append(
                (
                    month,
                    region,
                    qualified_opportunities,
                    closed_won,
                    win_rate,
                    sales_revenue,
                    average_deal_size,
                )
            )
            sales_lookup[(month, region)] = (
                qualified_opportunities,
                closed_won,
                win_rate,
                sales_revenue,
                average_deal_size,
            )

            at_risk_accounts = max(
                5,
                round(
                    active_customers
                    * max(0.01, 0.045 - month_number * 0.001)
                ),
            )
            renewal_rate = round(
                100.0 - churn_rate * 1.8,
                2,
            )
            adoption_rate = round(
                68 + region_index * 2 + month_number * 0.9,
                2,
            )
            avg_resolution_hours = round(
                22 - month_number * 0.35 + region_index * 0.5,
                2,
            )

            customer_success_rows.append(
                (
                    month,
                    region,
                    active_customers,
                    at_risk_accounts,
                    renewal_rate,
                    adoption_rate,
                    avg_resolution_hours,
                )
            )
            success_lookup[(month, region)] = (
                active_customers,
                at_risk_accounts,
                renewal_rate,
                adoption_rate,
                avg_resolution_hours,
            )

            regional_lookup.setdefault(
                f"2026-Q{quarter_number}",
                {},
            ).setdefault(region, []).append(month)

    regional_rows = []

    for quarter, regions in regional_lookup.items():
        for region, quarter_months in regions.items():
            revenue = round(
                sum(
                    revenue_lookup[(month, region)][0]
                    for month in quarter_months
                ),
                2,
            )
            target_revenue = round(
                sum(
                    revenue_lookup[(month, region)][1]
                    for month in quarter_months
                ),
                2,
            )
            new_customers = sum(
                customer_lookup[(month, region)][1]
                for month in quarter_months
            )
            renewal_rate = round(
                sum(
                    success_lookup[(month, region)][2]
                    for month in quarter_months
                ) / len(quarter_months),
                2,
            )
            win_rate = round(
                sum(
                    sales_lookup[(month, region)][2]
                    for month in quarter_months
                ) / len(quarter_months),
                2,
            )

            regional_rows.append(
                (
                    quarter,
                    region,
                    revenue,
                    target_revenue,
                    new_customers,
                    renewal_rate,
                    win_rate,
                )
            )

    quarter_adjustments = (-2.0, 0.0, 1.0, 2.0)
    employee_satisfaction_rows = []
    employee_rows = []
    employee_id = 1

    for quarter_number in range(1, 5):
        period = f"2026-Q{quarter_number}"

        for department, base_score in DEPARTMENT_BASES.items():
            satisfaction_score = round(
                base_score + quarter_adjustments[quarter_number - 1],
                1,
            )
            benchmark = 76.0
            response_count = 18 + quarter_number * 3
            tenure_years = round(
                1.5 + ((employee_id * 7) % 60) / 10,
                1,
            )

            employee_satisfaction_rows.append(
                (
                    period,
                    department,
                    satisfaction_score,
                    benchmark,
                    response_count,
                )
            )
            employee_rows.append(
                (
                    employee_id,
                    department,
                    satisfaction_score,
                    tenure_years,
                    period,
                    benchmark,
                )
            )
            employee_id += 1

    policy_rows = []

    for quarter_number in range(1, 5):
        period = f"2026-Q{quarter_number}"

        for policy_name, profile in POLICY_PROFILES.items():
            adoption_base, adoption_step, satisfaction_effect = profile
            adoption_rate = min(
                98.0,
                adoption_base + adoption_step * quarter_number,
            )
            satisfaction_score = round(
                67.0
                + satisfaction_effect
                + adoption_rate * 0.10
                + quarter_adjustments[quarter_number - 1],
                1,
            )

            policy_rows.append(
                (
                    period,
                    policy_name,
                    adoption_rate,
                    satisfaction_score,
                    76.0,
                )
            )

    sales_rows = []

    for sale_id, (month, region) in enumerate(
        revenue_lookup.keys(),
        start=1,
    ):
        revenue, _ = revenue_lookup[(month, region)]
        qualified, closed_won, win_rate, sales_revenue, _ = (
            sales_lookup[(month, region)]
        )
        _, at_risk, renewal_rate, adoption_rate, resolution_hours = (
            success_lookup[(month, region)]
        )
        product = (
            "Platform"
            if region in ("North", "East")
            else "Advisory"
        )
        units_sold = max(1, round(sales_revenue / 2500))

        sales_rows.append(
            (
                sale_id,
                region,
                product,
                sales_revenue,
                f"{month}-28",
                units_sold,
                qualified,
                closed_won,
                win_rate,
                renewal_rate,
                adoption_rate,
                at_risk,
                resolution_hours,
            )
        )

    customer_rows = []
    industries = ("Healthcare", "Financial Services", "Technology", "Retail")

    for customer_id in range(1, 121):
        region = REGIONS[(customer_id - 1) % len(REGIONS)]
        industry = industries[(customer_id - 1) % len(industries)]
        is_churned = customer_id % 11 == 0
        churn_date = (
            f"2026-{((customer_id - 1) % 12) + 1:02d}-15"
            if is_churned
            else None
        )
        satisfaction_score = round(
            62 + ((customer_id * 7) % 31),
            1,
        )
        status = "Churned" if is_churned else "Active"

        customer_rows.append(
            (
                customer_id,
                f"Customer {customer_id:03d}",
                industry,
                region,
                churn_date,
                satisfaction_score,
                status,
            )
        )

    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(SCHEMA_SQL)

        connection.executemany(
            """
            INSERT INTO monthly_revenue
            (month, region, revenue, target_revenue)
            VALUES (?, ?, ?, ?)
            """,
            revenue_rows,
        )
        connection.executemany(
            """
            INSERT INTO customer_metrics
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            customer_metric_rows,
        )
        connection.executemany(
            """
            INSERT INTO regional_performance
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            regional_rows,
        )
        connection.executemany(
            """
            INSERT INTO employee_satisfaction
            VALUES (?, ?, ?, ?, ?)
            """,
            employee_satisfaction_rows,
        )
        connection.executemany(
            """
            INSERT INTO employee_policy_metrics
            VALUES (?, ?, ?, ?, ?)
            """,
            policy_rows,
        )
        connection.executemany(
            """
            INSERT INTO sales_performance
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            sales_performance_rows,
        )
        connection.executemany(
            """
            INSERT INTO customer_success_metrics
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            customer_success_rows,
        )
        connection.executemany(
            """
            INSERT INTO sales
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            sales_rows,
        )
        connection.executemany(
            """
            INSERT INTO customers
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            customer_rows,
        )
        connection.executemany(
            """
            INSERT INTO employees
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            employee_rows,
        )

        connection.commit()

        tables = (
            "monthly_revenue",
            "customer_metrics",
            "regional_performance",
            "employee_satisfaction",
            "employee_policy_metrics",
            "sales_performance",
            "customer_success_metrics",
            "sales",
            "customers",
            "employees",
        )

        print(f"Created {DB_PATH}")

        for table in tables:
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            print(f"{table}: {count} rows")


if __name__ == "__main__":
    main()
