import json
import os
import sys
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
        exp_list[env.EXPENSE_DATA_KEY] = util.format_input_to_list(
            "Please input your expense categories, separated by a space [exp1 exp2 ...] I will add a Misc category since it is reserved: ")
        idxs_matched = util.check_lst_for_values(
            exp_list[env.EXPENSE_DATA_KEY], env.MISC_POS_VALUES)
        for idx in sorted(idxs_matched, reverse=True):
            print(
                f"Found {exp_list[env.EXPENSE_DATA_KEY][idx]} in your expenses. Removing since '{env.EXPENSE_MISC_STR}' is reserved as miscellaneous category.")
            del exp_list[env.EXPENSE_DATA_KEY][idx]
        exp_list[env.EXPENSE_DATA_KEY].append(env.EXPENSE_MISC_STR)
        data_help.write_to_jsonFile(exp_path, exp_list)

    elif env.EXPENSES_SUBTRACTED_KEY not in exp_list.keys():
        exp_list[env.EXPENSES_SUBTRACTED_KEY] = []
        data_help.write_to_jsonFile(exp_path, exp_list)


def choose_bank(json_path: str):
    """
    Prompt user for banks
    """
    bank_json = data_help.read_jsonFile(json_path)
    if env.BANK_SELECTION_KEY not in bank_json.keys():
        prompt = f"Please choose your bank from the list of banks: "
        choice = util.select_from_list(
            env.BANK_OPTIONS, prompt, ret_match=True)
        bank_json[env.BANK_SELECTION_KEY] = choice
        bank_json[env.BANK_CHOICES_KEY] = env.BANK_OPTIONS
        data_help.write_to_jsonFile(json_path, bank_json)


def declare_new_budget(date, exp_data):
    """
    Sets up an entirely new budget with expense categories for that month
    """

    exp_list = exp_data[env.EXPENSE_DATA_KEY]
    local_budget = {}
    month_total = util.get_float_input(
        f"Please input your total for the month ending {date}: ", force_pos=True)
    budg_remaining = month_total

    for i, exp in enumerate(exp_list):
        if i == len(exp_list) - 1:
            print("I got the last one for you :) MATH!")
            budg_amnt = budg_remaining
            budg_remaining = 0

        elif budg_remaining == 0:  # elif skips this condition if budget remaining is set above
            budg_amnt = 0
            local_budget[env.BUDGET_TOTAL_KEY] = month_total
        else:
            prompt = f"Enter your budget for: [{exp}] - Total Budget Re. ${budg_remaining} - Exp's Re. [{len(exp_list) - i - 1}]: "
            budg_amnt = prompt_for_budget_amnt(
                prompt, budg_remaining, exp_data)
        local_budget.update({exp: budg_amnt})
        budg_remaining = round(month_total - sum_budget(local_budget), 2)
        print(local_budget)
    return local_budget


def prompt_for_budget_amnt(prompt, budg_remaining, exp_data):
    """
    Gathers a budget entry of str:float type from user input, ensuring it is not over the months totaL
    """
    flag = False
    while not flag:
        budget_amnt = util.get_float_input(prompt, force_pos=True)

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
    for k, v in monthly_budget.items():
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
        if date not in exp_budg_keys:  # check for current month to find exp categories
            print(
                f"I have detected some data with for the month {date} that has no budget set.")
            print(
                "Please set the budget for this month.. or delete the data and run the program again.")
            if len(exp_budg) != 0:
                user_in = util.get_user_input_for_chars(
                    "Would you like to the whole thing (w) or create new (n)? ", ['w', 'n'])

                if user_in == 'w':
                    key = util.select_dict_key_using_integer(
                        exp_budg, "Please select a budget to copy: ")
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


def get_expenses_for_rows(df, stor_exp_data_path, stor_data_path, budg_path, regex_str, bank_name):
    """
    Gets the expense data for stores, prompting the user when multiple expenses exist for a store
    params:
        df - pandas dataframe
        stor_exp_data_path - filepath to expensesDB
    """
    print("\nIterating your transactions. If you want to quit halfway, type ctrl c to save!\n")

    # initialize the objects for tracking changes
    exp_stor_db = data_help.read_jsonFile(stor_exp_data_path)
    stor_db = data_help.read_jsonFile(stor_data_path)
    budg_db = data_help.read_jsonFile(budg_path)
    try:
        for idx, row in df.iterrows():
            # iterate through only the data which has no expenses declared.
            if pd.isnull(row[env.EXPENSE]):
                # get relevant expenses for that month set by the user.
                month_end_date = util.get_month_from_timestamp(
                    row[env.DATE], start=False)
                if type(row[env.BANK_STORENAME]) is str:
                    match = regex_str.search(row[env.BANK_STORENAME])

                    if match:

                        processed_text = util.process_text(match.group(0))
                        print(
                            f"Was able to filter - {row[env.BANK_STORENAME]} -> {processed_text}")
                        storename = processed_text

                    else:
                        print(f"Unable to filter - {row[env.BANK_STORENAME]}")
                        storename = row[env.BANK_STORENAME]

                elif bank_name == env.SCOTIABANK:  # cqtch the NaN case, scotia includes type column with data
                    query = row[env.TYPE].lower()
                    print(query)
                    storename = query
                
                else: # default case use empty str
                    print("No storename exists for this transaction.")
                    storename = ""

                print("Curr Transaction:  %-10s | %-10s | %-10s " %
                      (row[env.DATE], row[env.AMOUNT], storename))
                selected_exp, exp_stor_db, stor_db, storename = search_store_relationships(storename, exp_stor_db, budg_db[month_end_date],
                                                                                           stor_exp_data_path, stor_db, stor_data_path)
                df.at[idx, env.FILT_STORENAME] = storename
                df.at[idx, env.EXPENSE] = selected_exp

    except KeyboardInterrupt:
        print("\n\nQuitting to main menu. Your data inputs will be saved, and you can resume where you left off by restarting and selecting 'v' for view data!\n")

    return df


def search_store_relationships(storename, exp_stor_db, budg_db, stor_exp_data_path, stor_db, stor_data_path):
    """
    Searches the store expense relationship (exp_stor_db) for an expense and if multiple exist, prompts the user to select one.
    params:
        storename - a store's name from the dataframe
        exp_stor_db - a python dict containing stores as keys, and arrays of expenses as values
        budg_db - expense budget dict database
        stor_exp_data_path - filepath to storesWithExpenses.json
        stor_db - the storename to store strings database
        stor_data_path - the path to stor_db
    returns: the selected expense string, and the modified exp_stor_db
    """
    exp_stor_dbKeys = exp_stor_db.keys()

    if storename not in exp_stor_dbKeys:
        storename, stor_db, exp_stor_db = select_store_for_purchase(
            storename, stor_data_path, stor_db, exp_stor_db, stor_exp_data_path)

    exps_fr_store = exp_stor_db[storename]

    if len(exps_fr_store) == 0:
        selected_exps = util.select_indices_of_list(f"No expenses for '{storename}'. Please select one or multiple to go with this store from now on.",
                                                    list(budg_db.keys()),
                                                    return_matches=True)
        if len(selected_exps) == 1:
            selected_exp = selected_exps[0]
        else:
            selected_exp = util.select_from_list(
                selected_exps, f"Please select which expense you want for this transaction at '{storename}': ", ret_match=True)
        exp_stor_db[storename] = selected_exps
        data_help.write_to_jsonFile(stor_exp_data_path, exp_stor_db)

    elif len(exps_fr_store) == 1:
        selected_exp = exps_fr_store[0]
    else:
        selected_exp = exps_fr_store[util.select_from_list(
            exps_fr_store, f"Please select an expense for this transaction at '{storename}': ")]

    return selected_exp, dict(exp_stor_db), stor_db, storename


def select_store_for_purchase(storename, stor_data_path, stor_db, exp_stor_db, stor_exp_data_path):
    """
    Uses user input to match a storename to a storename in the database. If no store is found, takes user through adding a store.
    """
    if storename not in stor_db.keys():
        prompt = f"I cannot filter for the store '{storename}'. Please select the storename for this store and I will remember it for next time. If it is a new store, type 'n': "
        matched_storename = util.select_dict_key_using_integer(
            exp_stor_db, prompt, quit_str='n', print_children=False, print_aborting=False)

        if matched_storename == None:
            matched_storename = util.process_input(
                f"Could you enter a storename so I remember this store in the future? ")
            # if new store is added, add it to the exp_stor_db, with empty expenses to be added later by user
            exp_stor_db.update({matched_storename: []})
            data_help.write_to_jsonFile(stor_exp_data_path, exp_stor_db)
        stor_db.update({storename: matched_storename})

        data_help.write_to_jsonFile(stor_data_path, stor_db)

    else:
        matched_storename = stor_db[storename]

    return matched_storename, stor_db, exp_stor_db
