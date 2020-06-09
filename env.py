import os 
"""
Dataframe Headers
"""
INDEX = 'Date'
AMOUNT = 'Amount'
NULL = 'Null'
TYPE = 'Type'
STORE = 'Store'
EXPENSE = 'Expense'

COLUMN_NAMES = [INDEX, AMOUNT, NULL, TYPE, STORE, EXPENSE]
SB_dtypes = {INDEX : 'str', AMOUNT : 'float', NULL : 'str', TYPE : 'str', STORE : "str", EXPENSE : 'str'}
SB_parse_dates = ['Date']
OUT_DATA_TEMPL = "db.csv"
OUT_DATA_CHKSZ = 3
csv = "*.csv"
EXP_DB_FNAME = 'expensesDB.json'