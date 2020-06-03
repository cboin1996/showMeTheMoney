import pandas as pd
import os, sys
import json
"""
Loads a csv into a dataframe
"""
def load_csv(file_path, col_names=None):
    if col_names != None:
        return pd.read_csv(file_path, names=col_names)
    else:
        return pd.read_csv(file_path)
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