import os

import pandas as pd
from main_doc.batt import Battery as btt
from io import StringIO



def sort_trans_by_type(trans):
    """
    Splits a list of transaction dictionaries into two DataFrames:
    one for Buying transactions and one for Selling transactions.

    Parameters:
    transactions (list): A list of dictionaries representing transactions.

    Returns:
    tuple: (buying_df, selling_df)
    """
        # Check that input is a list of dicts
    if not isinstance(trans, list) or not all(isinstance(item, dict) for item in trans):
        raise ValueError("Input must be a list of dictionaries representing transactions.")

    # Convert the list of transactions to a DataFrame
    df = pd.DataFrame(trans)

    # Filter the DataFrame based on the 'Trans_type' column
    buying_df = df[df["Trans_type"] == "Buying"].reset_index(drop=True)
    selling_df = df[df["Trans_type"] == "Selling"].reset_index(drop=True)

    return buying_df, selling_df


def process_buying(bought_data):
    """
    Splits the dataframe into two:
    - battery_users: rows where Buyer starts with 'Bat'
    - non_battery_users: all other rows
    """
    # Ensure 'Buyer' column exists
    if not isinstance(bought_data, pd.DataFrame):
        try:
            bought_data = pd.read_json(StringIO(bought_data))
        except:
            print("Error: bought_data is not a DataFrame or valid JSON.")
            return pd.DataFrame()
    if 'Buyer' not in bought_data.columns:
        return pd.DataFrame()
        
    # Use str.startswith() to split
    battery_users = bought_data[bought_data['Buyer'].str.startswith('Bat')]
    non_battery_users = bought_data[~bought_data['Buyer'].str.startswith('Bat')]

    return battery_users, non_battery_users


def process_selling(sold_data):
    """
    Splits the dataframe into two:
    - battery_users: rows where Sellers starts with 'Bat'
    - non_battery_users: all other rows
    """
    # Ensure 'Seller' column exists

    if not isinstance(sold_data, pd.DataFrame):
        try:
            #sold_data = pd.read_json(sold_data)
            sold_data = pd.read_json(StringIO(sold_data))
        except:
            print("Error: bought_data is not a DataFrame or valid JSON.")
            return pd.DataFrame()
    if 'Buyer' not in sold_data.columns:
        return pd.DataFrame()     
        
        
        
        
    # Use str.startswith() to split
    battery_users = sold_data[sold_data['Seller'].str.startswith('Bat')]
    non_battery_users = sold_data[~sold_data['Seller'].str.startswith('Bat')]

    return battery_users, non_battery_users

def update_batteries_from_trans(df_battery_trans, battery_objects_dict):

    """
    Updates SOC of battery objects based on transaction data.
    
    Args:
    - df_battery_trans: DataFrame containing only transactions involving batteries (as Buyer or Seller)
    - battery_objects_dict: Dict of Battery objects keyed by user name, e.g., {'Bat_1': Battery(...)}
    
    Returns:
    - Updated battery_objects_dict
    """
    for _, row in df_battery_trans.iterrows():
        user = row['Buyer'] if row['Trans_type'] == "Buying" else row['Seller']

        energy = row['Matched_qty']

        if user in battery_objects_dict:
            battery = battery_objects_dict[user]

            if row['Trans_type'] == "Buying":
                if battery.can_charge():
                    charged = battery.charge(energy)
                    print(f"{user} charged with {charged:.2f} kWh (Matched: {energy:.2f} kWh), soc is now {battery.soc}")
            elif row['Trans_type'] == "Selling":
                if battery.can_discharge():
                    discharged = battery.discharge(energy)
                    print(f"{user} discharged {discharged:.2f} kWh (Matched: {energy:.2f} kWh), soc is now {battery.soc}")


    return battery_objects_dict



