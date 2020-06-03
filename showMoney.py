import data_help
import sys, os
import json
import pandas as pd
"""
TODO
1. Load CSV x
2. Pair stores to expense types from apple app X (note. used gather_store_db method)
3. Separate income from expenses (using +/-)
4. Pair scotia purchase to expense types from expenseDB
5. Sum totals for expense types
6. Sum totals for income (types? idk)
7. Graph the expense types
8. Add budjeting features
    - allow input for monthly budjet
    - red vs blue bars for over/under
9. Create feature that ignores duplicate data entries to prevent uploading the same csv or overlapping csv's..
"""
local_path = sys.path[0]

file_path = os.path.join(sys.path[0], 'data', 'pcbanking.csv')
df = data_help.load_csv(file_path=file_path, col_names=['Date', 'Amount', 'Null', 'Type', 'Store'])

print(df)



# data_help.gather_store_db(df, os.path.join(sys.path[0], 'expenseDB.json'), 'StoreName', 'ExpenseName')