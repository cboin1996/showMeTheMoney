import datetime
import pandas as pd
import re 
import calendar
import pyautogui
import data_help

import expManager
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


def select_dict_key_using_integer(dct, prompt, print_children=True, quit_str='', print_aborting=True):
    """
    Returns a key from the dictionary that a user selects using an integer index. Funny eh?
    params:
        dct: the dictionary to select from
        print_children: optional param for printed nested children in a dict
        quit_str: an optional str for having the user abort a selection process
    """
    keys_list = list(dct.keys())
    keys_list.sort()
    for idx, key in enumerate(keys_list):
        print(f"[{idx}] - {key}")
        if print_children == True:
            print_simple_dict(dct[key])
    
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

def print_simple_dict(dct):
    """
    Prints key value pairs for a dict
    """
    i = 0
    for k, v in dct.items():
        print(f"\t[{i}] {k} : {v}")
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

def format_input_to_list(prompt):
    """
    Used for getting the words in a list and verifying they are all strings
    """
    flag = False
    lst = []
    while not flag:
        user_in = input(prompt)
        match = re.search(r"[\w\s]+", user_in)
        if match:
            flag = True
            lst = match.group(0).split(' ')
        else:
            print("Invalid input")

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

def select_indices_of_list(prompt='', list_to_compare_to=[], return_matches=False, abortable=False, abortchar=None, print_lst=True):
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
    if print_lst == True:
        print_lst_with_index(list_to_compare_to)
    while True:
        user_input = input(prompt + " (e.g. 1 2 3): ")
        user_input = user_input.split(' ')
        for i, char in enumerate(user_input): # validate each character
            try:
                if abortable == True and char == abortchar:
                    print("Aborting process.")
                    return None
                if int(char) < len(list_to_compare_to) and int(char) >= 0:
                    user_input[i] = int(user_input[i])
                    success = True

                else:
                    print("Numbers must be 0 or more and less than %s"%(len(list_to_compare_to)-1))
                    success = False

            except ValueError:
                print("Must enter numbers separated by a single space")
                success = False
                break
        # this will not get reached unless successful trancsription
        if success == True and return_matches == False:
            return user_input
        if success == True and return_matches == True:
            return [list_to_compare_to[idx] for idx in user_input]

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

def print_fulldf(df):
    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.expand_frame_repr', False):
        print(" --- --- --- --- --- ")
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
    items = select_indices_of_list(prompt, list_to_compare_to=options, return_matches=True, abortable=True, abortchar='q')
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

if __name__=="__main__":
    format_input_to_list("Input words seped by spaces: ")
