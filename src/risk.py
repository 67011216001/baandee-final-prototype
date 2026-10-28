
import pandas as pd
import numpy as np
from pathlib import Path


def calculate_stock_risk(project_path):
    cleaned_path = Path(project_path) / "data" / "cleaned"
    raw_path = Path(project_path) / "data" / "raw"

    joined_file = cleaned_path / "joined_products_supplier.csv"
    orders_file = cleaned_path / "cleaned_orders.csv" if (cleaned_path / "cleaned_orders.csv").exists() else raw_path / "orders.csv"
    lines_file = cleaned_path / "cleaned_order_lines.csv" if (cleaned_path / "cleaned_order_lines.csv").exists() else raw_path / "order_lines.csv"
    inv_file = cleaned_path / "cleaned_inventory_snapshot.csv" if (cleaned_path / "cleaned_inventory_snapshot.csv").exists() else raw_path / "inventory_snapshot.csv"

    df_joined = pd.read_csv(joined_file)
    df_orders = pd.read_csv(orders_file)
    df_lines = pd.read_csv(lines_file)
    df_inv = pd.read_csv(inv_file)

    snapshot_date = pd.to_datetime("2026-07-31")
    start_30d = snapshot_date - pd.Timedelta(days=30)

    df_orders['order_date_dt'] = pd.to_datetime(df_orders['order_date'], errors='coerce')
    recent_orders = df_orders[(df_orders['order_date_dt'] >= start_30d) & (df_orders['order_date_dt'] <= snapshot_date)]
    recent_lines = df_lines[df_lines['order_id'].isin(recent_orders['order_id'])]

    sales_30d = recent_lines.groupby('product_id')['quantity'].sum().reset_index()
    sales_30d.rename(columns={'quantity': 'sales_30d_qty'}, inplace=True)

    def format_pid(val):
        try:
            return f"SKU-{int(float(val)):04d}"
        except:
            return str(val)

    df_inv['product_id'] = df_inv['product_id'].map(format_pid)

    df_risk = pd.merge(df_joined, df_inv[['product_id', 'available_qty']], on='product_id', how='left')
    df_risk = pd.merge(df_risk, sales_30d, on='product_id', how='left')
    df_risk['sales_30d_qty'] = df_risk['sales_30d_qty'].fillna(0)
    df_risk['daily_sales_rate'] = df_risk['sales_30d_qty'] / 30.0

    def evaluate_risk(row):
        lead_time = row['lead_time_days']
        stock = row['available_qty']
        daily_rate = row['daily_sales_rate']

        if pd.isna(lead_time) or lead_time <= 0 or pd.isna(stock) or stock < 0:
            return 'HUMAN_REVIEW_NEEDED'
        if stock == 0:
            return 'CRITICAL_RISK'
        if daily_rate == 0:
            return 'NORMAL'

        days_of_cover = stock / daily_rate

        if days_of_cover < lead_time:
            return 'CRITICAL_RISK'
        elif days_of_cover <= (lead_time + 7):
            return 'WARNING_RISK'
        else:
            return 'NORMAL'

    df_risk['risk_status'] = df_risk.apply(evaluate_risk, axis=1)
    df_risk['days_of_cover'] = np.where(
        df_risk['daily_sales_rate'] > 0,
        (df_risk['available_qty'] / df_risk['daily_sales_rate']).round(1),
        np.inf
    )

    output_risk_file = cleaned_path / "stock_risk_summary.csv"
    df_risk.to_csv(output_risk_file, index=False)

    return df_risk
