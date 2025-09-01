import random
import numpy as np
import pandas as pd

#predicted_bid_prices = forecasted_bid_prices + margin
#predicted_offer_prices = forecasted_offer_prices - margin

forecasted_prices = [0, 2]


# === 4. Q-learning Agent ===
class QLearningBidder:
    def __init__(self, alpha=0.1, gamma=0.95, epsilon=0.1):
        self.q_table = {}
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.actions = [-0.01, 0.0, 0.01]

    def get_qs(self, state):
        if state not in self.q_table:
            self.q_table[state] = [0.0 for _ in self.actions]
        return self.q_table[state]

    def choose_action(self, state):
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        qs = self.get_qs(state)
        return self.actions[np.argmax(qs)]

    def update(self, state, action, reward, next_state):
        qs = self.get_qs(state)
        next_qs = self.get_qs(next_state)
        action_idx = self.actions.index(action)
        qs[action_idx] += self.alpha * (reward + self.gamma * max(next_qs) - qs[action_idx])




# === 9. Q-learning on First Forecasted Bid ===
agent = QLearningBidder()
state = round(forecasted_prices[0], 3)
base_bid = forecasted_prices[0]
adjustment = agent.choose_action(state)
final_bid = base_bid + adjustment
accepted = final_bid >= 0.18
reward = (final_bid - 0.18) if accepted else -0.01
next_state = round(forecasted_prices[1], 3)
agent.update(state, adjustment, reward, next_state)

print(f"\n🔍 Forecasted price: {base_bid:.3f}")
print(f"🤖 Q-Learning bid adjustment: {adjustment:+.3f}")
print(f"💰 Final bid: {final_bid:.3f}")
print(f"🏁 Reward: {reward:.3f}")
