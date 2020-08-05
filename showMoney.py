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

def initialize_csvs(list_of_csvs, list_of_cols):
    """
    Initializes empty csv files given by paths list_of_csvs
    """
    
    for item in zip(list_of_csvs, list_of_cols):
        if not os.path.exists(item[0]):
            df = pd.DataFrame(columns=item[1])
            data_help.write_data(df, item[0])

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

def check_for_data(ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths, adata_path, db_exp_data_path, db_inc_data_path, exp_recbin_path, inc_recbin_path):
    """
    Checks db and new folder for any data. 
    Imports the data into expense and income dataframes
    """
    if len(ndata_filepaths) == 0:
        return False

    if len(ndata_filepaths) != 0 and len(db_exp_data_fpaths) != 0 and len(db_inc_data_fpaths) != 0:
        df_new = data_help.load_and_process_csvs(file_paths=ndata_filepaths, strip_cols=[env.TYPE, env.BANK_STORENAME])
        df_inc_new, df_exp_new = data_help.filter_by_amnt(df_new, col_name=env.AMOUNT)
        df_inc_new = data_help.add_columns(df_inc_new, [env.ADJUSTMENT])

        df_exp_new = data_help.add_columns(df_exp_new, [env.FILT_STORENAME, env.EXPENSE, env.ADJUSTMENT])

        df_exp = data_help.load_csvs(file_paths=db_exp_data_fpaths, strip_cols=[env.TYPE, env.BANK_STORENAME])
        df_inc = data_help.load_csvs(file_paths=db_inc_data_fpaths, strip_cols=[env.TYPE, env.BANK_STORENAME])

        df_exp = pd.concat([df_exp, df_exp_new])
        df_inc = pd.concat([df_inc, df_inc_new])

    elif len(ndata_filepaths) != 0:
        df_new = data_help.load_and_process_csvs(file_paths=ndata_filepaths, strip_cols=[env.TYPE, env.BANK_STORENAME])
        df_inc, df_exp = data_help.filter_by_amnt(df_new, col_name=env.AMOUNT)
        df_inc_new = data_help.add_columns(df_inc_new, [env.ADJUSTMENT])

        df_exp_new = data_help.add_columns(df_exp_new, [env.FILT_STORENAME, env.EXPENSE, env.ADJUSTMENT])

    else:
        return False

    df_exp_recbin = data_help.load_csv(exp_recbin_path, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)
    df_inc_recbin = data_help.load_csv(inc_recbin_path, dtype=env.INC_dtypes, parse_dates=env.SB_parse_dates)   
    print("New data loaded locally.")
    print(f"INCOME\n\n{df_inc}\n\nYOUR IGNORED INCOME\n\n{df_inc_recbin}\n\nEXPENSES\n\n{df_exp}\n\nYOUR IGNORED EXPENSES\n\n{df_exp_recbin}\n")
    df_exp = data_help.drop_dups(df=df_exp, col_names=env.CHECK_FOR_DUPLICATES_COL_NAMES, ignore_index=True, strip_col=env.TYPE)
    df_inc = data_help.drop_dups(df=df_inc, col_names=env.CHECK_FOR_DUPLICATES_COL_NAMES, ignore_index=True, strip_col=env.TYPE)

    df_exp = data_help.remove_subframe(df_to_remove_from=df_exp, df_to_remove=df_exp_recbin, col_names=env.CHECK_FOR_DUPLICATES_COL_NAMES)
    df_inc = data_help.remove_subframe(df_to_remove_from=df_inc, df_to_remove=df_inc_recbin, col_names=env.SB_INC_COLNAMES)

    print(f"INCOME\n\n{df_inc}\n\nEXPENSES\n\n{df_exp}\n")

    data_help.write_data(df_exp, os.path.join(db_exp_data_path, env.OUT_EXP_DATA_TEMPL), sortby=env.DATE)
    data_help.write_data(df_inc, os.path.join(db_inc_data_path, env.OUT_INC_DATA_TEMPL), sortby=env.DATE)
    timestamp = datetime.datetime.now().strftime("%m_%d_%Y__%H_%M_%S") + ".csv"
    data_help.move_files(files=ndata_filepaths, dest=os.path.join(adata_path, timestamp))
    print(f"Data imported to {db_inc_data_path} and {db_exp_data_path}. Old files moved to {adata_path}")
    return True

def edit_money_data(db_exp_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path, db_inc_data_fpaths, exp_recbin_path, inc_recbin_path):
    """
    Top level interface for editing databases
    params:
        db_exp_data_fpaths - the paths to any csv files under db folder
        stor_pair_path - the path to the store pairs json database under lib
        stor_exp_data_path - the path to the store expense json database under lib
        budg_path - the path to the budget database under lib
        exp_path - the path to the expense json database under lib
        db_inc_data_fpaths - the path to the income csv's found under db folder
        exp_recbin_path - the path to the expense recycle bin csv
        inc_recbin_path - the path to the income recycle bin csv
    """   
    prompt = "Would you like to edit:\n(a) - storenames\n(b) - budget amounts\n(c) - expenses\n(d) - imported data\n(q) to quit?\nType Here: "
    prompt_chars = ['a', 'b', 'c', 'd', 'q']
    done = False
    while not done:
        print("          ----|$$| EDITOR MENU |$$|----         ")
        user_in = util.get_user_input_for_chars(prompt, prompt_chars)
        if user_in == 'a':
            editor.store_editor(db_exp_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path)
        elif user_in == 'b':
            editor.budget_editor(budg_path)
        elif user_in == 'c':
            editor.expenses_editor(db_exp_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path)
        elif user_in == 'd':
            editor.df_editor_menu(db_inc_data_fpaths, inc_recbin_path, db_exp_data_fpaths, exp_recbin_path)

        elif user_in == 'q':
            print("Exited editor.")
            done = True

def get_expenses(db_exp_data_fpaths: list, db_inc_data_fpaths: list, stor_pair_path: str, stor_exp_data_path : str, budg_path: str, exp_path: str):
    """
    main method for the importing of expense data
    """
    exp_df = data_help.load_csvs(db_exp_data_fpaths, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates)# only using on csv db for now. newest will be last? idk verify later.
    exp_df = data_help.drop_for_substring(exp_df, env.BANK_STORENAME, env.IGNORABLE_TRANSACTIONS, 
                                          "\nRemoving the below expense transactions as they are either an internal bank acct transfer, cash advance or credit payment.")
    dates = data_help.extract_months(exp_df[env.DATE], start=False)
    expManager.get_budgets(budg_path, exp_path, dates) # check for any missing budgets either this month or any month in the data
    exp_df = expManager.get_expenses_for_rows(exp_df, stor_exp_data_path, stor_pair_path, budg_path)
    data_help.write_data(exp_df, db_exp_data_fpaths[0])

def get_income(db_inc_data_fpaths: list):
    """
    main method for the importing of income data
    """
    inc_df = data_help.load_csvs(db_inc_data_fpaths, dtype=env.INC_dtypes, parse_dates=env.SB_parse_dates)
    inc_df = data_help.drop_for_substring(inc_df, env.BANK_STORENAME, env.IGNORABLE_TRANSACTIONS, 
                                          "\nRemoving the below income transactions as they are either an internal bank acct transfer, cash advance or credit payment.")
    data_help.write_data(inc_df, db_inc_data_fpaths[0])
    print("\nFinished gathering your income data: \n")
    util.print_fulldf(inc_df)

def view_money_data(db_exp_data_fpaths, db_inc_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path):
    """
    main method for the viewing of data
    """
    df_exp = data_help.load_csvs(db_exp_data_fpaths, dtype=env.SB_dtypes, parse_dates=env.SB_parse_dates, index=env.DATE)
    df_inc = data_help.load_csvs(db_inc_data_fpaths, dtype=env.INC_dtypes, parse_dates=env.SB_parse_dates, index=env.DATE) # TODO SHOW NET INCOME ON PLOTS
    df_exp = data_help.combine_and_drop(df_exp, env.AMOUNT, env.ADJUSTMENT, 'subtract')

    df_inc = data_help.combine_and_drop(df_inc, env.AMOUNT, env.ADJUSTMENT, 'subtract')

    if df_inc.empty: # set index to datetime if empty.
        df_inc.set_index(pd.to_datetime(df_inc.index), inplace=True)
    
    budg_db = data_help.read_jsonFile(budg_path) # load the budget data
    df_budg = pd.DataFrame(budg_db)
    df_budg = df_budg.T # transpose to make index date str
    df_budg.set_index(pd.to_datetime(df_budg.index), inplace=True) # set index to date time

    years = data_help.extract_years(df_exp.index.to_series())
    years_to_show = util.select_indices_of_list("Which of the above year(s) would you like to take a peak at - or 'q' to quit: ", years, return_matches=True, abortable=True, abortchar='q')
    if years_to_show is not None: # select_indices_of_list returns None if user aborts
        for year in years_to_show:
            df_inc = df_inc[year] # filter for the year
            print("\nAll Income this year. ")
            util.print_fulldf(df_inc)
            print("Income grouped by month and store")
            df_inc_per_month = df_inc.groupby([pd.Grouper(freq='M'), env.BANK_STORENAME]).sum()
            util.print_fulldf(df_inc_per_month)

            df_budg = df_budg[year] 
            df_budg = df_budg.stack().apply(pd.Series).rename(columns={0:env.BUDGET}) # collapse data into multindex frame

            df_exp = df_exp[year]
            print("All transactions this year.")
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

        if f"{date.year}-{date.month}" in df_inc.index: # detect whether there was income that month.
            month_inc_tot = round(df_inc.loc[f"{date.year}-{date.month}", env.AMOUNT].sum(),2)
        else:
            month_inc_tot = 0

        budg_tot = round(budget_df.loc[f"{date.year}-{date.month}", env.BUDGET].sum(), 2)
        net_inc = round(month_inc_tot - month_exp_tot, 2)
        budg_re = round(budg_tot - month_exp_tot, 2)

        title = title_templ % (f"{date.month_name()} {date.year}", month_inc_tot, month_exp_tot, budg_tot, net_inc, budg_re)
        ax.set_title(title)
        sub_ax = sub_df.plot.bar(ax=ax)

        for l in sub_ax.get_xticklabels():
            l.set_rotation(45)
            l.set_ha('right')
        for p in sub_ax.patches:
            ax.annotate(str(round(p.get_height(), 2)), (p.get_x()+p.get_width()/2., p.get_height()), 
                        ha='center', va='center', fontsize=7, fontweight='bold')
            if p.get_height() < 0: # sets the color of the bar to red if below zero
                p.set_color('#ff2b2b')

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
    help_doc_path = os.path.join(root, 'README.md')
    recbin_path = os.path.join(data_path, 'recyclebin')
    exp_recbin_data_path = os.path.join(recbin_path, 'expenses')
    inc_recbin_data_path = os.path.join(recbin_path, 'income')
    exp_recbin_path = os.path.join(exp_recbin_data_path, 'exp_recbin.csv')
    inc_recbin_path = os.path.join(inc_recbin_data_path, 'inc_recbin.csv')

    list_of_dirs = [data_path,
                    ndata_path,
                    adata_path,
                    db_data_path,
                    db_exp_data_path,
                    db_inc_data_path,
                    lib_data_path,
                    backup_folderpath,
                    recbin_path,
                    exp_recbin_data_path,
                    inc_recbin_data_path]

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
    initialize_csvs([exp_recbin_path, inc_recbin_path], [env.COLUMN_NAMES, env.SB_INC_COLNAMES])
    expManager.setup_expense_names(exp_path) # check for expense list and setup if none are there.
    print("--- --- --- --- --- --- --- --- --- --- --- --- ---")
    print("--- --- --- -- SHOW ME YOUR MONEY -- --- --- --- --")
    print(f"--- --- --- --- --- V. {env.VERSION} --- --- --- --- --- ---")
    print("WELCOME TO SHOW ME YOUR MONEYYYYY COME ON DOWN!")
    quit = False
    while not quit:
        print("          ----|$$| MAIN MENU |$$|----         ")
        user_in = util.get_user_input_for_chars("Would you like to:\n(b) - backup data\n(e) - edit data\n(i) - import data\n(v) - view data\n(h) - print help docs\n(q) - quit?\nType here: ", ['b', 'e', 'i', 'v', 'h', 'q'])
        if user_in == 'h':
            data_help.print_file(help_doc_path)
        
        if user_in != 'q':
            ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths = find_data_paths(ndata_path, adata_path, db_exp_data_path, db_inc_data_path, output_str="LOCATING FILES")

            if user_in == 'i': 
                backup_data([db_data_path, lib_data_path], backup_folderpath)
                if check_for_data(ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths, adata_path, db_exp_data_path, db_inc_data_path, exp_recbin_path, inc_recbin_path):
                    ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths = find_data_paths(ndata_path, adata_path, db_exp_data_path, db_inc_data_path, output_str="RECHECKING FILES")
                    get_income(db_inc_data_fpaths)
                    get_expenses(db_exp_data_fpaths, db_inc_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path)
                    
                else:
                    print(f"No data found. Please place files in {ndata_path} so I can eat.")

            elif len(db_exp_data_fpaths) != 0: # if import wasnt selected and there is no data csv's to load... skip running the program functions and warn user
                if user_in == 'b':
                    backup_data([data_path, lib_data_path], backup_folderpath)
                
                elif user_in == 'e':
                    backup_data([db_data_path, lib_data_path], backup_folderpath)
                    edit_money_data(db_exp_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path, db_inc_data_fpaths, exp_recbin_path, inc_recbin_path)
                elif user_in == 'v':
                    get_income(db_inc_data_fpaths)
                    get_expenses(db_exp_data_fpaths, db_inc_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path)
                    view_money_data(db_exp_data_fpaths, db_inc_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path)
            else:
                print(f"No data found. Please place files in {ndata_path} so I can eat.")

        if user_in == 'q':
            print("Gone so soon? Ill be here if you need me. Goodby-")
            print("Transmission Terminated.")
            quit = True 
    

# data_help.gather_store_db(df, os.path.join(sys.path[0], 'exp_stor_db.json'), 'StoreName', 'ExpenseName')