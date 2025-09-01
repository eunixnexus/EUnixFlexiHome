
import time
from random import randint, uniform
import uuid
#Define the user here

class Agent:

    def __init__(self, user, unit_area):
        """TODO: to be defined."""
        self.user = user
        self.unit_area = unit_area
        self.userID = str(uuid.uuid4())


    def bidPrice(self, simu_row):
        price = round(uniform(10, 30), 2)
    
        data = {
            "User": self.user,
            "User_id": self.userID,
            "Unit_area": self.unit_area,
            "Order_id": str(uuid.uuid4()), 
            "energy_qty": simu_row.iloc[0]['Energy'],         
            "energy_rate": price,
            "bid-offer-time": (simu_row.iloc[0]['Datetime']).isoformat(), 
            "delivery-time": (simu_row.iloc[0]['Datetime']).isoformat(),            
            "Type": True,
        }  

        return data


    def offerPrice(self, simu_row):
        price = round(uniform(5, 25), 2)
    
        data = {
            "User": self.user,
            "User_id": self.userID,
            "Unit_area": self.unit_area,
            "Order_id": str(uuid.uuid4()), 
            "energy_qty": simu_row.iloc[0]['Energy'],         
            "energy_rate": price,
            "bid-offer-time": (simu_row.iloc[0]['Datetime']).isoformat(), 
            "delivery-time": (simu_row.iloc[0]['Datetime']).isoformat(),           
            "Type": False,
        }  
    
    
        return data
