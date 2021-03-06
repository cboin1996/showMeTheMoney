import datetime
import pandas as pd
import re 
import calendar
import pyautogui
import data_help

import expManager

import env

class Bankconfig:
    """
    Class for carrying the bank's configuration settings
    params:
        settings_path - the path to the bank_choices json file
        strip_cols - columns to strip for whitespace in a dataframe
        check_for_dups_col - columns to use as a subset for checking for duplicates in a dataframe
        regex_str - the regex used while parsing bank's data
        ignorable_transactions - the transactions that are ignored in a dataframe
        exp_colnames - the expense dataframe columns
        inc_colnames - the income dataframe columns
    """
    def __init__(self,  
                settings_path,
                strip_cols,
                check_for_dups_cols,
                regex_str,
                ignorable_transactions,
                exp_colnames,
                inc_colnames,
                exp_dtypes,
                inc_dtypes,
                selection):
        self.settings_path = settings_path
        self.strip_cols = strip_cols
        self.check_for_dups_cols = check_for_dups_cols
        self.regex_str = regex_str
        self.ignorable_transactions = ignorable_transactions
        self.exp_colnames = exp_colnames
        self.inc_colnames = inc_colnames
        self.exp_dtypes = exp_dtypes
        self.inc_dtypes = inc_dtypes
        self.selection = selection

def get_bank_conf(settings, settings_path, abortchar=None):
    bankconfig = None
    if len(settings[env.BANK_SELECTION_KEY]) == 1:
        bank_sel = settings[env.BANK_SELECTION_KEY][0]
    else:
        bank_sel = select_from_list(settings[env.BANK_SELECTION_KEY], "Which bank would you like to use today? ", ret_match=True, abortchar=abortchar)
    
    if bank_sel == env.SCOTIABANK:
        bankconfig = Bankconfig(
            settings_path = settings_path,
            strip_cols = [env.TYPE, env.BANK_STORENAME],
            check_for_dups_cols = env.CHECK_FOR_DUPLICATES_COL_NAMES,
            regex_str = env.RE_EXPR,
            ignorable_transactions = env.SCOTIA_IGNORABLE_TRANSACTIONS,
            exp_colnames = env.COLUMN_NAMES,
            inc_colnames = env.SB_INC_COLNAMES,
            exp_dtypes=env.SCOTIA_EXP_DTYPES,
            inc_dtypes=env.SCOTIA_INC_DTYPES,
            selection=bank_sel
        )

    elif bank_sel == env.CIBC:
        bankconfig = Bankconfig(
            settings_path = settings_path,
            strip_cols = [env.BANK_STORENAME],
            check_for_dups_cols = env.CIBC_CHECK_FOR_DUPLICATES_COL_NAMES,
            regex_str = env.RE_EXPR_CIBC,
            ignorable_transactions = env.CIBC_IGNORABLE_TRANSACTIONS,
            exp_colnames = env.CIBC_EXPENSE_COLNAMES, 
            inc_colnames = env.CIBC_INCOME_COLNAMES,
            exp_dtypes=env.CIBC_EXP_DTYPES,
            inc_dtypes=env.CIBC_INC_DTYPES,
            selection=bank_sel
        )
    elif bank_sel == env.BMO:
        bankconfig = Bankconfig(
            settings_path = settings_path,
            strip_cols = [env.BANK_STORENAME],
            check_for_dups_cols = env.BMO_CHECK_FOR_DUPLICATES_COL_NAMES,
            regex_str = env.RE_EXPR_BMO,
            ignorable_transactions = env.BMO_IGNORABLE_TRANSACTIONS,
            exp_colnames = env.BMO_EXPENSE_COLNAMES, 
            inc_colnames = env.BMO_INCOME_COLNAMES,
            exp_dtypes=env.BMO_EXP_DTYPES,
            inc_dtypes=env.BMO_INC_DTYPES,
            selection=bank_sel
        )
    elif bank_sel == env.RBC:
        bankconfig = Bankconfig(
            settings_path = settings_path,
            strip_cols = [env.BANK_STORENAME],
            check_for_dups_cols = env.RBC_CHECK_FOR_DUPLICATES_COL_NAMES,
            regex_str = env.RE_EXPR_RBC,
            ignorable_transactions = env.RBC_IGNORABLE_TRANSACTIONS,
            exp_colnames = env.RBC_EXPENSE_COLNAMES, 
            inc_colnames = env.RBC_INCOME_COLNAMES,
            exp_dtypes=env.RBC_EXP_DTYPES,
            inc_dtypes=env.RBC_INC_DTYPES,
            selection=bank_sel
        )
    
    return bankconfig
def get_current_month():
    today = datetime.datetime.today()
    datem = datetime.datetime(today.year, today.month, 1).strftime("%Y-%m-%d")
    return datem

def get_last_month(curr_month):
    date_obj = datetime.datetime.strptime(curr_month, "%Y-%m-%d")
    lastmonth = date_obj - datetime.timedelta(days=1)
    lastmonth = lastmonth.replace(day=1)
    return lastmonth.strftime("%Y-%m-%d")

def get_next_month(curr_month):
    date_obj = datetime.datetime.strptime(curr_month, "%Y-%m-%d")
    lastmonth = date_obj + datetime.timedelta(days=1)
    lastmonth = lastmonth.replace(day=1)
    return lastmonth.strftime("%Y-%m-%d")

def get_month_from_timestamp(timestamp, start=True):
    """
    Sets any day of a month to the start of the month for a pandas.Timestamp object 
    params:
        (pandas.Timestamp) timestamp : a pandas timestamp object
        (bool) start : the start or end of a month to return
    """
    dt_object = pd.Timestamp.to_pydatetime(timestamp)
    if start == True:
        day = 1
        
    else:
        day = calendar.monthrange(dt_object.year, dt_object.month)[1]
    dt_object = dt_object.replace(day=day).strftime("%Y-%m-%d")
    return dt_object 

def replace_string_in_list(lst, string, repl_string):
    """
    Replaces an item in a list with string, if the item exists.
    """
    for i, item in enumerate(lst):
        if item == string:
            print(f"Replaced '{item}' with '{repl_string}'.")
            lst[i] = repl_string
    return lst

def get_user_input_for_chars(prompt, chars):
    flag = False
    while not flag:
        inp = input(prompt)
        if inp in chars:
            flag = True 
        else:
            print("Invalid input.")
    
    return inp


def get_integer_input(prompt):
    flag = False 
    while not flag:
        try:
            integer =  int(input(prompt))
            return integer
        except ValueError:
            print("Must be an integer input.")

def get_float_input(prompt, force_pos=False, roundto=2):
    flag = False
    while not flag:
        try:
            flt = float(input(prompt))
            if flt >= 0:
                return round(flt, roundto) 
            else:
                print("Enter a positive value! I think we all wish money grew on trees.")
        except ValueError:
            print("Must be a number input!")

def process_text(string):
    return string.lower().strip()

def process_input(prompt):
    """
    Processes an input string
    """
    return process_text(input(prompt))

def select_from_list(lst, prompt, abortchar=None, ret_match=False, print_lst=True, check_contents=False):
    """
    Allows user to select a single item from a list by index
    params:
        check_contents - whether to check if user input is in the lst itself or not
    returns:
        if ret_match = False - returns index selection
        if ret_match = True - returns item at the index selection

    """
    if print_lst == True:
        for i, elem in enumerate(lst):
            print(f"\t[{i}] - {elem}")
    
    flag = False 
    while not flag:
        try:
            if abortchar is not None:
                prompt += " 'q' aborts: "
                
            raw_in = input(prompt)
            
            if abortchar == raw_in:
                print("Aborting process.")
                return None
            else:
                user_sel = int(raw_in)
            
            if check_contents == True:
                if user_sel in lst:
                    flag = True
                else:
                    print(f"Please enter a value within the list. options are: {lst}")
            elif user_sel > len(lst) - 1 or user_sel < 0:
                print(f"Please enter a number between 0 and {len(lst) - 1}")
            else:
                user_sel = int(raw_in)
                flag = True 

        except ValueError:
            print("Please input an integer.")
    
    if ret_match == True:
        user_sel = lst[user_sel]
    return user_sel 

def print_sorted_dict(dct, keys_list, print_vals=False, print_children=False, print_child_vals=False):
    for idx, key in enumerate(keys_list):
        output = f"[{idx}] - {key}"
        if print_vals == True:
            output = output +  f": {dct[key]}"
        print(output)
        
        if print_children == True:
            print_simple_dict(dct[key], print_child_vals)

def select_dict_key_using_integer(dct, prompt, print_children=True, quit_str='', print_aborting=True, print_vals=False, print_child_vals=False):
    """
    Returns a key from the dictionary that a user selects using an integer index. Funny eh?
    params:
        dct: the dictionary to select from
        print_children: optional param for printed nested children in a dict
        quit_str: an optional str for having the user abort a selection process
    """
    keys_list = list(dct.keys())
    keys_list.sort()
    print_sorted_dict(dct, keys_list, print_vals=print_vals, print_children=print_children, print_child_vals=print_child_vals)
    
    flag = False
    while not flag:
        try:
            user_sel = input(prompt)
            if quit_str == user_sel:
                if print_aborting == True:
                    print("Aborting.")
                return None 
            user_sel = int(user_sel)
            if user_sel > len(dct) - 1 or user_sel < 0:
                print(f"Please enter a number between 0 and {len(dct) - 1}")
            else:
                flag = True 
        
        except ValueError:
            print("Please input an integer")

    return keys_list[user_sel]

def select_dict_keys_using_integer(dct, prompt, print_children=True, quit_str='', print_aborting=True, print_vals=False):
    """
    Returns a key from the dictionary that a user selects using an integer index. Funny eh?
    params:
        dct: the dictionary to select from
        print_children: optional param for printed nested children in a dict
        quit_str: an optional str for having the user abort a selection process
    """    
    keys_list = list(dct.keys())
    keys_list.sort()
    print_sorted_dict(dct, keys_list, print_vals=print_vals, print_children=print_children)
    selection_list = []
    
    flag = False
    while not flag:
        try:
            user_sels = format_input_to_list(prompt, 'integer', quit_str=quit_str)
            if user_sels == None:
                if print_aborting == True:
                    print("Aborting.")
                return
          
            for i, sel in enumerate(user_sels):          
                if sel > len(dct) - 1 or sel < 0:
                    print(f"Please input numbers between 0 and {len(dct) - 1}")
                    flag = False
                    break

                else:
                    selection_list.append(keys_list[int(sel)])
                    flag = True
                        
        
        except ValueError:
            print("Please input integers!")
            flag = False

    return selection_list
def print_simple_dict(dct, print_vals=False):
    """
    Prints key value pairs for a dict
    """
    i = 0
    for k, v in dct.items():
        output = f"\t[{i}] {k} "
        if print_vals == True:
            output = output + f": {v}"
        print(output)
        i += 1

def print_nested_dict(dct):
    """
    Neatly prints out a nested tree for the user
    """
    for k, v in dct.items():
        print(f" - {k}")
        print_simple_dict(v)

def print_dict_keys(dct):
    for k,v in dct.items():
        print(f"- {k}")

def prompt_with_warning(prompt, ret_lowercase=True):
    """
    Prompts the user with a prompt given, and asks warning message with option to quit
    """
    flag = False
    while not flag:
        user_in = input(prompt)
        user_in = user_in.lower() if ret_lowercase == True else user_in
        y_n = get_user_input_for_chars("Are you sure? [y/n] or 'q' to quit. ", ['y', 'n', 'q'])
        if y_n == 'y':
            flag = True
        elif y_n == 'n':
            print("Okay. try again")
        else:
            print("Exiting process")
            flag = True 
            user_in = None
    
    return user_in

def format_input_to_list(prompt, mode='string', quit_str=None, sel_all=None):
    """
    Used for getting the words in a list and verifying they are all strings
    params:
        prompt - the prompt to the user
        mode - whether parse to an integer list or a string list upon input
    """
    flag = False
    lst = []
    while not flag:
        prompt += f"\nExpecting '{mode}' vals in format e.g. (v1 v2 v3). "
        if quit_str is not None:
            prompt += f"'{quit_str}' aborts: "
        user_in = input(prompt)
        if user_in == quit_str:
            print("Aborting.")
            return
        if user_in == sel_all:
            return sel_all
        if mode == 'integer':
            match = re.search(r"[\d\s]+", user_in) 
        elif mode == 'string':
            match = re.search(r"[\w\s]+", user_in)

        if match:
            flag = True
            lst = match.group(0).split(' ')

            if mode == 'integer':
                lst = [int(item) for item in lst]
        else:
            print(f"Invalid input. Must be {mode}'s separated by spaces")

    return lst 

def select_item_not_in_list(prompt, lst, ignorecase=True, abortchar=None):
    """
    Prompts the user to enter a string, and checks to make sure the string is not in the list before returning list with added string
    """
    flag = False
    lst_cp = list(lst)
    if ignorecase == True:
        for i in range(len(lst_cp)):
            lst_cp[i] = lst_cp[i].lower()
    while not flag:
        user_in = input(prompt)
        if abortchar == None:
            print("Aborting process.")
            return None
        if ignorecase == True:
            user_in = user_in.lower()
        if user_in in lst_cp:
            print("Please enter something not found in the list.")
        else:
            flag = True 
    
    return user_in

def select_indices_of_list(prompt='', list_to_compare_to=[], return_matches=False, abortchar=None, print_lst=True, ret_all_char=None):
    """
    Gets user input for certain elements of a list
    params:
        prompt - the string prompt for the input
        list_to_compare_to - the list that the users input selects items from
        return_matches - default false. If true, returns the matched elements from the user's selection.
    Returns:
        one of: the list of matches selected by the user, the indices of the list selected, or None if aborted.
    """
    success = False
    selections = []
    if print_lst == True:
        print_lst_with_index(list_to_compare_to)
    while success == False:
        try:
            user_input = format_input_to_list(prompt, mode='integer', quit_str=abortchar, sel_all=ret_all_char)
            if user_input == None:
                print("Aborting.")
                return None
            
            elif user_input == ret_all_char:
                return list_to_compare_to
                
            for i, integer in enumerate(user_input): # validate each character
                if integer < len(list_to_compare_to) and integer >= 0:
                    selections.append(integer)
                    success = True

                else:
                    print("Numbers must be 0 or more and less than %s"%(len(list_to_compare_to)-1))
                    success = False
                    break

        except ValueError:
            print("Must enter numbers separated by a single space")
            success = False
        # this will not get reached unless successful trancsription
        if return_matches == False:
            return selections
        if success == True and return_matches == True:
            return [list_to_compare_to[idx] for idx in selections]

def print_lst_with_index(lst):
    for idx, item in enumerate(lst):
        print(f"[{idx}] {item}")

def check_lst_for_values(lst, vals):
    """
    Checks a list of strings to se is a substring is within it
    """
    idxs_matched = []
    for i, item in enumerate(lst):
        if item.lower() in vals:
            idxs_matched.append(i)
    return idxs_matched

def print_fulldf(df, dont_print_cols=None):
    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.expand_frame_repr', False):
        print(" --- --- --- --- --- ")
        if dont_print_cols is not None:
            df_print = df.drop(columns=dont_print_cols)
            print(df_print)
        else:
            print(df)
        print(" --- --- --- --- --- ")

def add_set_to_set(orig_set, set_to_add, sort=False):
    """
    Adds a sets items to a set
    params:
        orig_set : set to add to
        set_to_add : the set to add them items from
        sorted : if true, converts set to list and orders
    """
    for item in set_to_add:
        orig_set.add(item)
    
    if sort == True:
        orig_set = sorted(list(orig_set))


    return orig_set

def get_editable_input(prompt, editable):
    """
    Allows user to edit a string 'editable' during input
    returns: user input
    """
    try:
        print(prompt)
        pyautogui.typewrite(editable)
        user_in = input()
    except KeyboardInterrupt:
        print("Aborting process. ")
        return None

    return user_in

def edit_list_in_dict(prompt, options, dct, key, dct_path, add=True):
    items = select_indices_of_list(prompt, list_to_compare_to=options, return_matches=True, abortchar='q')
    if items is not None:
        if add == True:
            for item in items:
                dct[key].append(item)
        else:
            for item in items:
                dct[key].remove(item)

        data_help.write_to_jsonFile(dct_path, dct)
    else:
        return None

def validate_lst_type(lst, typ):
    if type(lst) != list:
        return False
    for item in lst:
        if type(item) != typ:
            return False
    return True

def get_input_given_type(prompt, data_type, abortchar='q', setting=None):
    done = False 
    while not done:

            

        if validate_lst_type(setting, int):
            user_in = format_input_to_list(prompt, mode='integer', quit_str=abortchar)
        elif validate_lst_type(setting, str):
            user_in = format_input_to_list(prompt, mode='string', quit_str=abortchar)

        else:
            user_in = input(prompt + f"'{abortchar}' aborts: ")
        
        if user_in == abortchar or user_in is None:
            print("Aborting.")
            return

        try:
            user_in = data_type(user_in)
            if type(user_in) is not data_type:
                print(f"Please input '{data_type}' for this entry!")
            else:
                done = True
        except ValueError:
            print(f"Please input {type(user_in)} for this entry!")
        
    return user_in

if __name__=="__main__":
    format_input_to_list("Input words seped by spaces: ")
