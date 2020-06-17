import json
import os 
import pandas as pd

import util 
import data_help
import env
def store_editor(exp_db_data_filepaths, stor_pair_path, exp_stor_data_path, budg_path):
    """
    Edits a store's name across all databases.
    params:
        exp_db_data_filepaths - filepaths to expense csv's
        stor_pair_path - filepath to store name database
        exp_stor_data_path - filepath to store-expense data base
        budg_path - filepath to budget database
    """
    
    done = False
    while not done:
        df = data_help.load_csvs(exp_db_data_filepaths, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)
        stor_data = data_help.read_jsonFile(stor_pair_path)
        exp_stor_data = data_help.read_jsonFile(exp_stor_data_path)

        prompt = "Would you like to: \n(a) - change a storename\n(q) - quit\ntype here: "
        user_in = util.get_user_input_for_chars(prompt, ['a', 'b', 'q'])

        if user_in == 'a':
            change_storename(exp_db_data_filepaths, df, exp_stor_data, stor_data, stor_pair_path, exp_stor_data_path)
        elif user_in == 'q':
            done = True
    return

def change_storename(exp_db_data_filepaths, df, exp_stor_data, stor_data, stor_pair_path, exp_stor_data_path):
    storename = util.select_dict_key_using_integer(exp_stor_data, 'Please select a storename to change: ', print_children=False)
    new_name = util.prompt_with_warning("Please enter your new storename: ", ret_lowercase=True)
    if new_name != None: # none is returned from prompt_with_warning when user wants to abort.
        edit_df_entries(df, exp_db_data_filepaths[0], env.FILT_STORENAME, storename, new_name)

        stor_data = data_help.match_mod_dict_vals(stor_data, storename, new_name)
        data_help.write_to_jsonFile(stor_pair_path, stor_data)

        exp_stor_data = data_help.modify_dict_key(exp_stor_data, storename, new_name)
        data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)

def expenses_editor(exp_db_data_filepaths, stor_pair_path, exp_stor_data_path, budg_path, exp_path):
    """
    Edits an expense's name across all databases
    """
    df = data_help.load_csvs(exp_db_data_filepaths, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)
    stor_data = data_help.read_jsonFile(stor_pair_path)
    exp_stor_data = data_help.read_jsonFile(exp_stor_data_path)
    budg_data = data_help.read_jsonFile(budg_path)
    
    done = False
    while not done:
        exp_data = data_help.read_jsonFile(exp_path)
        prompt = "Would you like to:\n(a) - add an expense\n(b) - edit an expenses name\n(c) - pair expenses to stores\n(d) - delete an expense **CAUTION**\n(e) - edit an expense within your database\n(q) - quit editor\ntype here: "
        user_in = util.get_user_input_for_chars(prompt, ['a', 'b', 'c', 'd', 'e', 'q', 's'])

        if user_in == 'a':
            add_expense(exp_data, exp_stor_data, exp_path, exp_stor_data_path)
        elif user_in == 'b': # TODO
            pass
        elif user_in == 'c':
            pair_prompt = "Enter the expenses you want to add to store, separated by a space.. (q) to abort: "
            expenses = util.select_indices_of_list(pair_prompt, exp_data[env.EXPENSE_DATA_KEY], return_matches=True, abortable=True, abortchar='q')
            if expenses != None:
                for expense in expenses:
                    add_expense_to_store(exp_stor_data, exp_stor_data_path, expense)
        elif user_in == 'd':
            remove_expense_from_dbs(exp_db_data_filepaths[0], exp_stor_data, exp_data, budg_data, df, exp_stor_data_path, budg_path, exp_path)
        elif user_in == 'e':
            edit_cell_in_dfcol(exp_db_data_filepaths[0], exp_data[env.EXPENSE_DATA_KEY], df, col_name=env.EXPENSE)
        elif user_in == 'q':
            done = True
        elif user_in == 's':
            print("Ah so youre an alchemist then.")
            sync_expenses(exp_data, exp_stor_data, exp_path, exp_stor_data_path)

def remove_expense_from_dbs(exp_db_data_filepath, exp_stor_data, exp_data, budg_data, df, exp_stor_data_path, budg_path, exp_path): # TODO
    print("Warning! Removing an expense is no small task. I will be pruning your store-expense database, your overall transactions, your expenses database and you budgets.")
    print("This is irreversible, and will result in any reference to that expense being reverted to 'Misc'.")
    print("Any budget amnt for that expense will be added to Misc to maintain balance in the force.")
    exp_to_rem = util.select_from_list(exp_data[env.EXPENSE_DATA_KEY], "Which expense would you like to go? 'q' to abort: ", 
                                       abortchar='q', ret_match=True)
    if exp_to_rem != env.EXPENSE_MISC_STR:
        if exp_to_rem != None: # none comes if user aborts
            for store in exp_stor_data.keys(): # delete from exp_stor db
                if exp_to_rem in exp_stor_data[store]:
                    exp_stor_data[store].remove(exp_to_rem)
                    print(f"Removed {exp_to_rem} from {store}.")
            
            data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)
            
            exp_data[env.EXPENSE_DATA_KEY].remove(exp_to_rem) # delete from expenses db
            data_help.write_to_jsonFile(exp_path, exp_data)

            for date in budg_data.keys(): # remove from budget, adding amnt to Misc
                amnt_to_misc = budg_data[date][exp_to_rem]
                budg_data[date][env.EXPENSE_MISC_STR] += amnt_to_misc
                budg_data[date].pop(exp_to_rem)
            data_help.write_to_jsonFile(budg_path, budg_data)

            edit_df_entries(df, exp_db_data_filepath, env.EXPENSE, exp_to_rem, env.EXPENSE_MISC_STR)
    else:
        print(f"'{env.EXPENSE_MISC_STR}' is a reserved expense category, and it cannot be deleted.")

def edit_cell_in_dfcol(db_data_filepath : str, options_for_cell, df, col_name):
    index_list = df.index.tolist()
    print(df)
    prompt = "Select some indices from the above dataframe to edit: (q) to quit: "
    indices = util.select_indices_of_list(prompt, index_list, return_matches=True, abortable=True, abortchar='q', print_lst=False)
    if indices != None:
        for index in indices:
            option = util.select_from_list(options_for_cell, "Please select an option for this cell (q) to quit: ", abortchar='q', ret_match=True)
            if option != None:
                df.at[index, col_name] = option
                data_help.write_data(df, db_data_filepath)
            else:
                break

def add_expense(exp_data, exp_stor_data, exp_path, exp_stor_data_path):
    """
    Adds an expense to the expense database
    """
    flag = False 
    while not flag:
        exp_input = input("Enter the expense you wish to add: ")
        if exp_input not in exp_data[env.EXPENSE_DATA_KEY]:
            exp_data[env.EXPENSE_DATA_KEY].append(exp_input)
            data_help.write_to_jsonFile(exp_path, exp_data)

            user_in = util.get_user_input_for_chars("Do you want to add this expense to some stores [y/n]? ", ['y', 'n'])
            if user_in == 'y':
                add_expense_to_store(exp_stor_data, exp_stor_data_path, exp_input)

            else:
                flag = True
        else:
            print(f"That expense already exists! Try another one. Heres the list of existing expenses: {exp_data[env.EXPENSE_DATA_KEY]}")

def add_expense_to_store(exp_stor_data, exp_stor_data_path, expense):
    """
    Adds an expense to a store within storesWithExpenses.json
    params:
        exp_stor_data : the dict object of storesWithExpenses.json
        exp_stor_data_keylist : the list of keys of exp_stor_data
        expense : the expense to add to the store selected by the user
    """
    exp_stor_data_keylist = list(exp_stor_data.keys())
    exp_stor_data_keylist.sort()
    store_idxs = util.select_indices_of_list(prompt="Select a store to add this expense to. (q) to abort.", list_to_compare_to=exp_stor_data_keylist, abortable=True, abortchar='q') # TODO: Add the storename
    if store_idxs != None:
        for idx in store_idxs:
            exp_stor_data[exp_stor_data_keylist[idx]] = [expense]
            print(f"Added {expense} to {exp_stor_data_keylist[idx]}")
        data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)

def edit_df_entries(df, df_path, column_name, old_entry, new_entry):
    """
    Edits a value in a column replacing it with new_entry
    """
    if not df.loc[df[column_name] == old_entry].empty:
            df.loc[df[column_name] == old_entry, column_name] = new_entry
            data_help.write_data(df, df_path)
    else:
        print("No records matched in dataframe. Left it alone.")

def sync_expenses(exp_data, exp_stor_data, exp_path, exp_stor_data_path):
    """
    Makes sure that the expenses in storesWithExpenses.json are matched to expenses.json
    """
    matched_expenses = []
    for stor,expenses in exp_stor_data.items():
        for expense in expenses:
            if expense in exp_data[env.EXPENSE_DATA_KEY]:
                matched_expenses.append(expense)
            else:
                print(f"REMOVED: {expense} from {stor}")
        exp_stor_data[stor] = matched_expenses
        matched_expenses = []
    data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)

def set_dict_keys_to_lowercase(dct_path):
    dct = data_help.read_jsonFile(dct_path)
    for key in dct.keys():
        dct = data_help.modify_dict_key(dct, key, key.lower())
    data_help.write_to_jsonFile(dct_path, dct)
