import os
import re
import pandas as pd


VERSION = "1.5"
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
INC_UUID = 'Income_UUID'
EXP_UUID = 'Expense_UUID'
CIBC_CARD_NUM_COL = 'CardNumCol'

BUDGET = 'Budget'
REMAINING = 'Remaining'

# SCOTIABANK
SB_BASE_CREDIT_COLNAMES = [DATE, BANK_STORENAME, AMOUNT]
SB_BASE_DEBIT_COLNAMES = [DATE, AMOUNT, NULL, TYPE, BANK_STORENAME]
SB_INC_COLNAMES = [DATE, AMOUNT, TYPE, BANK_STORENAME]
COLUMN_NAMES = [DATE, AMOUNT, ADJUSTMENT, TYPE, BANK_STORENAME,
                FILT_STORENAME, EXPENSE, EXP_UUID, INC_UUID]
INC_COL_NAMES = [DATE, AMOUNT, ADJUSTMENT,
                 TYPE, BANK_STORENAME, INC_UUID, EXP_UUID]
CHECK_FOR_DUPLICATES_COL_NAMES = [DATE, AMOUNT, TYPE, BANK_STORENAME]  
SCOTIABANK = 'Scotiabank'

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
                                 'MB - CASH ADVANCE', 'PC - PAYMENT']
                                
SCOTIA_INC_DTYPES = {DATE: 'str', AMOUNT: 'float', ADJUSTMENT: 'float',
              TYPE: 'str', BANK_STORENAME: "str", INC_UUID: "str", EXP_UUID: "str"}

SCOTIA_EXP_DTYPES = {DATE: 'str', AMOUNT: 'float', ADJUSTMENT: 'float',
               TYPE: 'str', BANK_STORENAME: "str", FILT_STORENAME: "str", EXPENSE: 'str', EXP_UUID: "str", INC_UUID: "str"}
# CIBC
CIBC_BASE_COLNAMES = [DATE, BANK_STORENAME, AMOUNT, NULL]
CIBC_EXPENSE_COLNAMES = [DATE, BANK_STORENAME, AMOUNT, FILT_STORENAME, 
                         EXPENSE, EXP_UUID, INC_UUID]
CIBC_INCOME_COLNAMES = [DATE, BANK_STORENAME, AMOUNT, ADJUSTMENT, INC_UUID, EXP_UUID]
CIBC_CREDIT_COLNAMES = [DATE, BANK_STORENAME, AMOUNT, NULL, CIBC_CARD_NUM_COL]
CIBC_CHECK_FOR_DUPLICATES_COL_NAMES = [DATE, AMOUNT, BANK_STORENAME]
CIBC = 'CIBC'
CIBC_IGNORABLE_TRANSACTIONS = ['INTERNET TRANSFER','PAYMENT THANK YOU','Internet Banking 0000']
CIBC_EXP_DTYPES = {DATE: 'str', AMOUNT: 'float', ADJUSTMENT: 'float',
                  BANK_STORENAME: "str", FILT_STORENAME: "str", EXPENSE: 'str', EXP_UUID: "str", INC_UUID: "str", TYPE: "str"}
CIBC_INC_DTYPES = {DATE: 'str', AMOUNT: 'float', ADJUSTMENT: 'float',
                   BANK_STORENAME: "str", INC_UUID: "str", EXP_UUID: "str",TYPE: "str"}

# BMO
BMO_CARDNUM_COL = 'BMO_CARDNUM'
BMO_ITEMNUM_COL = "Item No."
BMO_DEBIT_COLNAMES = [NULL, TYPE, DATE, AMOUNT, BANK_STORENAME]
BMO_EXPENSE_COLNAMES = [TYPE, DATE, AMOUNT, ADJUSTMENT, BANK_STORENAME, 
                         EXPENSE, EXP_UUID, INC_UUID]
BMO_INCOME_COLNAMES = [TYPE, DATE, AMOUNT, ADJUSTMENT, BANK_STORENAME, INC_UUID, EXP_UUID]
BMO_CREDIT_COLNAMES = [BMO_ITEMNUM_COL, BMO_CARDNUM_COL, DATE, NULL, AMOUNT, BANK_STORENAME]
BMO_CHECK_FOR_DUPLICATES_COL_NAMES = [DATE, AMOUNT, BANK_STORENAME]
BMO = 'BMO'
BMO_IGNORABLE_TRANSACTIONS = ['TRSF FROM', 'CW TF']
BMO_EXP_DTYPES = {DATE: 'str', AMOUNT: 'float', ADJUSTMENT: 'float',
                  BANK_STORENAME: "str", FILT_STORENAME: "str", EXPENSE: 'str', EXP_UUID: "str", INC_UUID: "str"}
BMO_INC_DTYPES = {DATE: 'str', AMOUNT: 'float', ADJUSTMENT: 'float',
                   BANK_STORENAME: "str", INC_UUID: "str", EXP_UUID: "str"}

BMO_DATE_FORMAT = "%Y%m%d"

# RBC
RBC_ACC_NO = "Account No."
RBC_ACC_TYPE = "Account Type"
RBC_USD = "USD"
RBC_INVIS = "Invisible"
RBC_DEBIT_COLNAMES = [RBC_ACC_TYPE, RBC_ACC_NO, DATE, NULL, TYPE, BANK_STORENAME, AMOUNT, RBC_USD, RBC_INVIS]
RBC_EXPENSE_COLNAMES = [DATE, TYPE, BANK_STORENAME, AMOUNT, ADJUSTMENT, 
                         EXPENSE, EXP_UUID, INC_UUID]
RBC_INCOME_COLNAMES = [DATE, TYPE, BANK_STORENAME, AMOUNT, ADJUSTMENT, INC_UUID, EXP_UUID]
RBC_CREDIT_COLNAMES = RBC_DEBIT_COLNAMES

RBC_CHECK_FOR_DUPLICATES_COL_NAMES = [DATE, AMOUNT, BANK_STORENAME]
RBC = 'RBC'
RBC_IGNORABLE_TRANSACTIONS = ['DDA -', 'WWW']
RBC_EXP_DTYPES = {DATE: 'str', AMOUNT: 'float', ADJUSTMENT: 'float',
                  BANK_STORENAME: "str", FILT_STORENAME: "str", EXPENSE: 'str', EXP_UUID: "str", INC_UUID: "str"}
RBC_INC_DTYPES = {DATE: 'str', AMOUNT: 'float', ADJUSTMENT: 'float',
                   BANK_STORENAME: "str", INC_UUID: "str", EXP_UUID: "str"}


# Common Across bank Dataframe Types
pdates_colname = [DATE]

""" Settings options """

# Bank Database Options
BANK_OPTIONS = [SCOTIABANK, CIBC, BMO, RBC]
BANK_CHOICES_KEY = "bank options"
BANK_SELECTION_KEY = "selected banks"

PLOT_SIZE_KEY = "Figure Size"
PLOT_SIZE_DEFAULT = (15, 12)
NUM_ROWS_KEY = "number of rows"
NUM_ROWS_DEFAULT = 1
NUM_COLS_KEY = "number of columns"
NUM_COLS_DEFAULT = 1
PA_FIG_TITL_SIZE_KEY = "Parent figure title size"
PA_FIG_TITL_SIZE_DEFAULT = 8
SUB_FIG_TITL_SIZE_KEY = "Subfigures title size"
SUB_FIG_TITL_SIZE_DEFAULT = 12

MONTH_NUM_ROWS_KEY = "monthly plots number of rows"
MONTH_NUM_ROWS_DEFAULT = 2
MONTH_NUM_COLS_KEY = "monthly plots number of columns"
MONTH_NUM_COLS_DEFAULT = 2

SINGLE_PLOT_SIZE = (12, 8)
SINGLE_PLOT_SIZE_KEY = "Figure size for single plots"

SETTINGS_TEMPL = {  
                    BANK_SELECTION_KEY : [],
                    BANK_CHOICES_KEY: BANK_OPTIONS,
                    PLOT_SIZE_KEY: PLOT_SIZE_DEFAULT,
                    NUM_ROWS_KEY: NUM_ROWS_DEFAULT,
                    NUM_COLS_KEY: NUM_COLS_DEFAULT,       
                    PA_FIG_TITL_SIZE_KEY : PA_FIG_TITL_SIZE_DEFAULT,
                    SUB_FIG_TITL_SIZE_KEY : SUB_FIG_TITL_SIZE_DEFAULT,
                    MONTH_NUM_ROWS_KEY : MONTH_NUM_ROWS_DEFAULT,
                    MONTH_NUM_COLS_KEY : MONTH_NUM_COLS_DEFAULT,
                    SINGLE_PLOT_SIZE_KEY : SINGLE_PLOT_SIZE
}


def mydateparser(x): return pd.datetime.strptime(x, "%Y-%m-%d")

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

RE_EXPR_CIBC = re.compile(
    r'((?<=(Internet Banking) )(.+?)(?=\d+\s\s))'
    r'|((?<=(Electronic Funds Transfer))(.*))'
    r'|((.*)(?=#))'
)

RE_EXPR_BMO = re.compile(
    r'((?<=(\[CW\]|\[PR\]|\[DN\]))(.*)(?=(SENT|RECVD)))'
    r'|((?<=(\[CW\]|\[PR\]|\[DN\]))(.*)(?=#))'
    r'|((?<=(\[CW\]|\[PR\]|\[DN\]))(.*))'
)

RE_EXPR_RBC = re.compile(
    r'((.*)(?=\s\-\s\d+))'
    r'|((.*)(?=\-\s\d+))'
    r'|((.*)(?=#))'
)

OUT_EXP_DATA_TEMPL = "exp_db.csv"
OUT_EXPREC_DATA_TEMPL = "exp_recbin.csv"
OUT_INC_DATA_TEMPL = "inc_db.csv"
OUT_DATA_CHKSZ = 3
csv = "*.csv"
EXP_STOR_DB_FNAME = 'storesWithExpenses.json'
BUDGET_FNAME = 'Budget.json'
STORE_PAIR_FNAME = 'storePairs.json'
EXP_FNAME = 'expenses.json'
NOTES_FNAME = 'monthly_notes.json'
SETTINGS_JSON_NAME = 'settings.json'



EXPENSE_DATA_KEY = 'expense'
BUDGET_TOTAL_KEY = 'total'
EXPENSES_SUBTRACTED_KEY = "subtract"


EXPENSE_MISC_STR = "Misc"
MISC_POS_VALUES = ['misc', 'misc.', 'miscellaneous', 'miscellaneous.']

OUTPUT_SEP_STR = "--- --- --- --- --- ---"

""" Plotting Config"""
MONTH_FREQ = 'M'
YEAR_FREQ = 'Y'

