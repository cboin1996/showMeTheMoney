import pandas as pd
import os, sys
import json
import shutil

import env
import util
import re

def load_csv(file_path, col_names=None, index_col=None, dtype=None, parse_dates=None):
    """
    Loads a csv into a dataframe
    params:
        file_paths - the paths to the files to load
        col_names - the names of the dataframe columns
    """
    df = pd.read_csv(file_path, names=col_names, index_col=index_col, dtype=dtype, parse_dates=parse_dates)
    return df


def load_csvs(file_paths, col_names=None, dtype=None, parse_dates=None):
    """
    Loads multiple csvs into a single frame
    params:
        file_paths - the paths to the files to load
        col_names - the names of the dataframe columns
    returns : pandas dataframe
    """
    return pd.concat(pd.read_csv(file_path, names=col_names,  dtype=dtype, parse_dates=parse_dates) for file_path in file_paths) 


def drop_dups(df, col_names):
    """
    Drops any duplicates in a dataset, writes to file.
    """
    if df.duplicated(subset = col_names).any():
        print("Stripped data for newest entries only.")
        df.drop_duplicates(subset=col_names, inplace=True)
    else:
        print("hey thanks for the break. No duplicates detected.")
    return df

def write_data(df, out_filepath):
    """
    Writes filtered data to csv db
    """
    print(f"Wrote dataframe to {out_filepath}")
    df.to_csv(out_filepath, index=False)
    return

def move_files(files, dest):
    """
    """
    for file in files:
        shutil.move(file, dest)


def filter_by_amnt(df):
    """
    Takes a dataframe with positive and negative dollara mounts, and returns two frames: one with pos and one with neg.
    """
    inc_df = df[df[env.AMOUNT] > 0]
    exp_df = df[df[env.AMOUNT] < 0]
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

def extract_first_days_of_months(date_col):
    """
    Given a list of dates, returns only the first day of the months present in that list
    """
    date_col.drop_duplicates(inplace=True)
    date_list = []
    for date in date_col:
        date_list.append(util.get_month_from_timestamp(date))
    
    return set(date_list)

def modify_dict_key(dct, old_key, new_key):
    """
    Modify's a dict key, returning the modified dict
    """
    if old_key in dct.keys():
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
            dct[k] = new_val

    return dct

