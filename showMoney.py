import data_help
import sys, os
import json
import pandas as pd
import glob
import env
import numpy
"""
TODO
1. Load CSV x
2. Pair stores to expense types from apple app X (note. used gather_store_db method)
3. Separate income from expenses X (using +/-)
4. Pair scotia purchase to expense types from expenseDB
5. Sum totals for expense types
6. Sum totals for income (types? idk)
7. Graph the expense types
8. Add budjeting features
    - allow input for monthly budjet
    - red vs blue bars for over/under
9. Create feature that ignores duplicate data entries to prevent uploading the same csv or overlapping csv's X..
"""
"""
Initializes the program and returns any paths to new and archived data files.
"""
def initialize(data_path, ndata_path, adata_path, db_data_path):
    
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    if not os.path.exists(ndata_path):
        os.mkdir(ndata_path)
    if not os.path.exists(adata_path):
        os.mkdir(adata_path)
    if not os.path.exists(db_data_path):
        os.mkdir(db_data_path)

def search(ndata_path, adata_path, db_data_path):
    ndata_filepaths = glob.glob(os.path.join(ndata_path, env.csv), recursive=True)
    db_data_filepaths = glob.glob(os.path.join(db_data_path, env.csv), recursive=True)
    print(f"Searched {ndata_path} and found these files for your banking data: ")
    for files in ndata_filepaths:
        print(files)
    for files in db_data_filepaths:
        print(files)
    return ndata_filepaths, db_data_filepaths
"""
Checks db and new folder for any data. 
Imports it into a single data frame, while writing the new data into the database stored in db.
"""
def import_data(ndata_filepaths, db_data_filepaths, adata_path):
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

def showMoney(db_data_filepaths: list, expenseDB: dict):
    df = data_help.load_csv(file_path=db_data_filepaths[-1], index_col=0, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)# only using on csv db for now. newest will be last? idk verify later.
    inc_df, exp_df = data_help.filter_by_amnt(df)
    print(f"INCOME\n\n{inc_df}\n\nEXPENSES\n\n{exp_df}")
    data_help.get_expenses_for_rows(exp_df, expenseDB)
    
if __name__=="__main__":
    root = sys.path[0]
    data_path = os.path.join(root, 'data')
    ndata_path =  os.path.join(data_path, 'new')
    adata_path = os.path.join(data_path, 'archive')
    db_data_path = os.path.join(data_path, 'db')
    initialize(data_path, ndata_path, adata_path, db_data_path)

    with open(os.path.join(root, env.EXP_DB_FNAME), 'r') as f:
        expenseDB = json.load(f)

    ndata_filepaths, db_data_filepaths = search(ndata_path, adata_path, db_data_path)
    if import_data(ndata_filepaths, db_data_filepaths, adata_path):
        ndata_filepaths, db_data_filepaths = search(ndata_path, adata_path, db_data_path)
        showMoney(db_data_filepaths, expenseDB)
    else:
        print("No data found. Please import some.")

# data_help.gather_store_db(df, os.path.join(sys.path[0], 'expenseDB.json'), 'StoreName', 'ExpenseName')