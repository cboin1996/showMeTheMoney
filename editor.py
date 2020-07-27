import json
import os 
import pandas as pd

import util 
import data_help
import env
import expManager

def df_editor_menu(db_inc_data_fpaths, inc_recbin_path, db_exp_data_fpaths, exp_recbin_path):
    done = False
    while not done:
        df_user_in = util.get_user_input_for_chars("Which dataset:\n(a) - income\n(b) - expenses\n(c) - income recycle bin\n(d) - expenses recycle bin\n(q) - quit\nType here: ", ['a', 'b', 'c', 'd', 'q'])
        if df_user_in == 'a':
            df_editor(db_inc_data_fpaths[0], df_to_move_to_path=inc_recbin_path)
        elif df_user_in == 'b':
            df_editor(db_exp_data_fpaths[0], df_to_move_to_path=exp_recbin_path)
        elif df_user_in == 'c':
            df_editor(inc_recbin_path, df_to_move_to_path=db_inc_data_fpaths[0], restorable=True) # function takes list of csvs as input
        elif df_user_in == 'd':
            df_editor(exp_recbin_path, df_to_move_to_path=db_exp_data_fpaths[0], restorable=True) 
        elif df_user_in == 'q':
            done = True

def df_editor(df_to_move_from_path, df_to_move_to_path = None, restorable=False, recycle=True):
    """
    Allows the editing of a dataframe
    params:
        df_filepaths - the dataframe file paths to edit
        recbin_path - the recyclebin path (default None) if None, do not recycle
        restorable - whether or not the df is restorable
        recycle - whether or not data deleted from a frame will be moved to anotehr or lost
    """
    done = False
    while not done:
        df_to_move_from = data_help.load_csv(df_to_move_from_path, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)
        if df_to_move_to_path is not None:
            df_to_move_to = data_help.load_csv(df_to_move_to_path, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)

        if restorable == False:
            prompt = "Whould you like to: \n(a) - move transactions to the recycle bin\n(q) - quit\nType here: "
            input_chars = ['a', 'q']
        else:
            prompt = "Whould you like to: \n(a) - delete a row from the recycle bin\n(b) - restore from recycling\n(q) - quit\nType here: "
            recycle = False # if user is in recycle bin, deleting removes permanently
            input_chars = ['a', 'b', 'q']

        user_in = util.get_user_input_for_chars(prompt, input_chars)

        if user_in ==  'a':
            df_swap("Which rows? (q) to abort? ", df_to_move_from, df_to_move_to, df_to_move_from_path, df_to_move_to_path, recycle=recycle)
                    
        elif user_in == 'b':
            df_swap("Which row or rows would you like to restore (q) to abort? ", df_to_move_from, df_to_move_to, df_to_move_from_path, df_to_move_to_path, recycle=True)

        elif user_in == 'q':
            done = True

def df_swap(prompt, df_to_move_from, df_to_move_to, df_to_move_from_path, df_to_move_to_path, recycle=True):
    util.print_fulldf(df_to_move_from)
    rows = util.select_indices_of_list(prompt, list(df_to_move_from.index), abortable=True, abortchar='q', print_lst=False)
    if rows is not None: # above returns none if user aborts
        if recycle == True: # if recycle bin is wanted, perform the move between dataframes
            df_to_move_from, df_to_move_to = data_help.locate_and_move_data_between_dfs(df_to_move_from, rows, df_to_move_to)
            data_help.write_data(df_to_move_to, df_to_move_to_path, sortby=env.DATE)
            
        else: # drop and dont recycle
            df_to_move_from.drop(index=rows, inplace=True)

        data_help.write_data(df_to_move_from, df_to_move_from_path, sortby=env.DATE)

def store_editor(exp_db_data_filepaths, stor_pair_path, exp_stor_data_path, budg_path, exp_path):
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
        exp_data = data_help.read_jsonFile(exp_path)
        budg_db = data_help.read_jsonFile(budg_path)

        prompt = "Would you like to: \n(a) - change a storename\n(b) - edit bank to database store relationships\n(q) - quit\ntype here: "
        user_in = util.get_user_input_for_chars(prompt, ['a', 'b', 'q'])

        if user_in == 'a':
            change_storename(exp_db_data_filepaths, df, exp_stor_data, stor_data, stor_pair_path, exp_stor_data_path)
        elif user_in == 'b':
            change_storepair(exp_db_data_filepaths, df, exp_stor_data, stor_data, stor_pair_path, exp_stor_data_path, exp_data, budg_db)
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

def change_storepair(exp_db_data_filepaths, df, exp_stor_data, stor_data, stor_pair_path, exp_stor_data_path, exp_data, budg_db):
    """
    Allows user to change the pairing setup within stor_data, opting for the creation of a new store, or the repairing to a different store name
    """
    bank_storename = util.select_dict_key_using_integer(stor_data, 'Please select your banks storename to change, (q) to quit: ', print_children=False, quit_str='q')
    
    if bank_storename != None:
        print(f"\nYou currently have [{bank_storename}] paired with [{stor_data[bank_storename]}].")
        user_in = util.get_user_input_for_chars(f"\nDo you want to:\n(a) - re-pair [{bank_storename}] to an existing store you setup\n(b) - re-pair [{bank_storename}] to a new store name?\n(q) quit\nType here: ",
                                                ['a', 'b', 'q'])
        if user_in == 'a':
            new_pairing = util.select_from_list(list(exp_stor_data.keys()), f"\nPlease select a store to pair [{bank_storename}] to, or 'q' to quit: ", abortchar='q', ret_match=True)
        
        elif user_in == 'b':
            new_pairing = util.process_input(f"\nPlease input your new storename to be used with [{bank_storename}]: ")
            exp_stor_data[new_pairing] = [] # add new storename to exp_stor_data

        elif user_in == 'q':
            new_pairing = None
        
        if new_pairing is not None: # None type indicates user quit 
            stor_data[bank_storename] = new_pairing # set the new pairing into the stor_db
            print(f"Searching your transactions for any old references to [{bank_storename}]")
            df_to_walk = df[df[env.BANK_STORENAME].str.contains(bank_storename, case=False, regex=False)] # ignore case
            if df_to_walk.empty:
                print("No data to change in your transactions.")
            else:
                print("\nFound the below data to change.\n")
                util.print_fulldf(df_to_walk)
                for idx, row in df_to_walk.iterrows():
                    print("Curr Transaction:  %-10s | %-10s | %-10s | %-10s" % (row[env.DATE], row[env.AMOUNT], row[env.BANK_STORENAME], row[env.TYPE]))
                    month_end_date = util.get_month_from_timestamp(row[env.DATE], start=False) # get relevant expenses for that month set by the user.
                    selected_exp, exp_stor_data, stor_data, storename = expManager.search_store_relationships(new_pairing, exp_stor_data, budg_db[month_end_date], 
                                                                        exp_stor_data_path, stor_data, stor_pair_path) # take the new pairing and pass into this func to get expense out the other end.
                    df.at[idx, env.FILT_STORENAME] = storename
                    df.at[idx, env.EXPENSE] = selected_exp  
        
                data_help.write_data(df, exp_db_data_filepaths[0])
            
            data_help.write_to_jsonFile(stor_pair_path, stor_data) 
            util.print_fulldf(df)
            
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

        prompt_pt1 = "Would you like to:\n(a) - add an expense\n(b) - edit an expenses name\n(c) - pair expenses to stores\n"
        prompt_pt2 = "(d) - delete an expense **CAUTION**\n(e) - edit an expense within your database\n(f) - unpair an expense from stores\n(q) - quit editor\ntype here: "
        user_in = util.get_user_input_for_chars(prompt_pt1+prompt_pt2, ['a', 'b', 'c', 'd', 'e', 'f', 'q', 's'])

        if user_in == 'a':
            add_expense(exp_data, exp_stor_data, exp_path, exp_stor_data_path)
        elif user_in == 'b': # TODO
            edit_expense_name(exp_db_data_filepaths[0], df, exp_data, budg_data, exp_stor_data, exp_path, budg_path, exp_stor_data_path)
        elif user_in == 'c':
            pair_prompt = "Enter the expenses you want to add to store, separated by a space.. (q) to abort: "
            expenses = util.select_indices_of_list(pair_prompt, exp_data[env.EXPENSE_DATA_KEY], return_matches=True, abortable=True, abortchar='q')
            if expenses != None:
                add_expenses_to_store(exp_stor_data, exp_stor_data_path, expenses)
        elif user_in == 'd':
            remove_expense_from_dbs(exp_db_data_filepaths[0], exp_stor_data, exp_data, budg_data, df, exp_stor_data_path, budg_path, exp_path)
        elif user_in == 'e':
            edit_cell_in_dfcol(exp_db_data_filepaths[0], df, col_name=env.EXPENSE, opt_col=env.FILT_STORENAME, opt_dict=exp_stor_data)
        elif user_in == 'f':
            remove_exp_from_store(exp_db_data_filepaths[0], df, exp_stor_data, exp_stor_data_path)
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
                add_expenses_to_store(exp_stor_data, exp_stor_data_path, list(exp_input))

            else:
                flag = True
        else:
            print(f"That expense already exists! Try another one. Heres the list of existing expenses: {exp_data[env.EXPENSE_DATA_KEY]}")

def add_expenses_to_store(exp_stor_data, exp_stor_data_path, expenses):
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
            for expense in expenses:
                if expense not in exp_stor_data[exp_stor_data_keylist[idx]]:
                    exp_stor_data[exp_stor_data_keylist[idx]].append(expense)
                    print(f"Added '{expense}' to '{exp_stor_data_keylist[idx]}'")
                else:
                    print(f"Ignoring addition! '{expense}' already is in '{exp_stor_data_keylist[idx]}'")
        data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)

def remove_exp_from_store(df_path, df, exp_stor_data, exp_stor_data_path):
    """
    Removes an expense from exp_stor_data dict, replacing the reference with user selection or misc in the dataframe
    """
    exp_stor_keyslist = list(exp_stor_data.keys())
    exp_stor_keyslist.sort()
    prompt = "Select which store(s) you wish to remove expense(s) from. (q) to abort."
    storenames = util.select_indices_of_list(prompt, exp_stor_keyslist, return_matches=True, abortable=True, abortchar='q')
    if storenames is not None:
        for storename in storenames:
            removed_expenses = util.select_indices_of_list("Select which expense(s) to remove. (q) to abort.", exp_stor_data[storename], return_matches=True, abortable=True, abortchar='q')
            if removed_expenses is not None:
                print(f"--- Editing {env.EXP_STOR_DB_FNAME} --- ")
                for expense in removed_expenses:
                    exp_stor_data[storename].remove(expense)
                    print(f"Removed {expense} from {storename}.")
                
                if len(exp_stor_data[storename]) == 0: # if all was deleted, append misc into this store.
                    print(f"You deleted all expenses from {storename}, I am adding {env.EXPENSE_MISC_STR} to preserve your data.")
                    exp_stor_data[storename].append(env.EXPENSE_MISC_STR)
                    new_exp = env.EXPENSE_MISC_STR

                print(f"--- Editing {env.OUT_EXP_DATA_TEMPL} --- ")
                for rem_exp in removed_expenses:
                    if len(exp_stor_data[storename]) == 1:
                        print(f"Only expense left for '{storename}' is '{exp_stor_data[storename][0]}'. Replacing '{rem_exp}' with '{exp_stor_data[storename][0]}'.")
                        new_exp = exp_stor_data[storename][0]
                    else:

                        new_exp = util.select_from_list(exp_stor_data[storename], f"Which expense do you want to use to replace '{rem_exp}' in '{storename}'? (q) to quit. ", abortchar='q',
                                                        ret_match=True)
                        if new_exp is None: # user quits
                            return None 
                        
                    edit_df_entries_given_columns(df, df_path, env.EXPENSE, env.FILT_STORENAME, storename, rem_exp, new_exp)
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

def edit_df_entries_given_columns(df, df_path, col_to_change, col_to_match, match_key, old_entry, new_entry):
    """
    Find entries in col_to_match and replaces the values in col_to_change from old_entry to new_entry
    """
    if not df.loc[(df[col_to_match] == match_key) & (df[col_to_change] == old_entry)].empty:
        df.loc[(df[col_to_match] == match_key) & (df[col_to_change] == old_entry), col_to_change] = new_entry
        data_help.write_data(df, df_path)
    else:
        print("No records matched in dataframe, left it alone.")

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
