# solver_runner.py
from pyomo.environ import SolverFactory

def solve_model(model):
    solver = SolverFactory("cbc")
    results = solver.solve(model, tee=True)
    return results
