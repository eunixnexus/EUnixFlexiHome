def execute_market_result(agent_state, market_result, timestep):
    """
    Simulate device behavior based on market-cleared result.
    
    agent_state: dict with current SoC, PV forecast, load forecast, etc.
    market_result: dict with 'buy_kWh', 'sell_kWh' cleared quantities
    timestep: current time index
    """
    soc = agent_state["battery_soc"]
    pv = agent_state["pv_generation"][timestep]
    load = agent_state["load_demand"][timestep]

    buy_kWh = market_result.get("buy_kWh", 0)
    sell_kWh = market_result.get("sell_kWh", 0)

    # Use PV first for load
    pv_to_load = min(pv, load)
    residual_load = load - pv_to_load
    pv_left = pv - pv_to_load

    # If buying energy
    if buy_kWh > 0:
        print(f"[Timestep {timestep}] Buying {buy_kWh:.2f} kWh from grid.")
        soc += max(0, buy_kWh - residual_load)  # charge battery if extra
        residual_load -= min(buy_kWh, residual_load)

    # If selling energy
    if sell_kWh > 0:
        available_to_sell = min(soc, sell_kWh)
        print(f"[Timestep {timestep}] Selling {available_to_sell:.2f} kWh to grid.")
        soc -= available_to_sell

    # Update state
    agent_state["battery_soc"] = soc
    agent_state["executed_load"] = load
    agent_state["executed_pv"] = pv
    agent_state["grid_import"] = buy_kWh
    agent_state["grid_export"] = sell_kWh
    return agent_state
