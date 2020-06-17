import sys, os
import json
import pandas as pd
import glob
import numpy as np
import matplotlib.pyplot as plt
import datetime
import shutil, errno

import expManager
import data_help
import env
import util
import editor


def initialize_dirs(list_of_dirs):
    """
    Initializes the program and returns any paths to new and archived data files.
    """
    for dir in list_of_dirs:
        if not os.path.exists(dir):
            os.mkdir(dir)


def initialize_dbs(json_paths):
    """
    Initializes .json files into their paths given
    """
    for path in json_paths:
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump({}, f)

def find_data_paths(ndata_path, adata_path, db_exp_data_path, db_inc_data_path, output_str=""):
    """
    Searches the given paths ndata_path, adata_path, db_exp_data_path, for csv files
    """
    ndata_filepaths = glob.glob(os.path.join(ndata_path, env.csv), recursive=True)
    db_exp_data_fpaths = glob.glob(os.path.join(db_exp_data_path, env.csv), recursive=True)
    db_inc_data_fpaths = glob.glob(os.path.join(db_inc_data_path, env.csv), recursive=True)
    path_list = [ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths]
    print(env.OUTPUT_SEP_STR)
    print(output_str)
    print(f"Searched {ndata_path} and found: ")
    for files in ndata_filepaths:
        print(f"\t{files}")
    print(f"Searched {db_exp_data_path} and found: ")
    for files in db_exp_data_fpaths:
        print(f"\t{files}")
    print(f"Searched {db_inc_data_path} and found: ")
    for files in db_inc_data_fpaths:
        print(f"\t{files}")
    print(env.OUTPUT_SEP_STR)
    return ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths

def check_for_data(ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths, adata_path, db_exp_data_path, db_inc_data_path):
    """
    Checks db and new folder for any data. 
    Imports the data into expense and income dataframes
    """
    if len(ndata_filepaths) == 0:
        return False

    if len(ndata_filepaths) != 0 and len(db_exp_data_fpaths) != 0 and len(db_inc_data_fpaths) != 0:
        df_new = data_help.load_and_process_csvs(file_paths=ndata_filepaths, strip_cols=[env.TYPE, env.BANK_STORENAME])
        df_inc_new, df_exp_new = data_help.filter_by_amnt(df_new, col_name=env.AMOUNT)
        
        df_exp_new.loc[:, env.FILT_STORENAME] = np.nan
        df_exp_new.loc[:, env.EXPENSE] = np.nan # add NaN column to the expense df.
        

        df_exp = data_help.load_csvs(file_paths=db_exp_data_fpaths, strip_cols=[env.TYPE, env.BANK_STORENAME])
        df_inc = data_help.load_csvs(file_paths=db_inc_data_fpaths, strip_cols=[env.TYPE, env.BANK_STORENAME])

        df_exp = pd.concat([df_exp, df_exp_new])
        df_inc = pd.concat([df_inc, df_inc_new])

    elif len(ndata_filepaths) != 0:
        df_new = data_help.load_and_process_csvs(file_paths=ndata_filepaths)
        df_inc, df_exp = data_help.filter_by_amnt(df_new, col_name=env.AMOUNT)
        df_exp.loc[:, env.EXPENSE] = np.nan # add NaN column to the expense df.
        df_exp.loc[:, env.FILT_STORENAME] = np.nan

    else:
        return False
        
    print("New data loaded locally.")
    print(f"INCOME\n\n{df_inc}\n\nEXPENSES\n\n{df_exp}\n")
    df_exp = data_help.drop_dups(df=df_exp, col_names=env.CHECK_FOR_DUPLICATES_COL_NAMES, ignore_index=True, strip_col=env.TYPE)
    df_inc = data_help.drop_dups(df=df_inc, col_names=env.SB_INC_COLNAMES, ignore_index=True, strip_col=env.TYPE)

    print(f"INCOME\n\n{df_inc}\n\nEXPENSES\n\n{df_exp}\n")
    df_exp.sort_values(by=[env.DATE], inplace=True) # sort data by date.
    df_inc.sort_values(by=[env.DATE], inplace=True) # sort data by date.

    data_help.write_data(df_exp, os.path.join(db_exp_data_path, env.OUT_EXP_DATA_TEMPL))
    data_help.write_data(df_inc, os.path.join(db_inc_data_path, env.OUT_INC_DATA_TEMPL))
    data_help.move_files(files=ndata_filepaths, dest=adata_path)
    print(f"Data imported to {db_inc_data_path} and {db_exp_data_path}. Old files moved to {adata_path}")
    return True

def edit_money_data(db_exp_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path):
    """
    Top level interface for editing databases
    """   
    prompt_chars = ['s', 'e', 'b', 'q']
    user_in = util.get_user_input_for_chars("Would you like to edit: (s) - storenames, (b) - budget amounts or (e) - expense names (q) to quit? ", prompt_chars)
    if user_in == 's':
        editor.store_editor(db_exp_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path)
    elif user_in == 'e':
        editor.expenses_editor(db_exp_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path)
    elif user_in == 'b':
        editor.budget_editor(budg_path)
    

def get_expenses(db_exp_data_fpaths: list, db_inc_data_fpaths: list, stor_pair_path: str, stor_exp_data_path : str, budg_path: str, exp_path: str):
    """
    main method for the importing of expense data
    """
    exp_df = data_help.load_csvs(db_exp_data_fpaths, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)# only using on csv db for now. newest will be last? idk verify later.
    dates = data_help.extract_months(exp_df[env.DATE], start=False)
    expManager.get_budgets(budg_path, exp_path, dates) # check for any missing budgets either this month or any month in the data
    exp_df = expManager.get_expenses_for_rows(exp_df, stor_exp_data_path, stor_pair_path, budg_path)
    data_help.write_data(exp_df, db_exp_data_fpaths[0])

def get_income(db_inc_data_fpaths: list):
    """
    main method for the importing of income data
    """
    inc_df = data_help.load_csvs(db_inc_data_fpaths, dtype=env.INC_dtypes, parse_dates=env.SB_parse_dates)
    inc_df = inc_df[~inc_df.BankStoreName.str.contains("|".join(env.CREDIT_IGNORABLE_TRANSACTIONS))] # filter out any credit payments from debit to here.
    data_help.write_data(inc_df, db_inc_data_fpaths[0])
    print("Finished gathering your income data: \n")
    util.print_fulldf(inc_df)

def view_money_data(db_exp_data_fpaths, db_inc_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path):
    """
    main method for the viewing of data
    """
    df_exp = data_help.load_csvs(db_exp_data_fpaths, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates, index=env.DATE)
    df_inc = data_help.load_csvs(db_inc_data_fpaths, dtype=env.INC_dtypes, parse_dates=env.SB_parse_dates, index=env.DATE) # TODO SHOW NET INCOME ON PLOTS
    dates = data_help.extract_months(df_exp.index.to_series(), start=False)
    expManager.get_budgets(budg_path, exp_path, dates) # check for any missing budgets either this month or any month in the data
    budg_db = data_help.read_jsonFile(budg_path) # load the budget data
    df_budg = pd.DataFrame(budg_db)
    years = data_help.extract_years(df_exp.index.to_series())
    print(" --- --- --- --- ---")
    years_to_show = util.select_indices_of_list("Which of the above year(s) would you like to take a peak at? (e.g. 0 1 2): ", years, return_matches=True)

    for year in years_to_show:
        df_exp = df_exp[year]
        df_inc = df_inc[year]
        df_budg = df_budg.T # transpose to make index date str
        df_budg.set_index(pd.to_datetime(df_budg.index), inplace=True) # set index to date time
        df_budg = df_budg[year] # filter for the year
        df_budg = df_budg.stack().apply(pd.Series).rename(columns={0:env.BUDGET}) # collapse data into multindex frame

        print("\nAll Income this year. ")
        util.print_fulldf(df_inc)
        print("Income grouped by month and store")
        df_inc_per_month = df_inc.groupby([pd.Grouper(freq='M'), env.BANK_STORENAME]).sum()
        util.print_fulldf(df_inc_per_month)

        print("All transaction this year.")
        util.print_fulldf(df_exp)

        print("Totals by store grouped per month.")
        df_exp_stor_per_month = df_exp.groupby([pd.Grouper(freq="M"), env.EXPENSE, env.FILT_STORENAME]).sum()
        util.print_fulldf(df_exp_stor_per_month)

        print("Totals by expense grouped per month with budgets")
        df_exp_per_month = df_exp.groupby([pd.Grouper(freq="M"), env.EXPENSE]).sum()
        df_exp_budg_per_month = pd.concat([df_exp_per_month, df_budg], axis=1)
        df_exp_budg_per_month[env.AMOUNT] = df_exp_budg_per_month[env.AMOUNT].fillna(0)
        df_exp_budg_per_month[env.REMAINING] = df_exp_budg_per_month[env.BUDGET] - df_exp_budg_per_month[env.AMOUNT]
        util.print_fulldf(df_exp_budg_per_month)

        title_templ = "%s\nIncome: %s | Expenses: %s | Budget: %s\nNet Income: %s | Budget Rem.: %s"
        budg_plotter(df_exp_budg_per_month, df_exp_budg_per_month.groupby(level=0).sum(), df_inc, (15,12), nrows=3, ncols=1, 
                     subfigs_per_fig=3, title_templ=title_templ, show=False, sort_by_level=0)
        budg_plotter(df_exp_stor_per_month, df_exp_budg_per_month.groupby(level=0).sum(), df_inc, (15,12), nrows=3, ncols=1, 
                     subfigs_per_fig=3, title_templ=title_templ, show=True, sort_by_level=0)

def budg_plotter(df_to_plot, budget_df, df_inc, figsize=None, nrows=None, ncols=None, subfigs_per_fig=None, title_templ="", show=True, sort_by_level=None):
    """
    Given a multindex dataframe, plots the data
    params:
        df_to_plot - the multiindex df to iterate and plot. 
        budget_df - simplified budget data showing total amount and budget for the month
        figsize - the figure size in tuple format
        nrows - the number of figures to plot in a row
        ncols - the number of figures to plot in a col
        subfigs_per_fig - the number of subfigs to plot on a single figure
        title_templ - the unformatted string for formatting
        show - boolean allowing the function to be chained, showing all plots at once at the end.
        sort_by_level - the level of the multiindex to sort by. Note, use n-1 since the first index is dropped for plotting
    """
    plt.figure(figsize=figsize, facecolor='white')
    plot_idx = 1

    for date, sub_df in df_to_plot.groupby(level=0):
        if plot_idx > subfigs_per_fig:
            plt.tight_layout()
            plt.figure(figsize=figsize, facecolor='white')
            plot_idx = 1

        sub_df.reset_index(level=0, inplace=True, drop=True) # drop date index for plotting

        if sort_by_level != None:
            sub_df = sub_df.sort_index(level=sort_by_level)
        ax = plt.subplot(nrows, ncols, plot_idx)

        month_exp_tot = round(budget_df.loc[f"{date.year}-{date.month}", env.AMOUNT].sum(), 2)
        month_inc_tot = round(df_inc.loc[f"{date.year}-{date.month}", env.AMOUNT].sum(),2)
        budg_tot = round(budget_df.loc[f"{date.year}-{date.month}", env.BUDGET].sum(), 2)
        net_inc = round(month_inc_tot - month_exp_tot, 2)
        budg_re = round(budg_tot - month_exp_tot, 2)

        title = title_templ % (f"{date.year}-{date.month}", month_inc_tot, month_exp_tot, budg_tot, net_inc, budg_re)
        ax.set_title(title)
        sub_ax = sub_df.plot.bar(ax=ax)
        for p in sub_ax.patches:
            ax.annotate(str(round(p.get_height(), 2)), (p.get_x()+p.get_width()/2., p.get_height()), 
                        ha='center', va='center', fontsize=7, fontweight='bold')

        plot_idx += 1
    plt.tight_layout()
    if show == True:
        plt.show()

def backup_data(folderpaths_to_backup, backup_folderpath):
    """
    Performs a backup of folders within folderpaths_to_backup to backup_folderpath
    """
    
    for folderpath in folderpaths_to_backup:
        
        timestamp = datetime.datetime.now().strftime("%m_%d_%Y__%H_%M_%S")
        dest = os.path.join(backup_folderpath, timestamp, folderpath.split(os.sep)[-1])
        print(f"Backing up:\n\t{folderpath} ---> {dest}\n")
        try:

            shutil.copytree(folderpath, dest)
        except OSError as e:
            # If the error was caused because the source wasn't a directory
            if e.errno == errno.ENOTDIR:
                shutil.copy(folderpath, dest)
            else:
                print('Directory not copied. Error: %s' % e)
    print(env.OUTPUT_SEP_STR)

if __name__=="__main__":
    root = sys.path[0]
    data_path = os.path.join(root, 'data')
    ndata_path =  os.path.join(data_path, 'new')
    adata_path = os.path.join(data_path, 'archive')
    db_data_path = os.path.join(data_path, 'db')
    backup_folderpath = os.path.join(root, 'backups')
    db_exp_data_path = os.path.join(db_data_path, 'expenses')
    db_inc_data_path = os.path.join(db_data_path, 'income')
    lib_data_path = os.path.join(root, 'lib')

    list_of_dirs = [data_path,
                    ndata_path,
                    adata_path,
                    db_data_path,
                    db_exp_data_path,
                    db_inc_data_path,
                    lib_data_path,
                    backup_folderpath]

    budg_path = os.path.join(root, env.BUDGET_FNAME)
    stor_exp_data_path = os.path.join(root, env.EXP_STOR_DB_FNAME)
    stor_pair_path = os.path.join(root, env.STORE_PAIR_FNAME)
    exp_path = os.path.join(root, env.EXP_FNAME)

    json_paths = [budg_path,
                  stor_exp_data_path,
                  stor_pair_path,
                  exp_path]

    initialize_dirs(list_of_dirs)
    initialize_dbs(json_paths)
    expManager.setup_expense_names(exp_path) # check for expense list and setup if none are there.
    print("--- --- --- --- --- --- --- --- --- --- --- --- ---")
    print("--- --- --- -- SHOW ME YOUR MONEY -- --- --- --- --")
    print("--- --- --- --- --- V. 0.00 --- --- --- --- --- ---")
    print("WELCOME TO SHOW ME YOUR MONEYYYYY COME ON DOWN!")
    quit = False
    while not quit:
        user_in = util.get_user_input_for_chars("Would you like to (b) backup data (e) edit data, (i) import data, (v) view data or (q) quit? ", ['b', 'e', 'i', 'v', 'q'])
        if user_in != 'q':

            ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths = find_data_paths(ndata_path, adata_path, db_exp_data_path, db_inc_data_path, output_str="LOCATING FILES")

        if user_in == 'b':
            backup_data([db_data_path, lib_data_path], backup_folderpath)
        
        elif user_in == 'e':
            backup_data([db_data_path, lib_data_path], backup_folderpath)
            edit_money_data(db_exp_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path)

        elif user_in == 'i':
            if check_for_data(ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths, adata_path, db_exp_data_path, db_inc_data_path):
                backup_data([db_data_path, lib_data_path], backup_folderpath)
                ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths = find_data_paths(ndata_path, adata_path, db_exp_data_path, db_inc_data_path, output_str="RECHECKING FILES")
                get_expenses(db_exp_data_fpaths, db_inc_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path)
                get_income(db_inc_data_fpaths)
            else:
                print("No data found. Please import some.")
        elif user_in == 'v':
            get_expenses(db_exp_data_fpaths, db_inc_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path)
            get_income(db_inc_data_fpaths)
            view_money_data(db_exp_data_fpaths, db_inc_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path)
        
        elif user_in == 'q':
            print("Gone so soon? Ill be here if you need me. Goodby-")
            print("Transmission Terminated.")
            quit = True 
        
        if user_in != 'q':
            print("---- Done Iteration ----")

# data_help.gather_store_db(df, os.path.join(sys.path[0], 'exp_stor_db.json'), 'StoreName', 'ExpenseName')