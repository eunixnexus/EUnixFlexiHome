from typing import List, Dict, Any
import numpy as np
import pandas as pd
import uuid

# ========= 1. Battery Class Definition =========
class Battery:
    def __init__(self, user, unit_area, capacity_kWh, soc_kWh, charge_eff=0.95, discharge_eff=0.95, max_c_rate=50,max_d_rate=60, min_energy =5):
        self.user = user
        self.unit_area = unit_area
        self.userID = str(uuid.uuid4())
        self.capacity = capacity_kWh
        self.soc = soc_kWh
        self.charge_eff = charge_eff
        self.discharge_eff = discharge_eff
        self.max_charge_rate = max_c_rate  # Max charge kWh per time step
        self.max_discharge_rate = max_d_rate  # Max charge kWh per time step
        self.min_ben = min_energy #in kWh

    def get_soc_percent(self):
        return (self.soc / self.capacity) * 100

    def can_charge(self):
        return self.soc < self.capacity

    def can_discharge(self):
        return self.soc > (self.min_ben/self.discharge_eff) #We keep 2kWh so as not to fully discharge the battery

    def charge(self, energy_kWh):
        energy_in = min(energy_kWh, self.capacity - self.soc, self.max_charge_rate)
        self.soc += energy_in * self.charge_eff
        return energy_in  # Energy used from the grid

    def discharge(self, energy_kWh):
        energy_out = min((energy_kWh/self.discharge_eff), (self.soc-(self.min_ben/ self.discharge_eff)), (self.max_discharge_rate/ self.discharge_eff))
        self.soc -= energy_out
        return energy_out  # Energy delivered to the grid

    def get_offer(self, offer_thresh, sim_slot):
        """If SOC is high, offer energy."""
        if self.get_soc_percent() > 50:
            price = np.random.uniform(offer_thresh, offer_thresh + 15)#Perform Bidding strategy to determine the price
            quantity = min(self.max_discharge_rate, (self.soc-self.min_ben)*self.charge_eff)#Perform optimization to determine the quantity
            data = {
            "User": self.user,
            "User_id": self.userID,
            "Unit_area": self.unit_area,
            "Order_id": str(uuid.uuid4()), 
            "energy_qty": quantity,         
            "energy_rate": price,
            "bid-offer-time": sim_slot, 
            "delivery-time": sim_slot,            
            "Type": False,
            } 
            return data
        return None

    def get_bid(self, bid_thresh, sim_slot):
        """If SOC is low, bid to buy energy."""
        if self.get_soc_percent() < 50:
            price = np.random.uniform(bid_thresh - 15, bid_thresh + 0.05) #Perform Bidding strategy to determine the price
            quantity = min(self.max_charge_rate, (self.capacity - self.soc)/self.charge_eff) #Perform optimization to determine the quantity
            data = {
            "User": self.user,
            "User_id": self.userID,
            "Unit_area": self.unit_area,
            "Order_id": str(uuid.uuid4()), 
            "energy_qty": quantity,         
            "energy_rate": price,
            "bid-offer-time": sim_slot, 
            "delivery-time": sim_slot,            
            "Type": True,
            } 
            return data
        return None




# ========= 3. Simulate Market Interaction =========
def create_bat_orders(batteries, sim_slot, bid_threshold, offer_threshold):
    bids, offers = [], []
    
    for bat in batteries:
        bid = bat.get_bid(bid_threshold, sim_slot)
        offer = bat.get_offer(offer_threshold,sim_slot)
        if bid: bids.append(bid)
        if offer: offers.append(offer)

    return pd.DataFrame(bids), pd.DataFrame(offers)



def validate_and_structure_batteries(storage: Dict[str, List[float]], unit_area) -> List[Dict[str, Any]]:
    required_keys = ["capacities_kWh", "SOCs_kWh"]
    optional_keys_with_limits = ["charge_eff", "discharge_eff"]
    optional_keys_relative_to_capacity = ["max_ch_rate", "max_disch_rate", "min_energy"]

    # 1. Check that required keys are not empty
    for key in required_keys:
        if key not in storage or not storage[key]:
            raise ValueError(f"'{key}' is required and must not be empty.")

    base_length = len(storage["capacities_kWh"])

    # 2. Check that all non-empty lists have the same length
    for key, value in storage.items():
        if value and len(value) != base_length:
            raise ValueError(f"All non-empty arrays must be the same length. "
                             f"Key '{key}' has length {len(value)}, expected {base_length}.")

    # 3. Check SOCs < capacities
    for i, (soc, cap) in enumerate(zip(storage["SOCs_kWh"], storage["capacities_kWh"])):
        if soc >= cap:
            raise ValueError(f"At index {i}, SOC ({soc}) must be less than capacity ({cap}).")

    # 4. Check efficiency values are < 1
    for key in optional_keys_with_limits:
        if key in storage:
            for i, value in enumerate(storage[key]):
                if value >= 1:
                    raise ValueError(f"At index {i}, value in '{key}' ({value}) must be less than 1.")

    # 5. Check optional fields relative to capacity
    for key in optional_keys_relative_to_capacity:
        if key in storage:
            for i, (val, cap) in enumerate(zip(storage[key], storage["capacities_kWh"])):
                if val >= cap:
                    raise ValueError(f"At index {i}, value in '{key}' ({val}) must be less than capacity ({cap}).")

    # 6. Structure the battery data
    batteries = []
    for i in range(base_length):
        battery_kwargs = {
            "user": f"Bat_{i+1}",
            "unit_area":unit_area,
            "capacity_kWh": storage["capacities_kWh"][i],
            "soc_kWh": storage["SOCs_kWh"][i]
        }

        if storage["charge_eff"]:
            battery_kwargs["charge_eff"] = storage["charge_eff"][i]
        if storage["discharge_eff"]:
            battery_kwargs["discharge_eff"] = storage["discharge_eff"][i]
        if storage["max_ch_rate"]:
            battery_kwargs["max_c_rate"] = storage["max_ch_rate"][i]
        if storage["max_disch_rate"]:
            battery_kwargs["max_d_rate"] = storage["max_disch_rate"][i]
        if storage["min_energy"]:
            battery_kwargs["min_energy"] = storage["min_energy"][i]

        batteries.append(Battery(**battery_kwargs))

    return batteries
