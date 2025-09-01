import os
import pandas as pd
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.redis_int import RedisInterface


def load_data_from_redis(start_time_str, t_steps=96, batteries=None):    
    import pandas as pd
    from datetime import datetime, timedelta

    redis = RedisInterface(db=1)
    start_time = pd.to_datetime(start_time_str)
    slot_duration = timedelta(minutes=15)
    T = [start_time + i * slot_duration for i in range(t_steps)]

    # Read paths
    pv_paths = redis.read_dir("pv_paths")
    load_paths = redis.read_dir("load_paths")
    battery_paths = redis.read_dir("batteries_updated")

    def extract(path):
        try:
            df = pd.read_csv(path)
            df['time'] = pd.to_datetime(df['Datetime'])
            df = df[df['time'].isin(T)]
            df = df.set_index('time')
            if df.empty:
                return None
            return df['Energy']
        except Exception as e:
            print(f"Error reading {path}: {e}")
            return None

    # Extract PVs
    if not pv_paths:
        pvs = False
    else:
        pvs_data = {dev: extract(path) for dev, path in pv_paths.items()}
        pvs_data = {dev: val for dev, val in pvs_data.items() if val is not None}
        pvs = pvs_data if pvs_data else False

    # Extract Loads
    if not load_paths:
        loads = False
    else:
        load_data = {dev: extract(path) for dev, path in load_paths.items()}
        load_data = {dev: val for dev, val in load_data.items() if val is not None}
        loads = load_data if load_data else False

    # Batteries — if no paths, return False
    if not battery_paths:
        batteries = False
    else:
        batteries = battery_paths  # Assuming no need to extract CSV, only paths

    return pvs, loads, batteries

