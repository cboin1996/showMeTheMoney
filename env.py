import os 
import re
"""
Dataframe Headers
"""
DATE = 'Date'
AMOUNT = 'Amount'
NULL = 'Null'
TYPE = 'Type'
BANK_STORENAME = 'BankStoreName'
FILT_STORENAME = 'FilteredStoreName'
EXPENSE = 'Expense'

COLUMN_NAMES = [DATE, AMOUNT, NULL, TYPE, BANK_STORENAME, FILT_STORENAME, EXPENSE]
SB_dtypes = {DATE : 'str', AMOUNT : 'float', NULL : 'str', TYPE : 'str', BANK_STORENAME : "str", FILT_STORENAME : "str", EXPENSE : 'str'}
SB_parse_dates = ['Date']

"""
regular expression Parameters
Guide:
    r'((?<=(APOS|FPOS) )(.*)(?=#))' - match between 'APOS ' or 'FPOS ' up until '#'
    r'|((?<=(APOS|FPOS|OPOS) )(.+?)(?=\d+\s\s))' - match whats between 'APOS ', 'FPOS ', or 'OPOS ' until a number than is followed by at least two spaces
    r'|((?<=(MB-)|(PC-))(.*))'  - match from MB- or PC- forward
    r'|(.+?(?=[a-zA-Z]\d+))' - match up until a character with a 4 digit number exists
    r'|((?<=(APOS|FPOS) )(.*)\s\s)' - match between 'APOS ' or 'FPOS ' up until two spaces
    r'|^(((?!APOS|MB-|PC-|FPOS).)(.*)(?=#))' - Match anything excluding 'APOS', 'MB-', 'PC-', 'FPOS' up to '#'
    r'|^(((?!APOS|MB-|PC-|FPOS).)(.*)(\s\s))' - Match anything excluding 'APOS', 'MB-', 'PC-', 'FPOS' up to 'two spaces'
    r'|^(PC TO \d+)' - Match anything with PC TO and a number
    r'|((?<=(APOS|FPOS|OPOS) )(.*))' - Match anything excluding APOS, FPOS, or OPOS up until the end of the string
    | - or's the match params
"""
RE_EXPR = re.compile(
                        r'((?<=(APOS|FPOS|OPOS) )(.*)(?=#))'
                        r'|((?<=(APOS|FPOS|OPOS) )(.+?)(?=\d+\s\s))'
                        r'|((?<=(MB-)|(PC-))(.*))'
                        r'|(.+?(?=[a-zA-Z]\d+))'
                        r'|((?<=(APOS|FPOS|OPOS) )(.*)\s\s)'
                        r'|^(((?!APOS|MB-|PC-|FPOS|OPOS).)(.*)(?=#))'
                        r'|^(((?!APOS|MB-|PC-|FPOS|OPOS).)(.*)(\s\s))'
                        r'|^(PC TO \d+)'
                        r'|((?<=(APOS|FPOS|OPOS) )(.*))'
                    )

OUT_DATA_TEMPL = "db.csv"
OUT_DATA_CHKSZ = 3
csv = "*.csv"
EXP_STOR_DB_FNAME = os.path.join('lib', 'storesWithExpenses.json')
BUDGET_FNAME = os.path.join('lib', 'Budget.json')
STORE_PAIR_FNAME = os.path.join('lib', 'storePairs.json')
EXP_FNAME = os.path.join('lib', 'expenses.json')

EXPENSE_DATA_KEY = 'expense'
BUDGET_TOTAL_KEY = 'total'