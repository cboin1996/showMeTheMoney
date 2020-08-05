import os 
import re
import pandas as pd


VERSION = "1.30"
"""
Dataframe Headers
"""
DATE = 'Date'
AMOUNT = 'Amount'
ADJUSTMENT = 'Adjustment'
NULL = 'Null'
TYPE = 'Type'
BANK_STORENAME = 'BankStoreName'
FILT_STORENAME = 'FilteredStoreName'
EXPENSE = 'Expense'

BUDGET = 'Budget'
REMAINING = 'Remaining'

SB_BASE_CREDIT_COLNAMES = [DATE, BANK_STORENAME, AMOUNT]
SB_BASE_DEBIT_COLNAMES = [DATE, AMOUNT, NULL, TYPE, BANK_STORENAME]
SB_INC_COLNAMES = [DATE, AMOUNT, TYPE, BANK_STORENAME]

COLUMN_NAMES = [DATE, AMOUNT, ADJUSTMENT, TYPE, BANK_STORENAME, FILT_STORENAME, EXPENSE]
INC_COL_NAMES = [DATE, AMOUNT, ADJUSTMENT, TYPE, BANK_STORENAME]
CHECK_FOR_DUPLICATES_COL_NAMES = [DATE, AMOUNT, TYPE, BANK_STORENAME]

INC_dtypes = {DATE : 'str', AMOUNT : 'float', ADJUSTMENT : 'float', TYPE : 'str', BANK_STORENAME : "str"}
SB_dtypes = {DATE : 'str', AMOUNT : 'float', ADJUSTMENT : 'float', TYPE : 'str', BANK_STORENAME : "str", FILT_STORENAME : "str", EXPENSE : 'str'}
SB_parse_dates = ['Date']
mydateparser = lambda x: pd.datetime.strptime(x, "%Y-%m-%d")

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

OUT_EXP_DATA_TEMPL = "exp_db.csv"
OUT_INC_DATA_TEMPL = "inc_db.csv"
OUT_DATA_CHKSZ = 3
csv = "*.csv"
EXP_STOR_DB_FNAME = os.path.join('lib', 'storesWithExpenses.json')
BUDGET_FNAME = os.path.join('lib', 'Budget.json')
STORE_PAIR_FNAME = os.path.join('lib', 'storePairs.json')
EXP_FNAME = os.path.join('lib', 'expenses.json')

EXPENSE_DATA_KEY = 'expense'
BUDGET_TOTAL_KEY = 'total'
"""
IGNORABLE_TRANSACTIONS:
DEBIT
'MB-CREDIT CARD/LOC PAY.' - Credit payments rec'v by credit card or paid by debit (can be ignored since credit card transactions are imported and accounted for, thus payments need not be)
'MB-TRANSFER' - Transfer of money between two Scotia accounts
'PC FROM' - Transfer of money between two Scotia accounts
'PC TO' - Transfer of money between two Scotia accounts
'MB-CASH ADVANCE' - Any cash advances taken from credit cards into a debit account (the money from these are used to pay for items, and then are paid off by MB-CREDIT CARD/LOC PAY. Thus can be ignored, 
                    as only the expense needs tracked)
CREDIT
'MB - CASH ADVANCE' - Any cash advances on a credit card's statement (appears with space here instead of just dash)
'PC - PAYMENT FROM' - Any credit card payments
"""

SCOTIA_IGNORABLE_TRANSACTIONS = ['MB-CREDIT CARD/LOC PAY.', 'MB-TRANSFER', 'PC TO', 'PC FROM', 'MB-CASH ADVANCE', 
                                 'MB - CASH ADVANCE', 'PC - PAYMENT FROM']
IGNORABLE_TRANSACTIONS = SCOTIA_IGNORABLE_TRANSACTIONS # FOR FUTURE JUST + NEW ARRAYS OF IGNORABLE TRANSACTIONS

EXPENSE_MISC_STR = "Misc"
MISC_POS_VALUES = ['misc', 'misc.', 'miscellaneous', 'miscellaneous.']

OUTPUT_SEP_STR = "--- --- --- --- --- ---"