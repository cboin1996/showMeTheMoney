import json
import os 
import pandas as pd
import numpy as np

import util 
import data_help
import env
import expManager

def notes_editor(db_exp_data_fpaths, db_inc_data_fpaths, notes_path,  bankconfig=None):
    """
    Main menu for editing notes
    """
    done = False
    while not done:
        exp_df = data_help.load_csvs(db_exp_data_fpaths, dtype=bankconfig.exp_dtypes, parse_dates=env.pdates_colname)
        inc_df = data_help.load_csvs(db_inc_data_fpaths, dtype=bankconfig.inc_dtypes, parse_dates=env.pdates_colname)
        notes_dict = data_help.read_jsonFile(notes_path)

        exp_months = data_help.extract_months(exp_df[env.DATE], start=False)
        inc_months = data_help.extract_months(inc_df[env.DATE], start=False)
        months_in_data = util.add_set_to_set(exp_months, inc_months, sort=True)
        
        if notes_dict == {}:
            prompt = "You have not entered any notes yet. Which month(s) would you like to add notes for? "
            edit_prompt_base = "Please enter your note below for month "

        else:
            prompt = "Please select a month to edit : "
            edit_prompt_base = "Edit your note below for month "
        
        sel_months = util.select_indices_of_list(prompt, list_to_compare_to=months_in_data, return_matches=True, abortchar='q')
        
        if sel_months is not None:
            notes = edit_notes(edit_prompt_base, notes_dict, sel_months, notes_path)
            
        else:
            done = True
            
        
def edit_notes(prompt, notes, months, notes_path):
    """
    Editing notes method
    params:
        prompt: Output prompt to user
        notes - the notes object
        notes_path - the path to the notes object
        months - the months given for editing or adding notes to
        notes_path - path to notes file
    """
    for month in months:
        if month in notes.keys():
            editable = notes[month]
        else:
            editable = ""
        note = util.get_editable_input(prompt + f"[{month}], or ctrl-c to quit process. " + "Tip: use (\\n) to denote new lines for plotting: ", editable=editable)
        if note is not None: # note is None type upon quit
            notes[month] = note
            data_help.write_to_jsonFile(notes_path, notes)
        else:
            return None
        
    return notes


def store_editor(db_exp_data_fpaths, db_exprec_data_fpath, stor_pair_path, exp_stor_data_path, budg_path, exp_path, bankconfig=None):
    """
    Edits a store's name across all databases.
    params:
        db_exp_data_fpaths - filepaths to expense csv's
        stor_pair_path - filepath to store name database
        exp_stor_data_path - filepath to store-expense data base
        budg_path - filepath to budget database
    """
    
    done = False
    while not done:
        df = data_help.load_csvs(db_exp_data_fpaths, dtype=bankconfig.exp_dtypes, parse_dates=env.pdates_colname)
        df_rec = data_help.load_csv(db_exprec_data_fpath, dtype=bankconfig.exp_dtypes, parse_dates=env.pdates_colname)
        stor_data = data_help.read_jsonFile(stor_pair_path)
        exp_stor_data = data_help.read_jsonFile(exp_stor_data_path)
        exp_data = data_help.read_jsonFile(exp_path)
        budg_db = data_help.read_jsonFile(budg_path)

        prompt = "Would you like to: \n(a) - change storenames\n(b) - edit bank to database store relationships\n(q) - quit\ntype here: "
        user_in = util.get_user_input_for_chars(prompt, ['a', 'b', 'q'])

        if user_in == 'a':
            change_storename(db_exp_data_fpaths, df, db_exprec_data_fpath, df_rec, exp_stor_data, stor_data, stor_pair_path, exp_stor_data_path)
        elif user_in == 'b':
            change_storepair(db_exp_data_fpaths, df, db_exprec_data_fpath, df_rec, exp_stor_data, stor_data, stor_pair_path, exp_stor_data_path, exp_data, budg_db)
        elif user_in == 'q':
            done = True
    return

def change_storename(db_exp_data_fpaths, df, db_exprec_data_fpath, df_rec, exp_stor_data, stor_data, stor_pair_path, exp_stor_data_path):
    storenames = util.select_dict_keys_using_integer(exp_stor_data, 'Please select storename(s) to change: ', print_children=False, quit_str='q')
    if storenames != None: # select_dict_key_using_integer returns none if quitstr is given
        for storename in storenames:
            new_name = util.prompt_with_warning(f"Please enter your new storename for [{storename}]: ", ret_lowercase=True)
            if new_name != None: # none is returned from prompt_with_warning when user wants to abort.
                print(f"--- Editing {env.OUT_EXP_DATA_TEMPL} --- ")
                edit_df_entries(df, db_exp_data_fpaths[0], env.FILT_STORENAME, storename, new_name)
                print(f"--- Editing {env.OUT_EXPREC_DATA_TEMPL} --- ")
                edit_df_entries(df_rec, db_exprec_data_fpath, env.FILT_STORENAME, storename, new_name)
                print(f"--- Editing {env.STORE_PAIR_FNAME} --- ")
                stor_data = data_help.match_mod_dict_vals(stor_data, storename, new_name)
                data_help.write_to_jsonFile(stor_pair_path, stor_data)
                print(f"--- Editing {env.EXP_STOR_DB_FNAME} --- ")
                exp_stor_data = data_help.modify_dict_key(exp_stor_data, storename, new_name)
                data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)

def change_storepair(db_exp_data_fpaths, df, db_exprec_data_fpath, df_rec, exp_stor_data, 
                    stor_data, stor_pair_path, exp_stor_data_path, exp_data, budg_db):
    """
    Allows user to change the pairing setup within stor_data, opting for the creation of a new store, or the repairing to a different store name
    """
    bank_storenames = util.select_dict_keys_using_integer(stor_data, 'Please select your bank storename(s) to change its pairing, ', 
                                                        print_children=False, quit_str='q', print_vals=True)
    
    if bank_storenames != None:
        for bank_storename in bank_storenames:
            user_in = util.get_user_input_for_chars(f"\nDo you want to:\n(a) - re-pair [{bank_storename}] to an existing store you setup\n(b) - re-pair [{bank_storename}] to a new store name?\n(q) quit\nType here: ",
                                                    ['a', 'b', 'q'])
            if user_in == 'a':
                stor_exp_keys = list(exp_stor_data.keys())
                stor_exp_keys.sort()
                new_pairing = util.select_from_list(stor_exp_keys, f"\nPlease select a store to pair [{bank_storename}] to, or 'q' to quit: ", abortchar='q', ret_match=True)
            
            elif user_in == 'b':
                new_pairing = util.process_input(f"\nPlease input your new storename to be used with [{bank_storename}]: ")
                exp_stor_data[new_pairing] = [] # add new storename to exp_stor_data

            elif user_in == 'q':
                new_pairing = None
            
            if new_pairing is not None: # None type indicates user quit 
                stor_data[bank_storename] = new_pairing # set the new pairing into the stor_db
                prompt = f"Searching {db_exp_data_fpaths[0]} for any old references to [{bank_storename}]."
                replace_store_in_df(prompt, df, db_exp_data_fpaths[0], new_pairing, exp_stor_data, 
                                    budg_db, exp_stor_data_path, stor_data, stor_pair_path, bank_storename)
                prompt = f"Searching {db_exprec_data_fpath} for any old references to [{bank_storename}]."
                replace_store_in_df(prompt, df_rec, db_exprec_data_fpath, new_pairing, exp_stor_data, 
                                        budg_db, exp_stor_data_path, stor_data, stor_pair_path, bank_storename)

                data_help.write_to_jsonFile(stor_pair_path, stor_data) 
            

def replace_store_in_df(prompt, df, df_path, new_pairing, exp_stor_data, budg_db, 
                        exp_stor_data_path, stor_data, stor_pair_path, bank_storename):
    print(prompt)
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

        data_help.write_data(df, df_path)
        util.print_fulldf(df)
def expenses_editor(db_exp_data_fpaths, exp_recbin_path, stor_pair_path, exp_stor_data_path, budg_path, exp_path, bankconfig=None):
    """
    Edits an expense's name across all databases
    """
    done = False
    while not done:
        exp_data = data_help.read_jsonFile(exp_path)
        df_rec = data_help.load_csv(exp_recbin_path, dtype=bankconfig.exp_dtypes, parse_dates=env.pdates_colname)
        df = data_help.load_csvs(db_exp_data_fpaths, dtype=bankconfig.exp_dtypes, parse_dates=env.pdates_colname)
        stor_data = data_help.read_jsonFile(stor_pair_path)
        exp_stor_data = data_help.read_jsonFile(exp_stor_data_path)
        budg_data = data_help.read_jsonFile(budg_path)

        prompt = "\n".join(("Would you like to:", 
                            "(a) - add an expense", 
                            "(b) - edit an expenses name", 
                            "(c) - pair expenses to stores", 
                            "(d) - delete an expense **CAUTION**", 
                            "(e) - edit an expense within your database", 
                            "(f) - unpair an expense from stores", 
                            "(g) - add expense to be subtracted in plot title",
                            "(h) - remove expense to be subtracted in plot title",
                            "(q) - quit editor", 
                            "type here: "))
        user_in = util.get_user_input_for_chars(prompt, ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'q', 's'])

        if user_in == 'a':
            add_expense(exp_data, exp_stor_data, exp_path, exp_stor_data_path)
        elif user_in == 'b': # TODO
            edit_expense_name(db_exp_data_fpaths[0], df, exp_recbin_path, df_rec, exp_data, budg_data, exp_stor_data, exp_path, budg_path, exp_stor_data_path)
        elif user_in == 'c':
            pair_prompt = "Enter the expenses you want to add to store, separated by a space.. (q) to abort: "
            expenses = util.select_indices_of_list(pair_prompt, exp_data[env.EXPENSE_DATA_KEY], return_matches=True, abortchar='q')
            if expenses != None:
                add_expenses_to_store(exp_stor_data, exp_stor_data_path, expenses)
        elif user_in == 'd':
            remove_expense_from_dbs(db_exp_data_fpaths[0], exp_recbin_path, exp_stor_data, exp_data, budg_data, df, df_rec, exp_stor_data_path, budg_path, exp_path)
        elif user_in == 'e':
            edit_cell_in_dfcol(db_exp_data_fpaths[0], df, col_name=env.EXPENSE, opt_col=env.FILT_STORENAME, opt_dict=exp_stor_data)
        elif user_in == 'f':
            remove_exp_from_store(db_exp_data_fpaths[0], df, exp_recbin_path, df_rec, exp_stor_data, exp_stor_data_path)
        elif user_in =='g':
            prompt = "Which expense(s) would you like to be subtracted in the title to your plots? "
            util.edit_list_in_dict(prompt, exp_data[env.EXPENSE_DATA_KEY], exp_data, env.EXPENSES_SUBTRACTED_KEY, exp_path, add=True)
        elif user_in == 'h':
            prompt = "Which expense(s) would you like to remove? "
            util.edit_list_in_dict(prompt, exp_data[env.EXPENSES_SUBTRACTED_KEY], exp_data, env.EXPENSES_SUBTRACTED_KEY, exp_path, add=False) 
        elif user_in == 'q':
            done = True
        elif user_in == 's':
            print("Ah so youre an alchemist then.")
            sync_expenses(exp_data, exp_stor_data, exp_path, exp_stor_data_path)

def edit_expense_name(exp_db_data_filepath, df, exp_recbin_path, df_rec, exp_data, budg_data, exp_stor_data, exp_path, budg_path, exp_stor_data_path):
    """
    Edits an expense name across storesWithExpenses.json, Budgjet.json, expenses.json, and exp_db.csv
    """
    exps_to_edit = util.select_indices_of_list("Which expense(s) would you like to edit?: ", exp_data[env.EXPENSE_DATA_KEY],
                                        abortchar='q', return_matches=True)
    if exps_to_edit is not None: # none type quits
        for exp_to_edit in exps_to_edit:
            if exp_to_edit != env.EXPENSE_MISC_STR:

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
                    # Edit exp_db.csv and (writes itself)
                    print(f"--- Editing {env.OUT_EXP_DATA_TEMPL} --- ")
                    edit_df_entries(df, exp_db_data_filepath, env.EXPENSE, exp_to_edit, expense_new_name)
                    print(f"--- Editing {env.OUT_EXPREC_DATA_TEMPL} --- ")
                    edit_df_entries(df_rec, exp_recbin_path, env.EXPENSE, exp_to_edit, expense_new_name)
                    # Write changes
                    data_help.write_to_jsonFile(budg_path, budg_data)
                    data_help.write_to_jsonFile(exp_path, exp_data)
                    data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)

            else:
                print(f"'{env.EXPENSE_MISC_STR}' is a reserved expense category, and its name cannot be changed.")

def remove_expense_from_dbs(exp_db_data_filepath, exp_recbin_path, exp_stor_data, exp_data, 
                            budg_data, df, df_rec, exp_stor_data_path, budg_path, exp_path): 
    """
    Removes an expense from the storesWithExpenses.json, Budgjet.json, expenses.json
    """
    print("Warning! Removing an expense is no small task. I will be pruning your store-expense database, your overall transactions, your expenses database and you budgets.")
    print("This is irreversible, and will result in any reference to that expense being reverted to 'Misc'.")
    print("Any budget amnt for that expense will be added to Misc to maintain balance in the force.")
    exps_to_rem = util.select_indices_of_list("Which expense(s) would you like to go? ", exp_data[env.EXPENSE_DATA_KEY], 
                                       abortchar='q', return_matches=True)
    if exps_to_rem is not None:
        for exp_to_rem in exps_to_rem:
            if exp_to_rem != env.EXPENSE_MISC_STR:

                # delete from exp_stor db
                print(f"--- Editing {env.EXP_STOR_DB_FNAME} --- ")
                for store in exp_stor_data.keys():
                    if exp_to_rem in exp_stor_data[store]:
                        exp_stor_data[store].remove(exp_to_rem)
                        print(f"Removed {exp_to_rem} from {store}.")
                
                
                # delete from expenses db
                print(f"--- Editing {env.EXP_FNAME} --- ")
                exp_data[env.EXPENSE_DATA_KEY].remove(exp_to_rem) 
                print(f"Removed {exp_to_rem} from {env.EXP_FNAME}.")
                

                # remove from budget, adding amnt to Misc
                print(f"\n--- Editing {env.BUDGET_FNAME} --- ")
                for date in budg_data.keys(): 
                    if exp_to_rem in budg_data[date].keys():
                        amnt_to_misc = budg_data[date][exp_to_rem]
                        budg_data[date][env.EXPENSE_MISC_STR] += amnt_to_misc
                        budg_data[date].pop(exp_to_rem)
                    else:
                        print("No expense in this months budget.")

                print(f"--- Editing {env.OUT_EXP_DATA_TEMPL} --- ")
                edit_df_entries(df, exp_db_data_filepath, env.EXPENSE, exp_to_rem, env.EXPENSE_MISC_STR)
                print(f"--- Editing {env.OUT_EXPREC_DATA_TEMPL} --- ")
                edit_df_entries(df_rec, exp_recbin_path, env.EXPENSE, exp_to_rem, env.EXPENSE_MISC_STR)
                # write changes
                data_help.write_to_jsonFile(budg_path, budg_data)
                data_help.write_to_jsonFile(exp_path, exp_data)
                data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)
                    
            else:
                print(f"'{env.EXPENSE_MISC_STR}' is a reserved expense category, and it cannot be deleted.")

def edit_cell_in_dfcol(db_data_filepath : str, df, col_name, opt_col=None, opt_dict=None, col_type=None):
    """
    Edits a single cell in the df based upon options provided in opt_dict
    params:
        db_data_filepath - the path to the dataframes csv data
        df - (DataFrame) object
        col_name - the column to set the new value of
        opt_col - the column to grab a key from to search opt_dict for the list of options. If none, user can edit cell manually with input
        opt_dict - the dictionary containing the pairs between keys and options for a key
        col_type - the columns type to check for on user inputs
    """
    index_list = df.index.tolist()
    util.print_fulldf(df)
    prompt = f"Select some indices from the above dataframe column '{col_name}' to edit: : "
    indices = util.select_indices_of_list(prompt, index_list, return_matches=True, abortchar='q', print_lst=False)
    if indices != None:
        for index in indices:
            if opt_col != None:
                opt_key = df.loc[index, opt_col]
                val = util.select_from_list(opt_dict[opt_key], f"Please select an option for cell [{index}] col '{col_name}' or (q) to quit: ", abortchar='q', ret_match=True)
            
            else:
                if col_type == 'float':
                    val = util.get_float_input(f"Please input ({col_type}) for this entry at row [{index}] col [{col_name}]: ", force_pos=False, roundto=2)

            
            if val != None: # nonetype aborts
                df.at[index, col_name] = val
                data_help.write_data(df, db_data_filepath)
            
            else:
                 break


def add_expense(exp_data, exp_stor_data, exp_path, exp_stor_data_path):
    """
    Adds an expense to the expense database
    """
    flag = False 
    while not flag:
        exps = util.format_input_to_list("Enter the expenses you wish to add: ", mode='string', quit_str='q')
        if exps != None:
            for exp in exps:
                if exp not in exp_data[env.EXPENSE_DATA_KEY]:
                    exp_data[env.EXPENSE_DATA_KEY].append(exp)
                    data_help.write_to_jsonFile(exp_path, exp_data)

                    user_in = util.get_user_input_for_chars(f"Do you want to add expense [{exp}] expense to some stores [y/n]? ", ['y', 'n'])
                    if user_in == 'y':
                        add_expenses_to_store(exp_stor_data, exp_stor_data_path, [exp])

                    else:
                        flag = True
                else:
                    print(f"That expense already exists! Try another one. Heres the list of existing expenses: {exp_data[env.EXPENSE_DATA_KEY]}")
        else:
            flag = True

def add_expenses_to_store(exp_stor_data, exp_stor_data_path, expenses):
    """
    Adds an expense to a store within storesWithExpenses.json
    params:
        exp_stor_data : the dict object of storesWithExpenses.json
        exp_stor_data_keylist : the list of keys of exp_stor_data
        expense : the expense to add to the store selected by the user
    """
    stores = util.select_dict_keys_using_integer(exp_stor_data, "Select a store to add this expense to.", print_children=False, quit_str='q', print_aborting=True, print_vals=True)
    if stores != None:
        for store in stores:
            for expense in expenses:
                if expense not in exp_stor_data[store]:
                    exp_stor_data[store].append(expense)
                    print(f"Added '{expense}' to '{store}'")
                else:
                    print(f"Ignoring addition! '{expense}' already is in '{store}'")
        data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)

def remove_exp_from_store(df_path, df, exp_recbin_path, df_rec, exp_stor_data, exp_stor_data_path):
    """
    Removes an expense from exp_stor_data dict, replacing the reference with user selection or misc in the dataframe
    """
    prompt = "Select which store you wish to remove expense(s) from. (q) to abort."
    storenames = util.select_dict_keys_using_integer(exp_stor_data, prompt, print_children=False, quit_str='q', print_aborting=True, print_vals=True)
    if storenames is not None:
        for storename in storenames:
            removed_expenses = util.select_indices_of_list("Select which expense(s) to remove. (q) to abort.", exp_stor_data[storename], return_matches=True, abortchar='q')
            if removed_expenses is not None:
                print(f"--- Editing {env.EXP_STOR_DB_FNAME} --- ")
                for expense in removed_expenses:
                    exp_stor_data[storename].remove(expense)
                    print(f"Removed {expense} from {storename}.")
                
                if len(exp_stor_data[storename]) == 0: # if all was deleted, append misc into this store.
                    print(f"You deleted all expenses from {storename}, I am adding {env.EXPENSE_MISC_STR} to preserve your data.")
                    exp_stor_data[storename].append(env.EXPENSE_MISC_STR)
                    new_exp = env.EXPENSE_MISC_STR

                print(f"--- Editing {env.OUT_EXP_DATA_TEMPL} & {env.OUT_EXPREC_DATA_TEMPL} --- ")
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
                    edit_df_entries_given_columns(df_rec, exp_recbin_path, env.EXPENSE, env.FILT_STORENAME, storename, rem_exp, new_exp)

                data_help.write_to_jsonFile(exp_stor_data_path, exp_stor_data)

def df_editor_menu(db_inc_data_fpaths, inc_recbin_path, db_exp_data_fpaths, exp_recbin_path, bankconfig=None):
    done = False
    while not done:
        prompt = "Which one:\n(a) - income\n(b) - expenses\n(c) - income recycle bin\n"
        prompt = prompt + "(d) - expenses recycle bin\n(q) - quit\nType here: "
        df_user_in = util.get_user_input_for_chars(prompt, ['a', 'b', 'c', 'd', 'q'])
        if df_user_in == 'a':
            df_editor(db_inc_data_fpaths[0], df_to_move_to_path=inc_recbin_path, 
                      df_with_reductions_path=db_exp_data_fpaths[0], df_to_move_reduction_to_path=exp_recbin_path, 
                      uuid_col=env.INC_UUID, df_reduct_uuid_col=env.EXP_UUID, bankconfig=bankconfig, dtype='inc')
        elif df_user_in == 'b':
            df_editor(db_exp_data_fpaths[0], df_to_move_to_path=exp_recbin_path, 
                      df_with_reductions_path=db_inc_data_fpaths[0], df_to_move_reduction_to_path=inc_recbin_path, 
                      uuid_col=env.EXP_UUID, df_reduct_uuid_col=env.INC_UUID, bankconfig=bankconfig, dtype='exp')
        elif df_user_in == 'c':
            df_editor(inc_recbin_path, df_to_move_to_path=db_inc_data_fpaths[0], restorable=True, 
                      df_with_reductions_path=db_exp_data_fpaths[0], df_reduct_uuid_col=env.EXP_UUID, bankconfig=bankconfig,
                      dtype='inc') # function takes list of csvs as input
        elif df_user_in == 'd':
            df_editor(exp_recbin_path, df_to_move_to_path=db_exp_data_fpaths[0], restorable=True, 
                     df_with_reductions_path=db_inc_data_fpaths[0], df_reduct_uuid_col=env.INC_UUID, bankconfig=bankconfig,
                     dtype='exp') 
        elif df_user_in == 'q':
            done = True

def df_editor(df_to_move_from_path, df_to_move_to_path = None, restorable=False, recycle=True, df_with_reductions_path=None,  
              df_to_move_reduction_to_path=None, uuid_col=None, df_reduct_uuid_col=None, bankconfig=None, dtype=None):
    """
    Allows the editing of a dataframe
    params:
        df_to_move_from_path - the dataframe file paths to edit
        df_to_move_to_path - the recyclebin path (default None)
        restorable - whether or not the df is restorable, if True, will not recycle
        recycle - whether or not data deleted from a frame will be moved to another or lost
        df_with_reductions_path - the path to the dataframe containing prices to reduce df_to_move_from_path by
        dtype - specifies how the csv dataypes should be setup when loading.  
    """
    done = False
    if dtype == 'exp':
        dtype_move_from = bankconfig.exp_dtypes 
        dtype_move_to = bankconfig.exp_dtypes
        dtype_with_red = bankconfig.inc_dtypes
        dtype_move_red_to = bankconfig.inc_dtypes
    elif dtype == 'inc':
        dtype_move_from = bankconfig.inc_dtypes 
        dtype_move_to = bankconfig.inc_dtypes
        dtype_with_red = bankconfig.exp_dtypes
        dtype_move_red_to = bankconfig.exp_dtypes

    while not done:
        df_to_move_from = data_help.load_csv(df_to_move_from_path, dtype=dtype_move_from, parse_dates=env.pdates_colname)
        
        if df_to_move_to_path is not None:
            df_to_move_to = data_help.load_csv(df_to_move_to_path, dtype=dtype_move_to, parse_dates=env.pdates_colname)
        
        if df_with_reductions_path is not None:
            df_with_reductions = data_help.load_csv(df_with_reductions_path, dtype=dtype_with_red, parse_dates=env.pdates_colname)

        if df_to_move_reduction_to_path is not None:
            df_to_move_reduction_to = data_help.load_csv(df_to_move_reduction_to_path, dtype=dtype_move_red_to, parse_dates=env.pdates_colname)
        
        if restorable == False:
            prompt = "Would you like to: \n(a) - move transactions to the recycle bin\n(b) - adjust a transaction price manually\n"
            prompt = prompt + "(c) - reduce a transaction by another\n(q) - quit\nType here: "
            input_chars = ['a', 'b', 'c', 'q']
        else:
            prompt = "Would you like to: \n(a) - delete a row from the recycle bin\n(b) - restore from recycling\n(q) - quit\nType here: "
            recycle = False # if user is in recycle bin, deleting removes permanently
            input_chars = ['a', 'b', 'q']

        user_in = util.get_user_input_for_chars(prompt, input_chars)

        if user_in ==  'a' and recycle == True: # expenses or income case
            df_swap("Which rows would you like to recycle? (q) to abort? ", df_to_move_from, df_to_move_to, df_to_move_from_path, df_to_move_to_path)
        
        elif user_in == 'a' and recycle == False:
            df_to_move_from = data_help.drop_rows("Which rows would you like to delete? (q) to abort? ", df_to_move_from)
            if df_to_move_from is not None: # none type aborts
                data_help.write_data(df_to_move_from, df_to_move_from_path)

        elif user_in == 'b' and restorable == True:
            df_swap("Which row or rows would you like to restore (q) to abort? ", df_to_move_from, df_to_move_to, 
                    df_to_move_from_path, df_to_move_to_path, cross_check_df=df_with_reductions, cross_check_col=df_reduct_uuid_col, cross_check_df_path=df_with_reductions_path)
        
        elif user_in == 'b' and restorable == False:
            edit_cell_in_dfcol(df_to_move_from_path, df_to_move_from, col_name=env.ADJUSTMENT, col_type='float')
        
        elif user_in =='c' and restorable == False:
            edit_df_transaction_price(df_to_edit=df_to_move_from, df_to_edit_path=df_to_move_from_path, col_to_use=env.ADJUSTMENT, df_to_move_reduction_to=df_to_move_reduction_to, 
                                      df_to_move_reduction_to_path=df_to_move_reduction_to_path, df_with_reductions=df_with_reductions, df_with_reductions_path=df_with_reductions_path,
                                      reduction_col=env.AMOUNT, uuid_col=uuid_col, df_reduct_uuid_col=df_reduct_uuid_col)
  
        elif user_in == 'q':
            done = True

def edit_df_transaction_price(df_to_edit, df_to_edit_path, col_to_use, df_to_move_reduction_to, df_to_move_reduction_to_path, 
                              df_with_reductions, df_with_reductions_path, reduction_col, uuid_col=None, df_reduct_uuid_col=None):
    """
    params:
        df_to_edit - the dataframe to edit the price on
        col_to_use - the column across all dataframes to be using
        df_with_reductions - the dataframe carrying transaction values that can be inserted into df_to_edit
        df_to_move_reduction_to - the df that will take the reduction transaction from df_with_reductions
        reduction_col - the column to grab reduction value from
    """
    index_list = df_to_edit.index.tolist()
    util.print_fulldf(df_to_edit)
    prompt = f"Select some indices from the above dataframe column '{col_to_use}' to edit: : "
    indices = util.select_indices_of_list(prompt, index_list, return_matches=True, abortchar='q', print_lst=False)
    if indices is not None: # none type aborts
        for index in indices:
            reductions_index_list = df_with_reductions.index.tolist()
            util.print_fulldf(df_with_reductions)
            prompt = f"Which index contains the transaction you want? "
            reduction_indices = util.select_indices_of_list(prompt, reductions_index_list, abortchar='q', return_matches=False, print_lst=False)
            if reduction_indices is not None: # none type aborts
                for reduction_index in reduction_indices:
                    val = df_with_reductions.at[reduction_index,reduction_col] # get transaction val

                    if df_to_edit.at[index, col_to_use] == np.nan: # check for nan value
                        df_to_edit.at[index, col_to_use] = 0.0

                    df_with_reductions.at[reduction_index, uuid_col] = df_to_edit.at[index, uuid_col]
                    df_to_edit.at[index, col_to_use] = df_to_edit.at[index, col_to_use] + val
                df_swap(df_to_move_from=df_with_reductions, df_to_move_to=df_to_move_reduction_to, df_to_move_from_path=df_with_reductions_path,
                    df_to_move_to_path=df_to_move_reduction_to_path, rows=reduction_indices) # writes changes
            else:
                break
        
        data_help.write_data(df_to_edit, df_to_edit_path, sortby=env.DATE) # writes changes to the edited df.
    

            
def df_swap(prompt=None, df_to_move_from=None, df_to_move_to=None, df_to_move_from_path=None, df_to_move_to_path=None, rows=None,
            cross_check_df=None, cross_check_col=None, cross_check_df_path=None):
    """
    Performs a swap of data from one dataframe to another
    params
        prompt - the output to the user
        df_to_move_from - the dataframe to move rows from
        df_to_move_to - the dataframe to move the rows to
        rows - (default) None. If none, will prompt user, else will use the given rows to perform a swap.
        cross_check_df - perform a cross check on this dataframe for a value in cross_check_col and return matches
        cross_check_col - column to perform the cross check on
    """
    if rows is None:
        util.print_fulldf(df_to_move_from)
        rows = util.select_indices_of_list(prompt, list(df_to_move_from.index), abortchar='q', print_lst=False)
    if rows is not None: # above returns none if user aborts
        if cross_check_df is not None:
            data_help.check_for_match_in_rows(rows, df_to_move_from, env.AMOUNT, cross_check_df, cross_check_col, 
                                              cross_check_df_path, env.ADJUSTMENT)


        df_to_move_from, df_to_move_to = data_help.locate_and_move_data_between_dfs(df_to_move_from, rows, 
                                                                                    df_to_move_to, cross_check_col)
        data_help.write_data(df_to_move_to, df_to_move_to_path, sortby=env.DATE)
        data_help.write_data(df_to_move_from, df_to_move_from_path, sortby=env.DATE)
    
def edit_settings(settings_path):
    """
    Main interface for editing settings for the app
    """
    done = False 
    prompt = "Please select a setting to edit: "
    while not done:
        settings = data_help.read_jsonFile(settings_path)
        setting_sels = util.select_indices_of_list(prompt, list(settings.keys()), return_matches=True, abortchar=True, print_lst=True)
        for setting in setting_sels:
            data_type = type(settings[setting])
            value = util.get_input_given_type(f"Enter your '{data_type}' for {setting}={settings[setting]}. ", data_type, abortchar='q')
            if value is not None: # none type returned upon quit
                settings[setting] = value
                done = True
                data_help.write_to_jsonFile(settings_path, settings)

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
    done = False
    while not done:
        print(env.OUTPUT_SEP_STR)
        prompt = "Which budget month would you like to edit eh? (q) to abort: "
        dates = util.select_indices_of_list(prompt, list(budg_data.keys()), return_matches=True, abortchar='q')
        if dates is not None: # none type returned if user aborts
            for date in dates:
                print(f"--- Editing {date} ---")
                util.print_simple_dict(budg_data[date])
                expenses = util.select_indices_of_list("Select an expense(s). ", list(budg_data[date].keys()), return_matches=True, abortchar='q', print_lst=False)
                if expenses is not None: # quit if user says so.
                    for exp in expenses:
                        amnt = util.get_float_input(f"Enter the new amount for '{exp}': ", force_pos=True, roundto=2)
                        budg_data[date][exp] = amnt
                else:
                    continue 
            
            data_help.write_to_jsonFile(budg_path, budg_data)
        
        else:
            done=True
            
    

def set_dict_keys_to_lowercase(dct_path):
    """
    Function I wrote just to run on the stores exp database to keep all stores lowercase.
    """
    dct = data_help.read_jsonFile(dct_path)
    for key in dct.keys():
        dct = data_help.modify_dict_key(dct, key, key.lower())
    data_help.write_to_jsonFile(dct_path, dct)
