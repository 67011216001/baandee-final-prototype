
import pandas as pd
from pathlib import Path
from datetime import datetime


COLUMNS = [
    'request_id', 'product_id', 'product_name', 'requested_qty',
    'risk_status', 'status', 'created_at', 'updated_at', 'is_deleted'
]


def get_storage_path(project_path):
    p = Path(project_path) / "data" / "app_state"
    p.mkdir(parents=True, exist_ok=True)
    return p / "reorder_requests.csv"


def init_storage(project_path):
    sf = get_storage_path(project_path)
    if not sf.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(sf, index=False)
    return sf


def create_reorder_request(project_path, product_id, requested_qty, product_name="-", risk_status="UNKNOWN"):
    sf = init_storage(project_path)
    df = pd.read_csv(sf)

    next_num = len(df) + 1
    request_id = f"REQ-{next_num:04d}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_row = {
        'request_id': request_id,
        'product_id': str(product_id),
        'product_name': str(product_name),
        'requested_qty': int(requested_qty),
        'risk_status': str(risk_status),
        'status': 'Draft',
        'created_at': now_str,
        'updated_at': now_str,
        'is_deleted': False
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(sf, index=False)

    return new_row


def get_reorder_requests(project_path, include_deleted=False):
    sf = init_storage(project_path)
    df = pd.read_csv(sf)

    if df.empty:
        return df

    df['is_deleted'] = df['is_deleted'].astype(str).str.lower() == 'true'

    if not include_deleted:
        df = df[df['is_deleted'] == False]

    return df


def update_request_status(project_path, request_id, new_status="Approved"):
    sf = init_storage(project_path)
    df = pd.read_csv(sf)

    if df.empty or request_id not in df['request_id'].values:
        return False

    mask = df['request_id'] == request_id
    df.loc[mask, 'status'] = new_status
    df.loc[mask, 'updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.to_csv(sf, index=False)

    return True


def soft_delete_request(project_path, request_id):
    sf = init_storage(project_path)
    df = pd.read_csv(sf)

    if df.empty or request_id not in df['request_id'].values:
        return False

    mask = df['request_id'] == request_id
    df.loc[mask, 'is_deleted'] = True
    df.loc[mask, 'updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.to_csv(sf, index=False)

    return True
