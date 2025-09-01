# result_writer.py
from pyomo.environ import value
from shared.redis_int import RedisInterface
import pandas as pd
from datetime import datetime

def make_json_serializable(data):
    if isinstance(data, dict):
        return {make_json_serializable(k): make_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_json_serializable(i) for i in data]
    elif isinstance(data, (pd.Timestamp, datetime)):
        return data.isoformat()
    else:
        return data



def write_results_to_redis(model):
    redis = RedisInterface(db=1)
    records = []
 
    # Ensure time steps are sorted
    sorted_time_steps = sorted(model.T)

    # Select only the first 3 time steps
    limited_time_steps = sorted_time_steps[:3]

    for t in limited_time_steps:
  
        row = {
            "TimeStep": t,
            "Bid_Price": value(model.bid_price[t]),
            "Offer_Price": value(model.offer_price[t]),
            "Total_Load_Met": sum(value(model.load_met[l, t]) for l in model.L),
        }

        # Battery-level results
        for b in model.B:
            row.update({
                f"{b}_Charge": value(model.charge[b, t]),
                f"{b}_Discharge": value(model.discharge[b, t]),
                f"{b}_SoC": value(model.soc[b, t]),
                f"{b}_Bid": value(model.bid_qty[b, t]),
                f"{b}_Offer": value(model.offer_qty[b, t]),
                f"{b}_To_Grid": value(model.bat_to_grid[b, t]),
                f"Grid_To_{b}": value(model.grid_to_bat[b, t]),
            })

        # PV-level results
        for p in model.PV:
            row.update({
                f"{p}_To_Grid": value(model.pv_to_grid[p, t])
            })
            for b in model.B:
                row[f"{p}_To_{b}"] = value(model.pv_to_bat[p, b, t])
            for l in model.L:
                row[f"{p}_To_{l}"] = value(model.pv_to_load[p, l, t])

        # Load-level results
        for l in model.L:
            row.update({
                f"{l}_Met": value(model.load_met[l, t]),
                f"Grid_To_{l}": value(model.grid_to_load[l, t]),
            })
            for b in model.B:
                row[f"{b}_To_{l}"] = value(model.bat_to_load[b, l, t])

        records.append(row)    

    serializable_records = make_json_serializable(records)
    redis.write_json("optimization_result", serializable_records)
    print("Optimization results posted to Redis.")
