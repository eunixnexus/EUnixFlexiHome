# agent_controller.py

from shared.redis_int import RedisInterface
from shared.utils import log
from main_doc.resultAnalysis import process_buying, process_selling, update_batteries_from_trans
import json

class AgentController:
    def __init__(self, bid_agents, offer_agents, batt_agents, unit_area, sim_data_load, sim_data_gen):
        self.bid_agents = bid_agents
        self.offer_agents = offer_agents
        self.batt_agents = batt_agents
        self.unit_area = unit_area
        self.sim_data_load = sim_data_load
        self.sim_data_gen = sim_data_gen

        self.local_db = RedisInterface(db=1)
        self.market_db = RedisInterface(db=0)

    def send_bids_offers(self, sim_slot):
        for b_username, b_agent in self.bid_agents.items():
            row = self.sim_data_load[b_username]
            slot_data = row[row["Datetime"] == sim_slot]
            if slot_data.empty:
                log(f"No load data for {b_username} at {sim_slot}")
                continue
            bid = b_agent.bidPrice(slot_data)
            self.market_db.rpush_json(sim_slot, bid)

        for o_username, o_agent in self.offer_agents.items():
            row = self.sim_data_gen[o_username]
            slot_data = row[row["Datetime"] == sim_slot]
            if slot_data.empty:
                log(f"No gen data for {o_username} at {sim_slot}")
                continue
            offer = o_agent.offerPrice(slot_data)
            self.market_db.rpush_json(sim_slot, offer)

    def process_market_results(self, sim_slot, battery_objects_dict):
        key = f"market_result:{self.unit_area}:{sim_slot}"
        results = self.market_db.lrange_json(key)
        if not results:
            log(f"No market results for {sim_slot}")
            return

        result = results[0]  # assuming 1 result per slot
        bought, sold = process_buying(result), process_selling(result)
        update_batteries_from_trans(bought[0], battery_objects_dict)
        update_batteries_from_trans(sold[0], battery_objects_dict)

    def send_battery_orders(self, bids_df, offers_df, sim_slot):
        for df, label in [(bids_df, "bidding"), (offers_df, "offering")]:
            if df.empty:
                log(f"No battery is {label}.")
                continue
            for _, row in df.iterrows():
                self.market_db.rpush_json(sim_slot, row.to_dict())
