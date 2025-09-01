# build_model.py
from pyomo.environ import *




def create_model(pvs, loads, batteries, bid_prices, offer_prices):


    model = ConcreteModel()
    model.T = Set(initialize=pvs[list(pvs.keys())[0]].index.tolist(), ordered=True)
    model.B = Set(initialize=list(batteries.keys()))

    model.PV = Set(initialize=pvs.keys())
    model.L = Set(initialize=loads.keys())

    time_list = list(model.T.data())  # Ensure ordering is preserved

    model.bid_price = Param(model.T, initialize={t: float(bid_prices[i]) for i, t in enumerate(time_list)})
    model.offer_price = Param(model.T, initialize={t: float(offer_prices[i]) for i, t in enumerate(time_list)})



    model.capacity = Param(model.B, initialize={b: batteries[b]["capacity"] for b in model.B})
    model.initial_soc = Param(model.B, initialize={b: batteries[b]["SOC"] for b in model.B})
    model.charge_eff = Param(model.B, initialize={b: batteries[b]["charge_eff"] for b in model.B})
    model.discharge_eff = Param(model.B, initialize={b: batteries[b]["discharge_eff"] for b in model.B})
    model.max_c = Param(model.B, initialize={b: batteries[b]["max_c"] for b in model.B})
    model.max_d = Param(model.B, initialize={b: batteries[b]["max_d"] for b in model.B})

    model.penalty_sell = Param(initialize=0.01)
    model.penalty_buy = Param(initialize=0.01)

    model.pv_to_load = Var(model.PV, model.L, model.T, bounds=(0, None))
    model.pv_to_bat = Var(model.PV, model.B, model.T, bounds=(0, None))
    model.pv_to_grid = Var(model.PV, model.T, bounds=(0, None))
    model.bat_to_load = Var(model.B, model.L, model.T, bounds=(0, None))
    model.bat_to_grid = Var(model.B, model.T, bounds=(0, None))
    model.grid_to_load = Var(model.L, model.T, bounds=(0, None))
    model.grid_to_bat = Var(model.B, model.T, bounds=(0, None))

    model.charge = Var(model.B, model.T)
    model.discharge = Var(model.B, model.T)
    model.soc = Var(model.B, model.T, bounds=lambda m, b, t: (0, m.capacity[b]))
    model.bid_qty = Var(model.B, model.T, bounds=(0, None))
    model.offer_qty = Var(model.B, model.T, bounds=(0, None))
    model.load_met = Var(model.L, model.T, bounds=(0, None))

    model.obj = Objective(expr=sum(
        sum(model.bat_to_grid[b, t] for b in model.B) * model.offer_price[t] +
        sum(model.pv_to_grid[p, t] for p in model.PV) * model.offer_price[t] -
        sum(model.grid_to_bat[b, t] for b in model.B) * model.bid_price[t] -
        sum(model.grid_to_load[l, t] for l in model.L) * model.bid_price[t] -
        sum(model.bat_to_grid[b, t] for b in model.B) * model.penalty_sell -
        sum(model.grid_to_bat[b, t] for b in model.B) * model.penalty_buy
        for t in model.T), sense=maximize)

    model.constraints = ConstraintList()
    time_list = list(model.T.data())

    for i, t in enumerate(time_list):
        for b in model.B:
            # State of charge transition
            if i == 0:
                model.constraints.add(
                    model.soc[b, t] == model.initial_soc[b]
                    + model.charge_eff[b] * model.charge[b, t]
                    - model.discharge[b, t] / model.discharge_eff[b]
                )
            else:
                prev_t = time_list[i - 1]
                model.constraints.add(
                    model.soc[b, t] == model.soc[b, prev_t]
                    + model.charge_eff[b] * model.charge[b, t]
                    - model.discharge[b, t] / model.discharge_eff[b]
                )

            # Charging/discharging balance
            model.constraints.add(
                model.charge[b, t] == sum(model.pv_to_bat[p, b, t] for p in model.PV) + model.grid_to_bat[b, t]
            )
            model.constraints.add(
                model.discharge[b, t] == sum(model.bat_to_load[b, l, t] for l in model.L) + model.bat_to_grid[b, t]
            )

            # Bidding and offering quantities
            model.constraints.add(model.bid_qty[b, t] == model.grid_to_bat[b, t])
            model.constraints.add(model.offer_qty[b, t] == model.bat_to_grid[b, t])

        # Load constraints
        for l in model.L:
            model.constraints.add(
                sum(model.pv_to_load[p, l, t] for p in model.PV)
                + sum(model.bat_to_load[b, l, t] for b in model.B)
                + model.grid_to_load[l, t] == model.load_met[l, t]
            )
            model.constraints.add(model.load_met[l, t] <= float(loads[l][t]))

        # PV constraints
        for p in model.PV:
            model.constraints.add(
                sum(model.pv_to_load[p, l, t] for l in model.L)
                + sum(model.pv_to_bat[p, b, t] for b in model.B)
                + model.pv_to_grid[p, t] <= float(pvs[p][t])
            )

    return model
