import numpy as np
import pandas as pd
from pyomo.environ import *

# Parameters
T = 96  # time steps (15-min)
dt = 0.25
battery_capacity = 10  # MWh
battery_power = 5      # MW
efficiency = 0.95
initial_soc = 5        # MWh
degradation_cost = 5   # €/MWh
price_da = np.random.uniform(50, 150, T)
price_id = np.random.uniform(40, 160, T)
price_fcr = 100  # €/MW/day (simplified)

# Pyomo Model
model = ConcreteModel()
model.T = RangeSet(0, T-1)
model.charge = Var(model.T, domain=NonNegativeReals)
model.discharge = Var(model.T, domain=NonNegativeReals)
model.soc = Var(model.T, domain=NonNegativeReals)

# Objective: Maximize profit = discharge revenue - charge cost - degradation + FCR
model.obj = Objective(
    expr=sum((price_id[t] * model.discharge[t] - price_da[t] * model.charge[t] 
              - degradation_cost * (model.charge[t] + model.discharge[t])) * dt for t in model.T)
    + price_fcr * battery_power, sense=maximize)

# SoC dynamics
def soc_balance_rule(m, t):
    if t == 0:
        return m.soc[t] == initial_soc + (efficiency * m.charge[t] - m.discharge[t] / efficiency) * dt
    return m.soc[t] == m.soc[t-1] + (efficiency * m.charge[t] - m.discharge[t] / efficiency) * dt
model.soc_balance = Constraint(model.T, rule=soc_balance_rule)

# Constraints
model.soc_limit = Constraint(model.T, rule=lambda m, t: m.soc[t] <= battery_capacity)
model.charge_limit = Constraint(model.T, rule=lambda m, t: m.charge[t] <= battery_power)
model.discharge_limit = Constraint(model.T, rule=lambda m, t: m.discharge[t] <= battery_power)

# Solve
solver = SolverFactory('cbc')  # or 'glpk', 'gurobi'
solver.solve(model)

# Output
result = pd.DataFrame({
    "Time": pd.date_range("2025-01-01", periods=T, freq="15min"),
    "Price_DA": price_da,
    "Price_ID": price_id,
    "Charge": [value(model.charge[t]) for t in model.T],
    "Discharge": [value(model.discharge[t]) for t in model.T],
    "SoC": [value(model.soc[t]) for t in model.T]
})
result["Revenue (€)"] = result["Discharge"] * result["Price_ID"] * dt
result["Cost (€)"] = result["Charge"] * result["Price_DA"] * dt
result["Degradation (€)"] = (result["Charge"] + result["Discharge"]) * degradation_cost * dt
result["Net Profit (€)"] = result["Revenue (€)"] - result["Cost (€)"] - result["Degradation (€)"]

print("Total Daily Net Profit (with FCR): €", round(result["Net Profit (€)"].sum() + price_fcr * battery_power, 2))
