import pandas as pd
import numpy as np
import os, sys
import json
import shutil

import env
import util
import re

def print_file(file_path):
    """
    Generic file loader
    """
    with open(file_path, 'r') as f:
        print("--- --- DOCS START --- ---")
        print(f.read())
        print("--- --- DOCS END --- ---")

def load_csv(file_path, col_names=None, index_col=None, dtype=None, parse_dates=None):
    """
    Loads a csv into a dataframe
    params:
        file_paths - the paths to the files to load
        col_names - the names of the dataframe columns
    """
    df = pd.read_csv(file_path, names=col_names, index_col=index_col, dtype=dtype, parse_dates=parse_dates)
    return df


def load_csvs(file_paths, col_names=None, dtype=None, parse_dates=None, index=None, strip_cols=None):
    """
    Loads multiple csvs into a single frame
    params:
        file_paths - the paths to the files to load
        col_names - the names of the dataframe columns to grab while importing
    returns : pandas dataframe
    """
    df = pd.concat(pd.read_csv(file_path, names=col_names,  dtype=dtype, parse_dates=parse_dates, index_col=index, skipinitialspace=True) for file_path in file_paths)
    if strip_cols != None:
        df = strip_cols_in_df(df, strip_cols)
    return df

def load_and_process_csvs(file_paths, strip_cols=None):
    """
    Loads multiple csvs from differing data tables given from scotiabank (credit and debit)
    """
    dfs_in = []
    for fpath in file_paths:
        df = pd.read_csv(fpath, header=None)
        if len(df.columns) == 3: # scotia credit cards have 3 cols, debit has more.
            df.columns = env.SB_BASE_CREDIT_COLNAMES
            df[env.TYPE] = np.nan # add type column to credit data to match debit data frame
        else:
            df.columns = env.SB_BASE_DEBIT_COLNAMES
            df.drop(columns=[env.NULL], inplace=True)

        dfs_in.append(df)
    
    df_out = pd.concat(dfs_in)
    if strip_cols != None:
        df_out = strip_cols_in_df(df_out, strip_cols)

    return df_out
        
def strip_cols_in_df(df, cols):
    for col in cols:
        # print(f"{df[col]} : {df[col].str.strip()}")
        if not df[col].isnull().all(): # make sure that not all values are null in the column.
            df[col] = df[col].str.strip()

    return df

def drop_for_substring(df, col_name, lst_of_substrs, str_out=''):
    """
    Drops any matched for a list of substrings within the dataframe, returns the df
    """
    
    df_to_drop = df[df[col_name].str.contains("|".join(lst_of_substrs))]
    if df_to_drop.empty:
        print("No Transactions to remove.")
    else:
        print(str_out)
        util.print_fulldf(df_to_drop)
        df = df[~df[col_name].str.contains("|".join(lst_of_substrs))] # filter out any credit payments from debit to here.
    return df
def drop_dups(df, col_names, ignore_index=False, strip_col=None):
    """
    Drops any duplicates in a dataset, writes to file.
    """
    print("Removing duplicates in your data if any.")
    df[env.DATE] = pd.to_datetime(df[env.DATE]) # this line is crucial for making drop dups work. drop dups doesn't work on pandas Object type for dates.
    df.drop_duplicates(subset=col_names, inplace=True, ignore_index=ignore_index)

    return df

def remove_subframe(df_to_remove_from, df_to_remove, col_names):
    """
    Used to drop the a dataframe from within another
    """
    df = pd.concat([df_to_remove_from, df_to_remove])
    df[env.DATE] = pd.to_datetime(df[env.DATE])
    df.drop_duplicates(keep=False, inplace=True, subset=col_names)

    return df
def write_data(df, out_filepath, sortby=None):
    """
    Writes filtered data to csv db
    """
    if sortby is not None:
        df.sort_values(by=[sortby], inplace=True) # sort data by date.
    print(f"Wrote dataframe to {out_filepath}")
    df.to_csv(out_filepath, index=False)
    return

def move_files(files, dest):
    """
    """
    for file in files:
        shutil.move(file, dest)


def filter_by_amnt(df, col_name):
    """
    Takes a dataframe with positive and negative dollara mounts, and returns two frames: one with pos and one with neg.. where the negs are set to positive.
    """
    inc_df = df[df[col_name] > 0].copy()
    exp_df = df[df[col_name] < 0].copy()
    exp_df.loc[:, col_name] = exp_df[col_name].abs()
    return inc_df, exp_df


def gather_store_db(df, file_out, col1, col2):
    """
    Takes data from a csv with two headings, and creates the relationship between the two into a json outfile.
    params:
        df - pandas data frame
        file_out - the filepath to write to
        col1 - the column to become the keys of the dict
        col2 - the column to match to certain keys of the dict
    """
    linked_data = df.groupby(col1)[col2].apply(list).to_dict()
    for k,v in linked_data.items():
        linked_data[k] = list(set(v))
        
    print(linked_data)

    with open(file_out, 'w') as f:
        json.dump(linked_data, f)

def write_to_jsonFile(fp, obj):
    with open(fp, 'w') as f:
        json.dump(obj, f)
        print(f"Wrote changes to {fp}")

def write_to_jsonFile_ifchanged(fp, orig_obj, alt_obj):
    """
    Checks if two objects are not equal, if not writes the alt_obj to file and returns it
    """
    if orig_obj != alt_obj:
        write_to_jsonFile(fp, alt_obj)
        orig_obj = alt_obj

        print(f"Updated {fp} with changes.")
    return orig_obj

def read_jsonFile(fp):
    with open(fp, 'r') as f:
        return json.load(f)

def read_jsonFile_ifchanged(fp, obj1, obj2):
    if obj1 != obj2:
        return read_jsonFile(fp)

def extract_months(date_col, start=True):
    """
    Given a pandas series of dates, returns only the first day of the months present in that list
    """
    date_col.drop_duplicates(inplace=True)
    date_list = []
    for date in date_col:
        date_list.append(util.get_month_from_timestamp(date,  start=start))
  
    
    return set(date_list)

def extract_years(date_col, str_format=True):
    """
    Gets a list (str) of years found in a pandas series.
    """
    years = list(set(date_col.dt.year.values))
    if str_format == True:
        ret = [str(year) for year in years]
    else:
        ret = years
    return ret

def modify_dict_key(dct, old_key, new_key):
    """
    Modify's a dict key, returning the modified dict
    """
    if old_key in dct.keys():
        print(f"Replaced {old_key} with {new_key}")
        dct[new_key] = dct.pop(old_key)
    else:
        print("The key you wish to change does not exist in the dict.")
    
    return dct

def match_mod_dict_vals(dct:dict, old_val:str, new_val:str):
    """
    Modify dict vals of string type old_val to new_val
    """
    for k,v in dct.items():
        if old_val == v:
            print(f"Replaced {old_val} with {new_val}")
            dct[k] = new_val

    return dct


def locate_and_move_data_between_dfs(df_to_move_from, rows, df_to_accept):
    """
    Select rows from df_to_move_from to df_to_accept
    """
    df_to_move = df_to_move_from.loc[rows]
    df_to_move_from.drop(rows, inplace=True)
    print(f"Moving below df.\n{df_to_move}\n")
    df_to_accept = pd.concat([df_to_move, df_to_accept])

    return df_to_move_from, df_to_accept