import numpy as np
import matplotlib.pyplot as plt

class Battery:
    def __init__(self, capacity_kWh, max_power_kW, charge_efficiency=0.95, discharge_efficiency=0.95):
        self.capacity_kWh = capacity_kWh
        self.max_power_kW = max_power_kW
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency
        self.soc = 0.5 * capacity_kWh  # Start at 50% SOC
    
    def charge(self, power_kW, duration_h):
        energy_to_charge = power_kW * duration_h * self.charge_efficiency
        available_capacity = self.capacity_kWh - self.soc
        actual_energy = min(energy_to_charge, available_capacity)
        self.soc += actual_energy
        return actual_energy / self.charge_efficiency  # Energy drawn from the grid

    def discharge(self, power_kW, duration_h):
        energy_to_discharge = power_kW * duration_h * self.discharge_efficiency
        actual_energy = min(energy_to_discharge, self.soc)
        self.soc -= actual_energy
        return actual_energy * self.discharge_efficiency  # Energy delivered to the grid

    def get_soc(self):
        return self.soc

# Simulate price data and trading behavior
np.random.seed(42)
time_steps = 24  # 24 hours
duration_h = 1
prices = np.random.uniform(20, 100, time_steps)  # €/MWh

battery = Battery(capacity_kWh=100, max_power_kW=25)
soc_history = []
profit = 0

for t in range(time_steps):
    price = prices[t]
    soc = battery.get_soc()
    soc_history.append(soc)

    if price < 40:  # Buy energy (charge)
        energy_from_grid = battery.charge(battery.max_power_kW, duration_h)
        cost = energy_from_grid * price / 1000  # Convert kWh to MWh
        profit -= cost
        print(f"Hour {t}: Charging {energy_from_grid:.2f} kWh at {price:.2f} €/MWh. Cost: €{cost:.2f}")
    
    elif price > 80:  # Sell energy (discharge)
        energy_to_grid = battery.discharge(battery.max_power_kW, duration_h)
        revenue = energy_to_grid * price / 1000
        profit += revenue
        print(f"Hour {t}: Discharging {energy_to_grid:.2f} kWh at {price:.2f} €/MWh. Revenue: €{revenue:.2f}")

print(f"\nTotal profit: €{profit:.2f}")

# Plot SOC over time
plt.plot(soc_history, label="State of Charge (kWh)")
plt.xlabel("Hour")
plt.ylabel("Energy (kWh)")
plt.title("Battery SOC Over Time")
plt.grid(True)
plt.legend()
plt.show()
