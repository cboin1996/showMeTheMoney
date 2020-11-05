import pandas as pd
import numpy as np
import os
import sys
import json
import shutil

import env
import util
import re
import uuid


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
    df = pd.read_csv(file_path, names=col_names,
                     index_col=index_col, dtype=dtype, parse_dates=parse_dates)
    return df


def load_csvs(file_paths, col_names=None, dtype=None, parse_dates=None, index=None, strip_cols=None):
    """
    Loads multiple csvs into a single frame
    params:
        file_paths - the paths to the files to load
        col_names - the names of the dataframe columns to grab while importing
    returns : pandas dataframe
    """
    df = pd.concat(pd.read_csv(file_path, names=col_names,  dtype=dtype, parse_dates=parse_dates,
                               index_col=index, skipinitialspace=True) for file_path in file_paths)
    if strip_cols != None:
        df = strip_cols_in_df(df, strip_cols)
    return df


def load_and_process_csvs(file_paths, strip_cols=None, data_type=None):
    """
    Loads multiple csvs from differing data tables given from scotiabank (credit and debit)
    """
    dfs_in = []
    for fpath in file_paths:
        if data_type == env.RBC:
            df = pd.read_csv(fpath, header=None, skiprows=1)

        elif data_type != env.BMO:
            df = pd.read_csv(fpath, header=None)
        else:
            df = pd.read_csv(fpath, header=0, skiprows=9)

        # scotia credit cards have 3 cols, debit has more.
        if len(df.columns) == 3 and data_type == env.SCOTIABANK:
            df.columns = env.SB_BASE_CREDIT_COLNAMES
            # add type column to credit data to match debit data frame
            df[env.TYPE] = np.nan
        
        elif data_type == env.SCOTIABANK and len(df.columns) == 5:
            df.columns = env.SB_BASE_DEBIT_COLNAMES
            df.loc[df[env.BANK_STORENAME].isnull(),env.BANK_STORENAME] = df[env.TYPE]
            df.drop(columns=[env.NULL], inplace=True)
            
        elif len(df.columns) == 4 and data_type == env.CIBC:
            df.columns = env.CIBC_BASE_COLNAMES
            df[env.TYPE] = np.nan

        elif len(df.columns) == 5 and data_type == env.CIBC:
            df.columns = env.CIBC_CREDIT_COLNAMES
            df[env.TYPE] = np.nan
            df.drop(columns=[env.CIBC_CARD_NUM_COL], inplace=True)
        
        elif len(df.columns) == 5 and data_type == env.BMO:
            df.columns = env.BMO_DEBIT_COLNAMES
            df.drop(columns=[env.NULL], inplace=True)
            df.loc[:,env.DATE] = pd.to_datetime(df.loc[:,env.DATE], format=env.BMO_DATE_FORMAT).copy()


        elif len(df.columns) == 6 and data_type == env.BMO:
            df.columns = env.BMO_CREDIT_COLNAMES
            df.drop(columns=[env.NULL, env.BMO_CARDNUM_COL, env.BMO_ITEMNUM_COL], inplace=True)
            df.loc[:,env.DATE] = pd.to_datetime(df.loc[:,env.DATE], format=env.BMO_DATE_FORMAT).copy()
        
        elif len(df.columns) == 9 and data_type == env.RBC:
            df.columns = env.RBC_DEBIT_COLNAMES
            df.loc[df[env.BANK_STORENAME].isnull(),env.BANK_STORENAME] = df[env.TYPE]
            df.drop(columns=[env.NULL, env.RBC_ACC_NO, env.RBC_ACC_TYPE,
                env.RBC_USD, env.RBC_INVIS], inplace=True)

        dfs_in.append(df)

    df_out = pd.concat(dfs_in)
    if strip_cols != None:
        df_out = strip_cols_in_df(df_out, strip_cols)

    return df_out


def strip_cols_in_df(df, cols):
    for col in cols:
        # print(f"{df[col]} : {df[col].str.strip()}")
        # make sure that not all values are null in the column.
        if not df[col].isnull().all():
            df[col] = df[col].str.strip()

    return df


def drop_for_substring(df, col_name, lst_of_substrs, str_out=''):
    """
    Drops any matched for a list of substrings within the dataframe, returns the df
    """
    df[col_name] = df[col_name].fillna(
        '')  # avoids error when parsing NaN types in the col
    df_to_drop = df[df[col_name].str.contains("|".join(lst_of_substrs))]
    if df_to_drop.empty:
        print("No Transactions to remove.")
    else:
        print(str_out)
        util.print_fulldf(df_to_drop)
        # filter out any credit payments from debit to here.
        df = df[~df[col_name].str.contains("|".join(lst_of_substrs))]
    return df


def drop_rows(prompt, df):
    util.print_fulldf(df)
    rows = util.select_indices_of_list(prompt, list(
        df.index), abortchar='q', print_lst=False)
    if rows is not None:  # above returns none if user aborts
        df.drop(index=rows, inplace=True)
        return df
    else:
        return None


def drop_dups(df, col_names, ignore_index=False):
    """
    Drops any duplicates in a dataset, writes to file.
    """
    print("Removing duplicates in your data if any.")
    # this line is crucial for making drop dups work. drop dups doesn't work on pandas Object type for dates.
    df.loc[:,env.DATE] = pd.to_datetime(df.loc[:,env.DATE]).copy()
    df.drop_duplicates(subset=col_names, inplace=True,
                       ignore_index=ignore_index)

    return df


def remove_subframe(df_to_remove_from, df_to_remove, col_names):
    """
    Used to drop the a dataframe from within another
    Adding df_to_remove twice guarantees removal.
    """
    df = pd.concat([df_to_remove_from, df_to_remove, df_to_remove])
    df.loc[:,env.DATE] = pd.to_datetime(df.loc[:,env.DATE]).copy()
    df.drop_duplicates(keep=False, inplace=True, subset=col_names, ignore_index=True)

    return df


def write_data(df, out_filepath, sortby=None, fillna_col=None):
    """
    Writes filtered data to csv db 

    """
    if sortby is not None:
        df.sort_values(by=[sortby], inplace=True)  # sort data by date.

    if fillna_col is not None:
        for col in fillna_col:
            df[col] = df[col].fillna(0.0)

    print(f"Wrote dataframe to {out_filepath}")
    df.to_csv(out_filepath, index=False)
    return


def add_columns(df, colnames_to_add):
    """
    Adds empty column names to df
    """

    for colname in colnames_to_add:
        df.loc[:, colname] = np.nan
    return df


def move_files(files, dest):
    """
    """
    for file in files:
        shutil.move(file, dest)


def filter_by_amnt(df, col_name, col_name2=None, bank_name=None):
    """
    Takes a dataframe with positive and negative dollara mounts, and returns two frames: 
        one with pos and one with neg.. where the negs are set to positive.
    """
    if bank_name == env.SCOTIABANK or bank_name == env.BMO or bank_name == env.RBC:
        inc_df = df[df[col_name] > 0].copy()
        exp_df = df[df[col_name] < 0].copy()
        exp_df.loc[:, col_name] = exp_df[col_name].abs()
    elif bank_name == env.CIBC:
        inc_df = df[df[col_name2].notna()].copy()
        inc_df.drop(columns=[col_name], inplace=True)
        inc_df.rename(columns={col_name2: col_name}, inplace=True)

        exp_df = df[df[col_name].notna()].copy()
        exp_df.drop(columns=[col_name2], inplace=True)
    

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
    for k, v in linked_data.items():
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
    Given a pandas series of dates, returns only the first day of the months present in that list as a set
    """
    date_col.drop_duplicates(inplace=True)
    date_list = []
    for date in date_col:
        date_list.append(util.get_month_from_timestamp(date,  start=start))

    return set(date_list)

def extract_year_month(date_col, str_format=True):
    date_col.drop_duplicates(inplace=True)
    months = list(set(date_col.dt.to_period('M')))
    if str_format == True:
        ret = [str(month) for month in months]
    else:
        ret = months
    return ret

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

def drop_dt_indices_not_in_selection(indx_sels, indxs, dfs: list):

    if indx_sels != indxs:
        mod_dfs = []
        for df in dfs:
            dfout = df.copy()
            for indx in indxs: # get the indices to drop
                if indx not in indx_sels and indx in df.index:
                    dfout.drop(dfout.loc[indx].index, inplace=True)
            
            mod_dfs.append(dfout)

        return mod_dfs

    return dfs

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


def match_mod_dict_vals(dct: dict, old_val: str, new_val: str):
    """
    Modify dict vals of string type old_val to new_val
    """
    for k, v in dct.items():
        if old_val == v:
            print(f"Replaced {old_val} with {new_val}")
            dct[k] = new_val

    return dct


def locate_and_move_data_between_dfs(df_to_move_from, rows, df_to_accept, col_to_erase=None):
    """
    Select rows from df_to_move_from to df_to_accept
    """
    df_to_move = df_to_move_from.loc[rows]
    df_to_move_from.drop(rows, inplace=True)
    if col_to_erase is not None:
        df_to_move[col_to_erase] = ""
    print(f"Moving below df.\n{df_to_move}\n")
    df_to_accept = pd.concat([df_to_move, df_to_accept])

    return df_to_move_from, df_to_accept


def check_for_match_in_rows(rows, df, df_col_with_val, df_to_check, df_to_check_idcol, df_to_check_path, df_to_check_col_with_val):
    """
    params:
        rows: rows of the df
        df - the dataframe to get ids from to check for matches in df_to_check
    """
    for row in rows:
        val = df.at[row, df_col_with_val]
        # check column for unique id
        cross_check_id = df.at[row, df_to_check_idcol]
        # check if unique id exists in other df
        matches = df_to_check.loc[df_to_check[df_to_check_idcol]
                                  == cross_check_id]

        if matches.empty:  # catch if empty is returned
            print("No matches found when restoring. ")
        else:
            print(
                "\n I found the below transactions with the same dollar amount in the adjustment column: ")
            util.print_fulldf(matches)
            prompt = f"Which indices here are the matching transaction adjustment? Type (n) to ignore and restore anyways. "
            match_idx_lst = matches.index.tolist()
            idx = util.select_from_list(
                match_idx_lst, prompt, abortchar='a', ret_match=False, print_lst=False, check_contents=True)
            if idx is not None:
                df_to_check.at[idx, df_to_check_col_with_val] = round(
                    df_to_check.at[idx, df_to_check_col_with_val] - val, 2)
                write_data(df_to_check, df_to_check_path)  # write data out.
            else:  # none type indicates restore anyways
                return None


def combine_and_drop(df, col1, col2, operation: str):
    """
    Combines two columns, dropping col2 from the dataframe
    params:
        df - the pandas df
        col1 - the column name to add or subtract to
        col2 - the column name that gets added or is the amount to subtract
        operation - string for add, subtract
    """
    df[col2] = df[col2].fillna(0)
    if operation == 'subtract':
        df[col1] = df[col1] - df[col2]
    elif operation == 'add':
        df[col1] = df[col1] + df[col2]
    df.drop(columns=[col2], inplace=True)

    return df


def iterate_df_and_add_uuid_to_col(df, col):
    """
    Adds a unique UUID to pandas col for each item. 
    """
    for idx, row in df.iterrows():
        if pd.isnull(row[col]):
            uuid_val = uuid.uuid4()
            df.at[idx, col] = uuid_val

    return df
