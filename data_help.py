import pandas as pd
import os, sys
import json
import shutil
import env
import util
"""
Loads a csv into a dataframe
params:
    file_paths - the paths to the files to load
    col_names - the names of the dataframe columns
"""
def load_csv(file_path, col_names=None, index_col=None, dtype=None, parse_dates=None):
    return pd.read_csv(file_path, names=col_names, index_col=index_col)

"""
Loads multiple csvs into a single frame
params:
    file_paths - the paths to the files to load
    col_names - the names of the dataframe columns
returns : pandas dataframe
"""
def load_csvs(file_paths, col_names=None, dtype=None, parse_dates=None):
    return pd.concat(pd.read_csv(file_path, names=col_names, dtype=None, parse_dates=None) for file_path in file_paths) 

"""
Drops any duplicates in a dataset, writes to file.
"""
def drop_dups(df, col_names):
    if df.duplicated(subset = col_names).any():
        print("Stripping data for newest entries only.")
        df.drop_duplicates(subset=col_names, inplace=True)
    else:
        print("hey thanks for the break. No duplicates detected.")
    return df
"""
Writes filtered data to csv db
"""
def write_data(df, out_filepath):
    df.to_csv(out_filepath, index=False)
    return

"""
"""
def move_files(files, dest):
    for file in files:
        shutil.move(file, dest)

"""
Takes a dataframe with positive and negative dollara mounts, and returns two frames: one with pos and one with neg.
"""
def filter_by_amnt(df):
    inc_df = df[df[env.AMOUNT] > 0]
    exp_df = df[df[env.AMOUNT] < 0]
    return inc_df, exp_df

"""
Takes data from a csv with two headings, and creates the relationship between the two into a json outfile.
params:
    df - pandas data frame
    file_out - the filepath to write to
    col1 - the column to become the keys of the dict
    col2 - the column to match to certain keys of the dict
"""
def gather_store_db(df, file_out, col1, col2):
    linked_data = df.groupby(col1)[col2].apply(list).to_dict()
    for k,v in linked_data.items():
        linked_data[k] = list(set(v))
        
    print(linked_data)

    with open(file_out, 'w') as f:
        json.dump(linked_data, f)

"""
Gets the expense data for stores, prompting the user when multiple expenses exist for a store
params:

"""
def get_expenses_for_rows(df, expenseDB):
    df_no_exp = df[df[env.EXPENSE].isnull()]
    for idx, row in df_no_exp.iterrows():
        print(row[env.STORE]) # TODO: CONTINUE HERE.. need to parse store names somehow.

