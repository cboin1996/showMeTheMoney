import json
import os 
import pandas as pd

import util 
import data_help
import env
import expManager

def df_editor(df_filepaths):
    """
    Allows the editing of a dataframe
    """
    done = False
    while not done:
        df = data_help.load_csvs(df_filepaths, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)
        prompt = "Whould you like to: \n(a) - delete a row\n(q) - quit\nType here: "
        user_in = util.get_user_input_for_chars(prompt, ['a', 'q'])

        if user_in ==  'a':
            util.print_fulldf(df)
            edit_prompt = "Which row or rows would you like to delete (q) to abort? "
            rows = util.select_indices_of_list(edit_prompt, list(df.index), abortable=True, abortchar='q', print_lst=False)
            if rows is not None: # above returns none if user aborts
                df.drop(index=rows, inplace=True)
                data_help.write_data(df, df_filepaths[0])

        elif user_in == 'q':
            done = True
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
    storename = util.select_dict_key_using_integer(exp_stor_data, 'Please select a storename to change, (q) to quit: ', print_children=False, quit_str='q')
    if storename != None: # select_dict_key_using_integer returns none if quitstr is given
        new_name = util.prompt_with_warning("Please enter your new storename: ", ret_lowercase=True)
        if new_name != None: # none is returned from prompt_with_warning when user wants to abort.
            print(f"--- Editing {env.OUT_EXP_DATA_TEMPL} --- ")
            edit_df_entries(df, exp_db_data_filepaths[0], env.FILT_STORENAME, storename, new_name)
            print(f"--- Editing {env.STORE_PAIR_FNAME} --- ")
            stor_data = data_help.match_mod_dict_vals(stor_data, storename, new_name)
            data_help.write_to_jsonFile(stor_pair_path, stor_data)
            print(f"--- Editing {env.EXP_STOR_DB_FNAME} --- ")
            exp_stor_data = data_help.modify_dict_key(exp_stor_data, storename, new_name)
            data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)

def expenses_editor(exp_db_data_filepaths, stor_pair_path, exp_stor_data_path, budg_path, exp_path):
    """
    Edits an expense's name across all databases
    """
    done = False
    while not done:
        exp_data = data_help.read_jsonFile(exp_path)
        df = data_help.load_csvs(exp_db_data_filepaths, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)
        stor_data = data_help.read_jsonFile(stor_pair_path)
        exp_stor_data = data_help.read_jsonFile(exp_stor_data_path)
        budg_data = data_help.read_jsonFile(budg_path)

        prompt = "Would you like to:\n(a) - add an expense\n(b) - edit an expenses name\n(c) - pair expenses to stores\n(d) - delete an expense **CAUTION**\n(e) - edit an expense within your database\n(q) - quit editor\ntype here: "
        user_in = util.get_user_input_for_chars(prompt, ['a', 'b', 'c', 'd', 'e', 'q', 's'])

        if user_in == 'a':
            add_expense(exp_data, exp_stor_data, exp_path, exp_stor_data_path)
        elif user_in == 'b': # TODO
            edit_expense_name(exp_db_data_filepaths[0], df, exp_data, budg_data, exp_stor_data, exp_path, budg_path, exp_stor_data_path)
        elif user_in == 'c':
            pair_prompt = "Enter the expenses you want to add to store, separated by a space.. (q) to abort: "
            expenses = util.select_indices_of_list(pair_prompt, exp_data[env.EXPENSE_DATA_KEY], return_matches=True, abortable=True, abortchar='q')
            if expenses != None:
                for expense in expenses:
                    add_expense_to_store(exp_stor_data, exp_stor_data_path, expense)
        elif user_in == 'd':
            remove_expense_from_dbs(exp_db_data_filepaths[0], exp_stor_data, exp_data, budg_data, df, exp_stor_data_path, budg_path, exp_path)
        elif user_in == 'e':
            edit_cell_in_dfcol(exp_db_data_filepaths[0], df, col_name=env.EXPENSE, opt_col=env.FILT_STORENAME, opt_dict=exp_stor_data)
        elif user_in == 'q':
            done = True
        elif user_in == 's':
            print("Ah so youre an alchemist then.")
            sync_expenses(exp_data, exp_stor_data, exp_path, exp_stor_data_path)

def edit_expense_name(exp_db_data_filepath, df, exp_data, budg_data, exp_stor_data, exp_path, budg_path, exp_stor_data_path):
    """
    Edits an expense name across storesWithExpenses.json, Budgjet.json, expenses.json, and exp_db.csv
    """
    exp_to_edit = util.select_from_list(exp_data[env.EXPENSE_DATA_KEY], "Which expense would you like to edit? 'q' to abort: ",
                                        abortchar='q', ret_match=True)
    
    if exp_to_edit != env.EXPENSE_MISC_STR:
        if exp_to_edit != None: # none if user aborts
            expense_new_name = util.select_item_not_in_list(f"Enter your new expense name for '{exp_to_edit}' 'q' to abort: ", exp_data[env.EXPENSE_DATA_KEY],
                                                         ignorecase=False, abortchar='q')
            if expense_new_name != None: 
                # edit the exp_stor_db
                print(f"--- Editing {env.EXP_STOR_DB_FNAME} --- ")
                for store in exp_stor_data.keys():
                    if exp_to_edit in exp_stor_data[store]:
                        print(f"In {store}: ", end=" ")
                    exp_stor_data[store] = util.replace_string_in_list(exp_stor_data[store], exp_to_edit, expense_new_name)
            
                # Edit the budg_db
                print(f"\n--- Editing {env.BUDGET_FNAME} --- ")
                for date in budg_data.keys():
                    budg_data[date] = data_help.modify_dict_key(budg_data[date], exp_to_edit, expense_new_name)
                # Edit expenses.json
                print(f"--- Editing {env.EXP_FNAME} --- ")
                exp_data[env.EXPENSE_DATA_KEY] = util.replace_string_in_list(exp_data[env.EXPENSE_DATA_KEY], exp_to_edit, expense_new_name)
                # Edit exp_db.csv (writes itself)
                print(f"--- Editing {env.OUT_EXP_DATA_TEMPL} --- ")
                edit_df_entries(df, exp_db_data_filepath, env.EXPENSE, exp_to_edit, expense_new_name)
                # Write changes
                data_help.write_to_jsonFile(budg_path, budg_data)
                data_help.write_to_jsonFile(exp_path, exp_data)
                data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)

    else:
        print(f"'{env.EXPENSE_MISC_STR}' is a reserved expense category, and its name cannot be changed.")

def remove_expense_from_dbs(exp_db_data_filepath, exp_stor_data, exp_data, budg_data, df, exp_stor_data_path, budg_path, exp_path): 
    """
    Removes an expense from the storesWithExpenses.json, Budgjet.json, expenses.json
    """
    print("Warning! Removing an expense is no small task. I will be pruning your store-expense database, your overall transactions, your expenses database and you budgets.")
    print("This is irreversible, and will result in any reference to that expense being reverted to 'Misc'.")
    print("Any budget amnt for that expense will be added to Misc to maintain balance in the force.")
    exp_to_rem = util.select_from_list(exp_data[env.EXPENSE_DATA_KEY], "Which expense would you like to go? 'q' to abort: ", 
                                       abortchar='q', ret_match=True)
    if exp_to_rem != env.EXPENSE_MISC_STR:
        if exp_to_rem != None: # none comes if user aborts
             # delete from exp_stor db
            print(f"--- Editing {env.EXP_STOR_DB_FNAME} --- ")
            for store in exp_stor_data.keys():
                if exp_to_rem in exp_stor_data[store]:
                    exp_stor_data[store].remove(exp_to_rem)
                    print(f"Removed {exp_to_rem} from {store}.")
            
            
            # delete from expenses db
            print(f"--- Editing {env.EXP_FNAME} --- ")
            exp_data[env.EXPENSE_DATA_KEY].remove(exp_to_rem) 
            

            # remove from budget, adding amnt to Misc
            print(f"\n--- Editing {env.BUDGET_FNAME} --- ")
            for date in budg_data.keys(): 
                amnt_to_misc = budg_data[date][exp_to_rem]
                budg_data[date][env.EXPENSE_MISC_STR] += amnt_to_misc
                budg_data[date].pop(exp_to_rem)

            print(f"--- Editing {env.OUT_EXP_DATA_TEMPL} --- ")
            edit_df_entries(df, exp_db_data_filepath, env.EXPENSE, exp_to_rem, env.EXPENSE_MISC_STR)
            # write changes
            data_help.write_to_jsonFile(budg_path, budg_data)
            data_help.write_to_jsonFile(exp_path, exp_data)
            data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)
            
    else:
        print(f"'{env.EXPENSE_MISC_STR}' is a reserved expense category, and it cannot be deleted.")

def edit_cell_in_dfcol(db_data_filepath : str, df, col_name, opt_col, opt_dict):
    """
    Edits a single cell in the df based upon options provided in opt_dict
    params:
        db_data_filepath - the path to the dataframes csv data
        df - (DataFrame) object
        col_name - the column to set the new value of
        opt_col - the column to grab a key from to search opt_dict for the list of options
        opt_dict - the dictionary containing the pairs between keys and options for a key
    """
    index_list = df.index.tolist()
    print(df)
    prompt = "Select some indices from the above dataframe to edit: (q) to quit: "
    indices = util.select_indices_of_list(prompt, index_list, return_matches=True, abortable=True, abortchar='q', print_lst=False)
    if indices != None:
        for index in indices:
            opt_key = df.loc[index, opt_col]
            option = util.select_from_list(opt_dict[opt_key], f"Please select an option for cell [{index}] col '{col_name}' or (q) to quit: ", abortchar='q', ret_match=True)
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
            exp_stor_data[exp_stor_data_keylist[idx]].append(expense)
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

def budget_editor(budg_path):
    """
    Allows user to play around with the budget database
    """
    done = False 
    
    prompt = "Would you like to \n(a) - change budget amounts\n(q) - quit?\nType here: "
    while not done:
        budg_data = data_help.read_jsonFile(budg_path)
        print(env.OUTPUT_SEP_STR)
        user_in = util.get_user_input_for_chars(prompt, ['a', 'q'])
        if user_in == 'a':
            change_budget_amounts(budg_data, budg_path)
        elif user_in == 'q':
            done = True


def change_budget_amounts(budg_data, budg_path):
    """
    Changes budget amounts selected by the user
    """
    print(env.OUTPUT_SEP_STR)
    prompt = "Which budget month would you like to edit eh? (q) to abort: "
    dates = util.select_indices_of_list(prompt, list(budg_data.keys()), return_matches=True, abortable=True, abortchar='q')
    if dates is not None: # none type returned if user aborts
        for date in dates:
            print(f"--- Editing {date} ---")
            util.print_simple_dict(budg_data[date])
            expenses = util.select_indices_of_list("Select an expense(s). (q) to abort: ", list(budg_data[date].keys()), return_matches=True, abortable=True, abortchar='q', print_lst=False)
            if expenses is not None: # quit if user says so.
                for exp in expenses:
                    amnt = util.get_float_input(f"Enter the new amount for '{exp}': ", force_pos=True, roundto=2)
                    budg_data[date][exp] = amnt
            else:
                return 
        
        data_help.write_to_jsonFile(budg_path, budg_data)
            
            
    

def set_dict_keys_to_lowercase(dct_path):
    """
    Function I wrote just to run on the stores exp database to keep all stores lowercase.
    """
    dct = data_help.read_jsonFile(dct_path)
    for key in dct.keys():
        dct = data_help.modify_dict_key(dct, key, key.lower())
    data_help.write_to_jsonFile(dct_path, dct)
