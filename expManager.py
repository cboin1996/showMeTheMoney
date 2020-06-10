import json
import os, sys 
import datetime
import re
import pandas as pd

import util
import env
import data_help

def setup_expense_names(exp_path: str):
    """
    Gets a list of expense names from the user and saves them.
    """
    exp_list = data_help.read_jsonFile(exp_path)
    if len(exp_list) == 0:
        exp_list[env.EXPENSE_DATA_KEY] = util.format_input_to_list("Please input your expense categories, separated by a space [exp1 exp2 ...]: ")
        data_help.write_to_jsonFile(exp_path, exp_list)

def add_budget_info(monthly_budget: dict):
    """
    Takes a previous months expense categories and allows user to set new budget parameters
    params:
        (dict) monthly_budjet: expenses linked to budget to be modified
    """
    pass 

def declare_new_budget(date, exp_data):
    """
    Sets up an entirely new budget with expense categories for that month
    """
    done_adding_budgets = False 
    exp_list  = exp_data[env.EXPENSE_DATA_KEY]
    local_budget = {}
    month_total = util.get_integer_input(f"Please input your total for the month starting {date}: ")
    budg_remaining = month_total

    for i, exp in enumerate(exp_list):
        if i == len(exp_list) - 1:
            print("I got the last one for you :) MATH!")
            budg_amnt = budg_remaining
            budg_remaining = 0

        elif budg_remaining == 0: # elif skips this condition if budget remaining is set above
            budg_amnt = 0
            local_budget[env.BUDGET_TOTAL_KEY] = month_total
        else:
            prompt = f"Enter your budget for: [{exp}] - Total Budget Re. ${budg_remaining}: "
            budg_amnt = prompt_for_budget_amnt(prompt, budg_remaining, exp_data)
        local_budget.update({exp:budg_amnt})
        budg_remaining = month_total - sum_budget(local_budget)
        print(local_budget)
    return local_budget

def prompt_for_budget_amnt(prompt, budg_remaining, exp_data):
    """
    Gathers a budget entry of str:float type from user input, ensuring it is not over the months totaL
    """
    print("Input your expense name and budget separated by a space (food 150)")
    flag = False 
    while not flag:
        budget_amnt = util.get_integer_input(prompt)

        if budget_amnt <= budg_remaining:
            flag = True
        else:
            print("Value you entered is over your total. Please try again.")

    return budget_amnt

def sum_budget(monthly_budget: dict):
    """
    Sums a budget dict to get the total budget amnt
    """
    sum = 0
    for k,v in monthly_budget.items():
        if v is not None and k != env.BUDGET_TOTAL_KEY:
            sum += v

    return sum



def get_budgets(budg_path, exp_path, dates=None):
    """
    Prompts user for budgeting options given a new month if no budget is present for that month
    """
    exp_budg = data_help.read_jsonFile(budg_path)
    exp_data = data_help.read_jsonFile(exp_path)
    if dates == None:
        dates = [util.get_current_month()]
    for date in dates:
        exp_budg_keys = exp_budg.keys()
        if date not in exp_budg_keys: # check for current month to find exp categories
            print(f"I have detected some data with for the month {date} that has no budget set.")
            print("Please set the budget for this month.. or delete the data and run the program again.")
            if len(exp_budg) != 0:
                user_in = util.get_user_input_for_chars("Would you like to the whole thing (w) or create new (n)? ", ['w', 'n'])

                if user_in == 'w':
                    key = util.select_dict_key_using_integer(exp_budg, "Please select a budget to copy: ")
                    exp_budg[date] = exp_budg[key]
                elif user_in == 'n':
                    exp_budg[date] = declare_new_budget(date, exp_data)
            else:
                exp_budg[date] = declare_new_budget(date, exp_data)
            
            print(f"Your budget is now saved for {date}.")
            
        else:
            print(f"Your monthly budget for {date} is: ")
        
        util.print_simple_dict(exp_budg[date])
    
    data_help.write_to_jsonFile(budg_path, exp_budg)
    return 

def get_expenses_for_rows(df, stor_exp_data_path, stor_data_path, budg_path):
    """
    Gets the expense data for stores, prompting the user when multiple expenses exist for a store
    params:
        df - pandas dataframe
        stor_exp_data_path - filepath to expensesDB
    """
    print("\nIterating your transactions.\n")

    exp_stor_db = data_help.read_jsonFile(stor_exp_data_path) # initialize the objects for tracking changes
    storDB = data_help.read_jsonFile(stor_data_path)
    exp_budg_db = data_help.read_jsonFile(budg_path)

    for idx, row in df.iterrows():
        if pd.isnull(row[env.EXPENSE]):
            month_start_date = util.get_month_from_timestamp(row[env.DATE]) # get relevant expenses for that month set by the user.
            if type(row[env.BANK_STORENAME]) is str:
                match = env.RE_EXPR.search(row[env.BANK_STORENAME])
                if match:
                    processed_text = util.process_text(match.group(0))
                    # print(f"Was able to filter - {row[env.BANK_STORENAME]} -> {processed_text}")
                    storename = processed_text
                        
                else:
                    print(f"Unable to filter - {row[env.BANK_STORENAME]}")
                    storename = row[env.BANK_STORENAME]
                
            else:
                query = row[env.TYPE].lower()
                print(query)
                storename = query
        else:
            print("Already have expense here heeheh")

        print("Curr Transaction:  %-10s %-10s %-10s %-10s" % (row[env.DATE], row[env.AMOUNT], storename, row[env.TYPE]))
        selected_exp, exp_stor_db = search_store_relationships(storename, exp_stor_db, exp_budg_db[month_start_date], stor_exp_data_path)
        df.at[idx, env.FILT_STORENAME] = processed_text
        df.at[idx, env.EXPENSE] = selected_exp  
    
    print(df)
    return df
    
def search_store_relationships(storename, exp_stor_db, exp_budg_db, stor_exp_data_path):

    """
    Searches the store expense relationship (exp_stor_db) for an expense and if multiple exist, prompts the user to select one.
    params:
        storename - a store's name from the dataframe
        exp_stor_db - a python dict containing stores as keys, and arrays of expenses as values
        exp_budg_db - expense budget dict database
        stor_exp_data_path - filepath to expensesDB 
    returns: the selected expense string, and the modified exp_stor_db
    """
    exp_stor_dbKeys = exp_stor_db.keys()
    if storename in exp_stor_dbKeys: # check if store is within the exp_stor_db
        exps_fr_store = exp_stor_db[storename]
        if len(exps_fr_store) == 0:
            selected_exp = util.select_dict_key_using_integer(exp_budg_db, 
                                                              f"No expenses for {storename}. Please select an expense to go with this store from now on.",
                                                              print_children=False)
            exp_stor_db[storename] = [selected_exp]
            data_help.write_to_jsonFile(stor_exp_data_path, exp_stor_db)

        elif len(exps_fr_store) == 1:
            selected_exp = exps_fr_store[0]
        else:
            selected_exp = exps_fr_store[select_expense_idx(exps_fr_store, storename)]

        return selected_exp, dict(exp_stor_db)
    
    else: # simplify store name, check for matches
        select_store_for_purchase(storename, store_keys=exp_stor_dbKeys)
        return "foo", dict(exp_stor_db)

def select_store_for_purchase(storename, store_keys=None): # TODO:
    """
    Uses user input to match a storename to a storename in the database. Allows writing
    """
    simplified_sname = storename.split(' ')[0]
    print(simplified_sname)
    matches = [key for key in store_keys if simplified_sname in key]
    print(matches)

def select_expense_idx(exps_fr_store, storename):
    """
    Gets the index of an expense to select from the user
    """
    selection_idx = util.select_from_list(exps_fr_store, "Multiple expenses for this store. Select one please: ")
    return selection_idx