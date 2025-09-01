import redis
import json
import time
#from random import randint, uniform
#testing the update
# Connect to Redis


class redisConnectionSend:

    def __init__(self, db = 0):
        """TODO: to be defined."""
        self.db = db
        self.rp = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.red_cl = redis.StrictRedis(host='localhost', port=6379, db=self.db)
        self.pubsub = self.rp.pubsub()
        self.pubsub.subscribe('registration_channel')
        print("Registering, waiting response!!")
        regData = self.read_from_redis("registraion")
          
        if regData:
           action = regData["action"]
           self.Ex_id  = regData["platID"]
           print(f"Registered: market uuid {self.Ex_id}")
           
        else:  
            try:
                for message in self.pubsub.listen():
                    if message['type'] == 'message':  # Handle actual messages
                        #data = message['data']
                        action, unique_id = message["data"].split(":")
                        if action == "end":
                            print("Received termination signal. Exiting...")
                            break  # Exit the loop to terminate
                        elif action.startswith("Registration"):
                            print(f"Registered: market uuid {unique_id}")
                            # Simulate work and write to database
                            break
            finally:
            # Ensure the pubsub connection is closed
                print("Registration channel closed.")
            self.Ex_id = unique_id
        


    def send_to_redis(self, inst, order):
    #Push to Redis
        self.red_cl.rpush(inst, json.dumps(order))
        print(f"Sent data to Redis for Slot : {inst}")
        #time.sleep(0.005)  # Simulate data sending interval
        
    def read_from_redis(self, key):
          # Retrieve all the data from the "time_series_data" list (or set a range)
        data_list = self.red_cl.lrange(key, 0, -1)  # 0 to -1 to get all elements
        if not data_list:
            print("No data found in the Redis list.")
            return False
        # Process each entry in the list
        data_dict = [json.loads(item.decode('utf-8')) for item in data_list]
        #df = pd.DataFrame(parsed_data)
        for item in data_list:
            self.red_cl.lrem(key, 1, item) #Delete read data
            
        return data_dict  
        
    def write_json(self, key: str, data: dict):
        json_data = json.dumps(data)
        self.red_cl.set(key, json_data) 
        
    def subscript(self):


        self.pubsub.subscribe('slot_channel')  # Subscribe to the steps channel

        try:
            for message in self.pubsub.listen():
                if message['type'] == 'message':  # Handle actual messages
                    step = message['data']
                    if step == "end":
                        #print("Received termination signal. Exiting...")
                        break  # Exit the loop to terminate
                    elif step.startswith("Begin"):
                        time_value = step.split()[-1]
                        r_data = {
                                "action": "Begin",
                                "timeSlot": time_value,
                                } 
                        #print(f"Executing step: {step}")
                        step = r_data
                        break
                        # Simulate work and write to database
                    elif step.startswith("Result"):
                        time_value = step.split()[-1]
                        r_data = {
                                "action": "Result",
                                "timeSlot": time_value,
                                } 
                        #print(f"Result of : {step}")
                        step = r_data
                        break
                        #r.set(f"data:{step}", f"Result of {step}")  # Save step result to Redis
        finally:
            self.pubsub.close()  # Ensure the pubsub connection is closed
            #print("Subscript A: Connection closed.")
        return step


