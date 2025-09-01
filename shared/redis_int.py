# common/redis_interface.py

import redis
import json
from shared import config

class RedisInterface:
    def __init__(self, db=0):
        self.redis = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=db,
            decode_responses=True
        )

    def write_json(self, key: str, data: dict):
        json_data = json.dumps(data)
        self.redis.set(key, json_data)



    def read_json(self, key):
        data_list = self.redis.lrange(key, 0, -1)  # Get all elements
        if not data_list:
            print("No data found in the Redis list.")
            return False

        data_dict = [json.loads(item) for item in data_list]

        #for item in data_list:
            #self.redis.lrem(key, 1, item)  # Remove after reading

        return data_dict
    
    
    
    def read_dir(self, key):
        data = self.redis.get(key)
        if not data:
            print(f"No data found for key: {key}")
            return None
        return json.loads(data)

        


    def rpush_json(self, key: str, data: dict):
        self.redis.rpush(key, json.dumps(data))

    def lrange_json(self, key: str):
        raw_list = self.redis.lrange(key, 0, -1)
        return [json.loads(item) for item in raw_list]

    def lrem(self, key: str, value):
        self.redis.lrem(key, 1, json.dumps(value))

    def publish(self, channel: str, message: str):
        self.redis.publish(channel, message)

    def subscribe(self, channel: str):
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
        return pubsub

    def setex(self, key, ttl, value):
        self.redis.setex(key, ttl, json.dumps(value))
