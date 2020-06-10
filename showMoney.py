import sys, os
import json
import pandas as pd
import glob
import numpy

import expManager
import data_help
import env
import util
import editor
"""
TODO
1. Load CSV x
2. Pair stores to expense types from apple app X (note. used gather_store_db method)
3. Separate income from expenses X (using +/-)
4. Pair scotia purchase to expense types from exp_stor_db
5. Sum totals for expense types
6. Sum totals for income (types? idk)
7. Graph the expense types
8. Add budjeting features
    - allow input for monthly budjet
    - red vs blue bars for over/under
9. Create feature that ignores duplicate data entries to prevent uploading the same csv or overlapping csv's X..
"""

def initialize_dirs(list_of_dirs):
    """
    Initializes the program and returns any paths to new and archived data files.
    """
    for dir in list_of_dirs:
        if not os.path.exists(dir):
            os.mkdir(dir)


def initialize_dbs(json_paths):
    """
    Initializes .json files into their paths given
    """
    for path in json_paths:
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump({}, f)

def find_data_paths(ndata_path, adata_path, db_data_path):
    ndata_filepaths = glob.glob(os.path.join(ndata_path, env.csv), recursive=True)
    db_data_filepaths = glob.glob(os.path.join(db_data_path, env.csv), recursive=True)
    print(f"Searched {ndata_path} and found these files for your banking data: ")
    for files in ndata_filepaths:
        print(files)
    print(f"Searched {db_data_path} and found these files for your banking data: ")
    for files in db_data_filepaths:
        print(files)
    return ndata_filepaths, db_data_filepaths

def import_data(ndata_filepaths, db_data_filepaths, adata_path):
    """
    Checks db and new folder for any data. 
    Imports it into a single data frame, while writing the new data into the database stored in db.
    """
    if len(ndata_filepaths) == 0:
        return False
    if len(ndata_filepaths) != 0 and len(db_data_filepaths) != 0:
        df_new = data_help.load_csvs(file_paths=ndata_filepaths, col_names=env.COLUMN_NAMES)
        df_db = data_help.load_csvs(file_paths=db_data_filepaths)
        df = pd.concat([df_new, df_db])
    elif len(ndata_filepaths) != 0:
        df = data_help.load_csvs(file_paths=ndata_filepaths, col_names=env.COLUMN_NAMES)
    elif len(db_data_filepaths) != 0:
        df = data_help.load_csvs(file_paths=db_data_filepaths)
        return True
    else:
        return False
        
    print("New data loaded into database.")
    print(df)
    df = data_help.drop_dups(df=df, col_names=env.COLUMN_NAMES)
    print(df)
    df.sort_index(inplace=True) # sort data by date.
    data_help.write_data(df, os.path.join(db_data_path, env.OUT_DATA_TEMPL))
    data_help.move_files(files=ndata_filepaths, dest=adata_path)
    print(f"Data imported to {db_data_path}. Old files moved to {adata_path}")
    return True

def edit_money_data(db_data_filepaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path):
    """
    Top level interface for editing databases
    """   
    user_in = util.get_user_input_for_chars("Would you like to edit storenames (s), or expense names (e)? ", ['s', 'e'])
    
    if user_in == 's':
        editor.store_editor(db_data_filepaths, stor_pair_path, stor_exp_data_path, budg_path)
    elif user_in == 'e':
        editor.expenses_editor(db_data_filepaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path)

def import_money_data(db_data_filepaths: list, stor_pair_path: str, stor_exp_data_path : str, budg_path: str, exp_path: str):
    """
    main method for the importing of data
    """
    df = data_help.load_csvs(db_data_filepaths, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)# only using on csv db for now. newest will be last? idk verify later.
    dates = data_help.extract_first_days_of_months(df[env.DATE])
    expManager.get_budgets(budg_path, exp_path, dates) # check for any missing budgets either this month or any month in the data
    
    """ CODE FOR SPLITTING EXP AND INCOME     
    inc_df, exp_df = data_help.filter_by_amnt(df)
    print(f"INCOME\n\n{inc_df}\n\nEXPENSES\n\n{exp_df}")
    exp_df = expManager.get_expenses_for_rows(exp_df, stor_exp_data_path, stor_pair_path, budg_path)
    data_help.write_data(exp_df, db_data_filepaths[0])
    """

    df = expManager.get_expenses_for_rows(df, stor_exp_data_path, stor_pair_path, budg_path)
    data_help.write_data(df, db_data_filepaths[0])

def view_money_data(db_data_filepaths, stor_pair_path, stor_exp_data_path, budg_path):
    df = data_help.load_csvs(db_data_filepaths, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)
    dates = data_help.extract_first_days_of_months(df[env.DATE])
    expManager.get_budgets(budg_path, exp_path, dates) # check for any missing budgets either this month or any month in the data
    print(df)
if __name__=="__main__":
    root = sys.path[0]
    data_path = os.path.join(root, 'data')
    ndata_path =  os.path.join(data_path, 'new')
    adata_path = os.path.join(data_path, 'archive')
    db_data_path = os.path.join(data_path, 'db')
    lib_data_path = os.path.join(root, 'lib')

    list_of_dirs = [data_path,
                    ndata_path,
                    adata_path,
                    db_data_path,
                    lib_data_path]

    budg_path = os.path.join(root, env.BUDGET_FNAME)
    stor_exp_data_path = os.path.join(root, env.EXP_STOR_DB_FNAME)
    stor_pair_path = os.path.join(root, env.STORE_PAIR_FNAME)
    exp_path = os.path.join(root, env.EXP_FNAME)

    json_paths = [budg_path,
                  stor_exp_data_path,
                  stor_pair_path,
                  exp_path]

    initialize_dirs(list_of_dirs)
    initialize_dbs(json_paths)
    expManager.setup_expense_names(exp_path) # check for expense list and setup if none are there.
    print("--- --- --- --- --- --- --- --- --- --- --- --- ---")
    print("--- --- --- -- SHOW ME YOUR MONEY -- --- --- --- --")
    print("--- --- --- --- --- V. 0.00 --- --- --- --- --- ---")
    user_in = util.get_user_input_for_chars("Welcome to the money manager. Would you like to (e) edit data, (i) import data, or (v) view data? ", ['e', 'i', 'v'])
    ndata_filepaths, db_data_filepaths = find_data_paths(ndata_path, adata_path, db_data_path)
    if user_in == 'e':
        edit_money_data(db_data_filepaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path)
    elif user_in == 'i':
        ndata_filepaths, db_data_filepaths = find_data_paths(ndata_path, adata_path, db_data_path)
        if import_data(ndata_filepaths, db_data_filepaths, adata_path):
            ndata_filepaths, db_data_filepaths = find_data_paths(ndata_path, adata_path, db_data_path)
            import_money_data(db_data_filepaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path)
        else:
            print("No data found. Please import some.")
    else:
        view_money_data(db_data_filepaths, stor_pair_path, stor_exp_data_path, budg_path)

# data_help.gather_store_db(df, os.path.join(sys.path[0], 'exp_stor_db.json'), 'StoreName', 'ExpenseName')