import sys
import os
import json
import pandas as pd
import glob
import numpy as np
import matplotlib.pyplot as plt
import datetime
import shutil
import errno

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

def initialize_settings(settings_path):
    settings = data_help.read_jsonFile(settings_path)
    for key in env.SETTINGS_KEYS:
        if key not in settings.keys():
            settings[key] = env.SETTINGS_TEMPL[key]
    data_help.write_to_jsonFile(settings_path, settings)

def find_data_paths(ndata_path, adata_path, db_exp_data_path, db_inc_data_path, output_str=""):
    """
    Searches the given paths ndata_path, adata_path, db_exp_data_path, for csv files
    """
    ndata_filepaths = glob.glob(os.path.join(
        ndata_path, env.csv), recursive=True)
    db_exp_data_fpaths = glob.glob(os.path.join(
        db_exp_data_path, env.csv), recursive=True)
    db_inc_data_fpaths = glob.glob(os.path.join(
        db_inc_data_path, env.csv), recursive=True)
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


def check_for_data(ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths, adata_path,
                   db_exp_data_path, db_inc_data_path, exp_recbin_path, inc_recbin_path, 
                   bankconfig):
    """
    Checks db and new folder for any data. 
    Imports the data into expense and income dataframes
    """
    if len(ndata_filepaths) == 0:
        return False

    bank_sel_json = data_help.read_jsonFile(bankconfig.settings_path)

    if len(ndata_filepaths) != 0 and len(db_exp_data_fpaths) != 0 and len(db_inc_data_fpaths) != 0:
        df_new = data_help.load_and_process_csvs(file_paths=ndata_filepaths, strip_cols=bankconfig.strip_cols,
                                                 data_type=bank_sel_json[env.BANK_SELECTION_KEY])
        df_inc_new, df_exp_new = data_help.filter_by_amnt(df_new, col_name=env.AMOUNT, col_name2=env.NULL, 
                                                          bank_name=bank_sel_json[env.BANK_SELECTION_KEY])
        df_inc_new = data_help.add_columns(
            df_inc_new, [env.ADJUSTMENT, env.INC_UUID, env.EXP_UUID])

        df_exp_new = data_help.add_columns(df_exp_new, [env.FILT_STORENAME, env.EXPENSE, 
                                                        env.ADJUSTMENT, env.EXP_UUID, 
                                                        env.INC_UUID])

        df_exp = data_help.load_csvs(file_paths=db_exp_data_fpaths, strip_cols=bankconfig.strip_cols)
        df_inc = data_help.load_csvs(file_paths=db_inc_data_fpaths, strip_cols=bankconfig.strip_cols)

        df_exp = pd.concat([df_exp, df_exp_new])
        df_inc = pd.concat([df_inc, df_inc_new])

    elif len(ndata_filepaths) != 0:
        df_new = data_help.load_and_process_csvs(file_paths=ndata_filepaths, strip_cols=bankconfig.strip_cols,
                                                 data_type=bank_sel_json[env.BANK_SELECTION_KEY])
        df_inc, df_exp = data_help.filter_by_amnt(
            df_new, col_name=env.AMOUNT, col_name2=env.NULL, bank_name=bank_sel_json[env.BANK_SELECTION_KEY])
        df_inc_new = data_help.add_columns(df_inc, [env.ADJUSTMENT, env.INC_UUID, env.EXP_UUID])

        df_exp_new = data_help.add_columns(df_exp, [env.FILT_STORENAME, env.EXPENSE, env.ADJUSTMENT, 
                                                    env.EXP_UUID, env.INC_UUID])

    else:
        return False

    df_exp_recbin = data_help.load_csv(
        exp_recbin_path, dtype=bankconfig.exp_dtypes, parse_dates=env.pdates_colname)
    df_inc_recbin = data_help.load_csv(
        inc_recbin_path, dtype=bankconfig.inc_dtypes, parse_dates=env.pdates_colname)
    print("New data loaded locally.")
    print(f"INCOME\n\n{df_inc}\n\nYOUR IGNORED INCOME\n\n{df_inc_recbin}\n\nEXPENSES\n\n{df_exp}\n\nYOUR IGNORED EXPENSES\n\n{df_exp_recbin}\n")
    df_exp = data_help.drop_dups(
        df=df_exp, col_names=bankconfig.check_for_dups_cols, ignore_index=True)
    df_inc = data_help.drop_dups(
        df=df_inc, col_names=bankconfig.check_for_dups_cols, ignore_index=True)

    df_exp = data_help.remove_subframe(
        df_to_remove_from=df_exp, df_to_remove=df_exp_recbin, col_names=bankconfig.check_for_dups_cols)
    df_inc = data_help.remove_subframe(
        df_to_remove_from=df_inc, df_to_remove=df_inc_recbin, col_names=bankconfig.check_for_dups_cols)

    print(f"INCOME\n\n{df_inc}\n\nEXPENSES\n\n{df_exp}\n")
    df_exp = data_help.iterate_df_and_add_uuid_to_col(df_exp, env.EXP_UUID)
    df_inc = data_help.iterate_df_and_add_uuid_to_col(df_inc, env.INC_UUID)

    data_help.write_data(df_exp, os.path.join(
        db_exp_data_path, env.OUT_EXP_DATA_TEMPL), sortby=env.DATE, fillna_col=[env.ADJUSTMENT])
    data_help.write_data(df_inc, os.path.join(
        db_inc_data_path, env.OUT_INC_DATA_TEMPL), sortby=env.DATE, fillna_col=[env.ADJUSTMENT])
    timestamp = datetime.datetime.now().strftime("%m_%d_%Y__%H_%M_%S") + ".csv"
    data_help.move_files(files=ndata_filepaths,
                         dest=os.path.join(adata_path, timestamp))
    print(
        f"Data imported to {db_inc_data_path} and {db_exp_data_path}. Old files moved to {adata_path}")
    return True


def edit_money_data(db_exp_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path, exp_path, db_inc_data_fpaths, exp_recbin_path, inc_recbin_path, notes_path, bankconfig=None):
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
    prompt = "\n".join(("Would you like to edit:",
                        "(a) - storenames",
                        "(b) - budget amounts",
                        "(c) - expenses",
                        "(d) - imported data",
                        "(e) - notes",
                        "(f) - settings",
                        "(q) to quit?",
                        "Type Here: "))
    prompt_chars = ['a', 'b', 'c', 'd', 'e', 'f', 'q']
    done = False
    while not done:
        print("          ----|$$| EDITOR MENU |$$|----         ")
        user_in = util.get_user_input_for_chars(prompt, prompt_chars)
        if user_in == 'a':
            editor.store_editor(db_exp_data_fpaths, exp_recbin_path, stor_pair_path,
                                stor_exp_data_path, budg_path, exp_path, bankconfig=bankconfig)
        elif user_in == 'b':
            editor.budget_editor(budg_path)
        elif user_in == 'c':
            editor.expenses_editor(
                db_exp_data_fpaths, exp_recbin_path, stor_pair_path, stor_exp_data_path, budg_path, exp_path, bankconfig=bankconfig)
        elif user_in == 'd':
            editor.df_editor_menu(
                db_inc_data_fpaths, inc_recbin_path, db_exp_data_fpaths, exp_recbin_path, bankconfig=bankconfig)
        elif user_in == 'e':
            editor.notes_editor(db_exp_data_fpaths,
                                db_inc_data_fpaths, notes_path, bankconfig=bankconfig)
        
        elif user_in == 'f':
            editor.edit_settings(bankconfig.settings_path)

        elif user_in == 'q':
            print("Exited editor.")
            done = True


def get_expenses(db_exp_data_fpaths: list, db_inc_data_fpaths: list, stor_pair_path: str, 
                 stor_exp_data_path: str, budg_path: str, exp_path: str, dont_print_cols=None, 
                 bankconfig=None):
    """
    main method for the importing of expense data
    """
    bank_json = data_help.read_jsonFile(bankconfig.settings_path)
    bank_name = bank_json[env.BANK_SELECTION_KEY]
    exp_df = data_help.load_csvs(db_exp_data_fpaths, dtype=bankconfig.exp_dtypes,
                                 parse_dates=env.pdates_colname)  # only using on csv db for now. newest will be last? idk verify later.

    exp_df = data_help.drop_for_substring(exp_df, env.BANK_STORENAME, bankconfig.ignorable_transactions,
                                          "\nRemoving the below expense transactions as they are either an internal bank acct transfer, cash advance or credit payment.")
    dates = data_help.extract_months(exp_df[env.DATE], start=False)
    # check for any missing budgets either this month or any month in the data
    expManager.get_budgets(budg_path, exp_path, dates)
    exp_df = expManager.get_expenses_for_rows(exp_df, stor_exp_data_path, 
                                              stor_pair_path, budg_path, bankconfig, bank_name)
    print("\nFinished gathering your expense data: \n")
    util.print_fulldf(exp_df, dont_print_cols)
    data_help.write_data(exp_df, db_exp_data_fpaths[0])


def get_income(db_inc_data_fpaths: list, dont_print_cols=None, bankconfig=None):
    """
    main method for the importing of income data
    """
    inc_df = data_help.load_csvs(
        db_inc_data_fpaths, dtype=bankconfig.inc_dtypes, parse_dates=env.pdates_colname)
    inc_df = data_help.drop_for_substring(inc_df, env.BANK_STORENAME, bankconfig.ignorable_transactions,
                                          "\nRemoving the below income transactions as they are either an internal bank acct transfer, cash advance or credit payment.")
    data_help.write_data(inc_df, db_inc_data_fpaths[0])
    print("\nFinished gathering your income data: \n")
    util.print_fulldf(inc_df, dont_print_cols)


def view_money_data(db_exp_data_fpaths, db_inc_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path, notes_path, exp_path, 
                    dont_print_cols=None, bankconfig=None, settings_path=None):
    """
    main method for the viewing of data
    params:
        exp_path - path to expenses.json
        dont_print_cols - ignore columns for output to CLI
    """
    df_exp = data_help.load_csvs(
        db_exp_data_fpaths, dtype=bankconfig.exp_dtypes, parse_dates=env.pdates_colname, index=env.DATE)
    df_inc = data_help.load_csvs(db_inc_data_fpaths, dtype=bankconfig.inc_dtypes,
                                 parse_dates=env.pdates_colname, index=env.DATE)  # TODO SHOW NET INCOME ON PLOTS
    df_exp = data_help.combine_and_drop(df_exp, env.AMOUNT, env.ADJUSTMENT, 
                                        'subtract')

    df_inc = data_help.combine_and_drop(df_inc, env.AMOUNT, env.ADJUSTMENT, 
                                        'subtract')
    exp_dict = data_help.read_jsonFile(exp_path)

    settings = data_help.read_jsonFile(settings_path)

    if df_inc.empty:  # set index to datetime if empty.
        df_inc.set_index(pd.to_datetime(df_inc.index), inplace=True)

    budg_db = data_help.read_jsonFile(budg_path)  # load the budget data
    df_budg = pd.DataFrame(budg_db)
    df_budg = df_budg.T  # transpose to make index date str
    df_budg.set_index(pd.to_datetime(df_budg.index),
                      inplace=True)  # set index to date time

    notes_dict = data_help.read_jsonFile(notes_path)

    years = data_help.extract_years(df_exp.index.to_series())
    years_to_show = util.select_indices_of_list(
        "Which of the above year(s) would you like to take a peak at - or 'q' to quit: ", years, return_matches=True, abortchar='q')
    if years_to_show is not None:  # select_indices_of_list returns None if user aborts
        for year in years_to_show:
            df_inc = df_inc[year]  # filter for the year
            print("\nAll Income this year. ")
            util.print_fulldf(df_inc, dont_print_cols=dont_print_cols)
            print("Income grouped by month and store")
            df_inc_per_month = df_inc.groupby(
                [pd.Grouper(freq='M'), env.BANK_STORENAME]).sum()
            util.print_fulldf(df_inc_per_month)
            df_budg = df_budg[year]
            df_budg = df_budg.stack().apply(pd.Series).rename(
                columns={0: env.BUDGET})  # collapse data into multindex frame

            df_exp = df_exp[year]
            print("All expense transactions this year.")
            util.print_fulldf(df_exp, dont_print_cols=dont_print_cols)

            print("Totals by store grouped per month.")
            df_exp_stor_per_month = df_exp.groupby(
                [pd.Grouper(freq="M"), env.EXPENSE, env.FILT_STORENAME]).sum()
            util.print_fulldf(df_exp_stor_per_month)

            print("Totals by expense grouped per month with budgets")
            df_exp_per_month = df_exp.groupby(
                [pd.Grouper(freq="M"), env.EXPENSE]).sum()
            df_exp_budg_per_month = pd.concat(
                [df_exp_per_month, df_budg], axis=1)
            df_exp_budg_per_month[env.AMOUNT] = df_exp_budg_per_month[env.AMOUNT].fillna(
                0)
            df_exp_budg_per_month[env.REMAINING] = df_exp_budg_per_month[env.BUDGET] - \
                df_exp_budg_per_month[env.AMOUNT]
            util.print_fulldf(df_exp_budg_per_month)

            # do not plot in title if none are present
            if len(exp_dict[env.EXPENSES_SUBTRACTED_KEY]) == 0:
                title_templ_for_budg = "%s\nIncome: %s | Expenses: %s | Budget: %s\nNet Income: %s | Budget Rem.: %s"
                subtractable_expenses = None
            else:
                title_templ_for_budg = "%s\nIncome: %s | Expenses: %s | Budget: %s\nNet Income: %s | Budget Rem.: %s | Budget Rem. without %s : %s"
                subtractable_expenses = exp_dict[env.EXPENSES_SUBTRACTED_KEY]

            budg_plotter(df_exp_budg_per_month, df_exp_budg_per_month.groupby(level=0).sum(), df_inc, figsize=settings[env.PLOT_SIZE_KEY], nrows=settings[env.NUM_ROWS_KEY], 
                        ncols=settings[env.NUM_COLS_KEY], subfigs_per_fig=settings[env.NUM_ROWS_KEY]*settings[env.NUM_COLS_KEY], title_templ=title_templ_for_budg, 
                        show=False, sort_by_level=0, notes=notes_dict, subtractable_expenses=subtractable_expenses, tbox_color='wheat', tbox_style='round', tbox_alpha=0.5)
            title_templ_for_stor_plt = "%s\nIncome: %s | Expenses: %s | Budget: %s\nNet Income: %s | Budget Rem.: %s"
            budg_plotter(df_exp_stor_per_month, df_exp_budg_per_month.groupby(level=0).sum(), df_inc, figsize=settings[env.PLOT_SIZE_KEY], nrows=settings[env.NUM_ROWS_KEY], 
                        ncols=settings[env.NUM_COLS_KEY], subfigs_per_fig=settings[env.NUM_ROWS_KEY]*settings[env.NUM_COLS_KEY], title_templ=title_templ_for_stor_plt, 
                        show=True, sort_by_level=0, notes=notes_dict, tbox_color='wheat', tbox_style='round', tbox_alpha=0.5)


def budg_plotter(df_to_plot, budget_df, df_inc, figsize=None, nrows=None, ncols=None, subfigs_per_fig=None, title_templ="", show=True,
                 sort_by_level=None, notes=None, subtractable_expenses=None, tbox_color=None, tbox_style=None, tbox_alpha=None):
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
        notes - Textbox text dict {date : note} to add to figures
        subtractable_expenses - the expenses to subtract when plotting the title information. If none, do not calculate and include in the title
        tbox_color - Colour of textbox, 
        tbox_style - Style of textbox (see matplolib), 
        tbox_alpha - transparency of textbox
    """
    plt.figure(figsize=figsize, facecolor='white')
    plot_idx = 1
    # allows multiindex slicing once sorted.
    df_to_plot.sort_index(level=[0, 1], ascending=[True, True], inplace=True)
    for date, sub_df in df_to_plot.groupby(level=0):
        str_date = date.strftime("%Y-%m-%d")
        date_key = f"{date.year}-{date.month}"
        if plot_idx > subfigs_per_fig:
            plt.tight_layout()
            plt.figure(figsize=figsize, facecolor='white')
            plot_idx = 1

        # drop date index for plotting
        sub_df.reset_index(level=0, inplace=True, drop=True)

        if sort_by_level != None:
            sub_df = sub_df.sort_index(level=sort_by_level)

        ax = plt.subplot(nrows, ncols, plot_idx)

        month_exp_tot = round(budget_df.loc[date_key, env.AMOUNT].sum(), 2)

        if date_key in df_inc.index:  # detect whether there was income that month.
            month_inc_tot = round(df_inc.loc[date_key, env.AMOUNT].sum(), 2)
        else:
            month_inc_tot = 0

        budg_tot = round(budget_df.loc[date_key, env.BUDGET].sum(), 2)
        net_inc = round(month_inc_tot - month_exp_tot, 2)
        budg_re = round(budg_tot - month_exp_tot, 2)

        if subtractable_expenses is not None:  # check for any subtractable expenses when plotting to title
            budg_re_with_subtractions = budg_re
            for exp in subtractable_expenses:
                subtr_amnt = round(
                    df_to_plot.loc[(str_date, exp), env.REMAINING].sum(), 2)
                budg_re_with_subtractions -= subtr_amnt

            budg_re_with_subtractions = round(budg_re_with_subtractions, 2)
            title = title_templ % (f"{date.month_name()} {date.year}", month_inc_tot, month_exp_tot,
                                   budg_tot, net_inc, budg_re, subtractable_expenses, budg_re_with_subtractions)

        else:
            title = title_templ % (f"{date.month_name()} {date.year}",
                                   month_inc_tot, month_exp_tot, budg_tot, net_inc, budg_re)
        ax.set_title(title)
        sub_ax = sub_df.plot.bar(ax=ax)

        # check to ensure params are passed, and notes dict contains the date
        if (tbox_color is not None and tbox_style is not None and tbox_alpha is not None) and str_date in notes.keys():
            if notes[str_date] != "":  # ignore adding box if note is empty
                tbox_txt = bytes(notes[str_date], 'UTF-8')  # encode to bytes
                # decode to get the newline characters working
                tbox_txt = tbox_txt.decode('unicode-escape')
                plt.text(0.15, 0.95, tbox_txt, transform=sub_ax.transAxes, fontsize=8, verticalalignment='top',
                         bbox={'boxstyle': tbox_style, 'facecolor': tbox_color, 'alpha': tbox_alpha})

        for l in sub_ax.get_xticklabels():
            l.set_rotation(45)
            l.set_ha('right')
        for p in sub_ax.patches:
            ax.annotate(str(round(p.get_height(), 2)), (p.get_x()+p.get_width()/2., p.get_height()),
                        ha='center', va='center', fontsize=7, fontweight='bold')
            if p.get_height() < 0:  # sets the color of the bar to red if below zero
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
        dest = os.path.join(backup_folderpath, timestamp,
                            folderpath.split(os.sep)[-1])
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


if __name__ == "__main__":

    root = sys.path[0]
    data_path = os.path.join(root, 'data')
    ndata_path = os.path.join(data_path, 'new')
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

    budg_path = os.path.join(lib_data_path, env.BUDGET_FNAME)
    stor_exp_data_path = os.path.join(lib_data_path, env.EXP_STOR_DB_FNAME)
    stor_pair_path = os.path.join(lib_data_path, env.STORE_PAIR_FNAME)
    exp_path = os.path.join(lib_data_path, env.EXP_FNAME)
    notes_path = os.path.join(lib_data_path, env.NOTES_FNAME)
    settings_path = os.path.join(lib_data_path, env.SETTINGS_JSON_NAME)

    json_paths = [budg_path,
                  stor_exp_data_path,
                  stor_pair_path,
                  exp_path,
                  notes_path,
                  settings_path]

    initialize_dirs(list_of_dirs)
    initialize_dbs(json_paths)

    # check for expense list and setup if none are there.
    expManager.setup_expense_names(exp_path)
    # check for bank choice and setup if no choice is there.
    expManager.choose_bank(settings_path)
    # initialize settings
    initialize_settings(settings_path)

    bank_sel_json = data_help.read_jsonFile(settings_path)
    if bank_sel_json[env.BANK_SELECTION_KEY] == env.SCOTIABANK:
        bankconfig = util.Bankconfig(
            settings_path = settings_path,
            strip_cols = [env.TYPE, env.BANK_STORENAME],
            check_for_dups_cols = env.CHECK_FOR_DUPLICATES_COL_NAMES,
            regex_str = env.RE_EXPR,
            ignorable_transactions = env.SCOTIA_IGNORABLE_TRANSACTIONS,
            exp_colnames = env.COLUMN_NAMES,
            inc_colnames = env.SB_INC_COLNAMES,
            exp_dtypes=env.SCOTIA_EXP_DTYPES,
            inc_dtypes=env.SCOTIA_INC_DTYPES
        )

    elif bank_sel_json[env.BANK_SELECTION_KEY] == env.CIBC:
        bankconfig = util.Bankconfig(
            settings_path = settings_path,
            strip_cols = [env.BANK_STORENAME],
            check_for_dups_cols = env.CIBC_CHECK_FOR_DUPLICATES_COL_NAMES,
            regex_str = env.RE_EXPR_CIBC,
            ignorable_transactions = env.CIBC_IGNORABLE_TRANSACTIONS,
            exp_colnames = env.CIBC_EXPENSE_COLNAMES, 
            inc_colnames = env.CIBC_INCOME_COLNAMES,
            exp_dtypes=env.CIBC_EXP_DTYPES,
            inc_dtypes=env.CIBC_INC_DTYPES
        )


    initialize_csvs([exp_recbin_path, inc_recbin_path], 
                    [bankconfig.exp_colnames, bankconfig.inc_colnames])
    print("--- --- --- --- --- --- --- --- --- --- --- --- ---")
    print("--- --- --- -- SHOW ME YOUR MONEY -- --- --- --- --")
    print(f"--- --- --- --- --- V. {env.VERSION} --- --- --- --- --- ---")
    print("WELCOME TO SHOW ME YOUR MONEYYYYY COME ON DOWN!")
    quit = False
    while not quit:
        print("          ----|$$| MAIN MENU |$$|----         ")
        user_in = util.get_user_input_for_chars(
            "Would you like to:\n(b) - backup data\n(e) - edit data\n(i) - import data\n(v) - view data\n(h) - print help docs\n(q) - quit?\nType here: ", ['b', 'e', 'i', 'v', 'h', 'q'])
        if user_in == 'h':
            data_help.print_file(help_doc_path)

        if user_in != 'q':
            ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths = find_data_paths(
                ndata_path, adata_path, db_exp_data_path, db_inc_data_path, output_str="LOCATING FILES")

            if user_in == 'i':
                backup_data([db_data_path, lib_data_path], backup_folderpath)
                if check_for_data(ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths, adata_path,
                                  db_exp_data_path, db_inc_data_path, exp_recbin_path, inc_recbin_path, 
                                  bankconfig):
                    ndata_filepaths, db_exp_data_fpaths, db_inc_data_fpaths = find_data_paths(
                        ndata_path, adata_path, db_exp_data_path, db_inc_data_path, output_str="RECHECKING FILES")
                    get_income(db_inc_data_fpaths, bankconfig=bankconfig)
                    get_expenses(db_exp_data_fpaths, db_inc_data_fpaths,
                                 stor_pair_path, stor_exp_data_path, budg_path, 
                                 exp_path, bankconfig=bankconfig)

                else:
                    print(
                        f"No data found. Please place files in {ndata_path} so I can eat.")

            # if import wasnt selected and there is no data csv's to load... skip running the program functions and warn user
            elif len(db_exp_data_fpaths) != 0:
                if user_in == 'b':
                    backup_data([data_path, lib_data_path], backup_folderpath)

                elif user_in == 'e':
                    backup_data([db_data_path, lib_data_path],
                                backup_folderpath)
                    edit_money_data(db_exp_data_fpaths, stor_pair_path, stor_exp_data_path, budg_path,
                                    exp_path, db_inc_data_fpaths, exp_recbin_path, inc_recbin_path,  
                                    notes_path, bankconfig=bankconfig)
                elif user_in == 'v':
                    get_income(db_inc_data_fpaths, bankconfig=bankconfig)
                    get_expenses(db_exp_data_fpaths, db_inc_data_fpaths,
                                 stor_pair_path, stor_exp_data_path, budg_path, 
                                 exp_path, bankconfig=bankconfig)
                    view_money_data(db_exp_data_fpaths, db_inc_data_fpaths, stor_pair_path, stor_exp_data_path,
                                    budg_path, notes_path, exp_path, dont_print_cols=[env.INC_UUID, env.EXP_UUID], 
                                    bankconfig=bankconfig, settings_path=settings_path)
            else:
                print(
                    f"No data found. Please place files in {ndata_path} so I can eat.")

        if user_in == 'q':
            print("Gone so soon? Ill be here if you need me. Goodby-")
            print("Transmission Terminated.")
            quit = True


# data_help.gather_store_db(df, os.path.join(sys.path[0], 'exp_stor_db.json'), 'StoreName', 'ExpenseName')
