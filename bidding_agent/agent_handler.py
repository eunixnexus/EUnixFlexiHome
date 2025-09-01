from shared.redis_int import RedisInterface
from shared.utils import log

class AgentRedisHandler:
    def __init__(self):
        self.market_db = RedisInterface(db=0)
        self.local_db = RedisInterface(db=1)
        self.pubsub = self.market_db.subscribe("registration_channel")
        self.Ex_id = self._handle_registration()

    def _handle_registration(self):
        log("Registering, waiting for response...")
        reg_data = self.local_db.read_json("registration")  # assuming local agent stores it

        if reg_data:
            log(f"Registered: market uuid {reg_data['platID']}")
            return reg_data["platID"]

        try:
            for msg in self.pubsub.listen():
                if msg["type"] == "message":
                    action, plat_id = msg["data"].split(":")
                    if action == "end":
                        log("Received termination signal.")
                        break
                    elif action.startswith("Registration"):
                        log(f"Registered via pubsub: market uuid {plat_id}")
                        return plat_id
        finally:
            self.pubsub.close()
            log("Registration channel closed.")
        return None

    def send_to_market(self, key, data):
        self.market_db.rpush_json(key, data)
        log(f"Sent to market DB: {key}")

    def send_to_local(self, key, data):
        self.local_db.rpush_json(key, data)
        log(f"Sent to local DB: {key}")

    def read_local(self, key):
        data = self.local_db.lrange_json(key)
        for item in data:
            self.local_db.lrem(key, item)
        return data

    def wait_for_signal(self, channel):
        pub = self.market_db.subscribe(channel)
        try:
            for msg in pub.listen():
                if msg["type"] == "message":
                    step = msg["data"]
                    if step == "end":
                        break
                    elif step.startswith("Begin"):
                        return {"action": "Begin", "timeSlot": step.split()[-1]}
                    elif step.startswith("Result"):
                        return {"action": "Result", "timeSlot": step.split()[-1]}
        finally:
            pub.close()
