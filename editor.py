import json
import os 
import pandas as pd

import util 
import data_help
import env
def store_editor(db_data_filepaths, stor_pair_path, exp_stor_data_path, budg_path):
    """
    Edits a store's name across all databases.
    params:
        db_data_filepaths - filepaths to money csv's
        stor_pair_path - filepath to store name database
        exp_stor_data_path - filepath to store-expense data base
        budg_path - filepath to budget database
    """
    df = data_help.load_csvs(db_data_filepaths, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)
    stor_data = data_help.read_jsonFile(stor_pair_path)
    exp_stor_data = data_help.read_jsonFile(exp_stor_data_path)
    # budg_data = data_help.read_jsonFile(budg_path)
    storename = util.select_dict_key_using_integer(exp_stor_data, 'Please select a storename to change: ', print_children=False)
    new_name = util.prompt_with_warning("Please enter your new storename: ")
    if new_name != None: # none is returned from prompt_with_warning when user wants to quit.
        edit_df_entries(df, db_data_filepaths[0], env.FILT_STORENAME, storename, new_name)

        stor_data = data_help.match_mod_dict_vals(stor_data, storename, new_name)
        data_help.write_to_jsonFile(stor_pair_path, stor_data)

        exp_stor_data = data_help.modify_dict_key(exp_stor_data, storename, new_name)
        data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)
    
    return

def expenses_editor(db_data_filepaths, stor_pair_path, exp_stor_data_path, budg_path, exp_path):
    """
    Edits an expense's name across all databases
    """
    df = data_help.load_csvs(db_data_filepaths, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)
    stor_data = data_help.read_jsonFile(stor_pair_path)
    exp_stor_data = data_help.read_jsonFile(exp_stor_data_path)
    budg_data = data_help.read_jsonFile(budg_path)
    
    done = False
    while not done:
        exp_data = data_help.read_jsonFile(exp_path)
        prompt = "Would you like to:\n(a) - add an expense\n(b) - edit an expenses name\n(c) - delete an expense **CAUTION**\n(q) - quit editor\ntype here: "
        user_in = util.get_user_input_for_chars(prompt, ['a', 'b', 'c', 'q'])

        if user_in == 'a':
            add_expense(exp_data, exp_stor_data, exp_path, exp_stor_data_path)
        elif user_in == 'b': # TODO
            pass
        elif user_in == 'c':
            pass 
        elif user_in == 'q':
            done = True
        

def add_expense(exp_data, exp_stor_data, exp_path, exp_stor_data_path):
    """
    Adds an expense to the expense database
    """
    flag = False 
    exp_stor_data_keylist = list(exp_stor_data.keys())
    while not flag:
        exp_input = input("Enter the expense you wish to add: ")
        exp_data[env.EXPENSE_DATA_KEY].append(exp_input)
        data_help.write_to_jsonFile(exp_path, exp_data)

        user_in = util.get_user_input_for_chars("Do you want to add this expense to some stores [y/n]? ", ['y', 'n'])
        if user_in == 'y':
            store_idxs = util.select_indices_of_list(prompt="Select a store to add this expense to.", list_to_compare_to=exp_stor_data_keylist) # TODO: Add the storename
            for idx in store_idxs:
                exp_stor_data[exp_stor_data_keylist[idx]] = exp_input
                print(f"Added {exp_input} to {exp_stor_data_keylist[idx]}")
            data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)

        else:
            flag = True


def edit_df_entries(df, df_path, column_name, old_entry, new_entry):
    if not df.loc[df[column_name] == old_entry].empty:
            df.loc[df[column_name] == old_entry, column_name] = new_entry
            data_help.write_data(df, df_path)
    else:
        print("No records matched in dataframe. Left it alone.")