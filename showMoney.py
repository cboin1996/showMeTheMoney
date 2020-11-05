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
    for key in env.SETTINGS_TEMPL.keys(): # add keys in globvar
        if key not in settings.keys():
            settings[key] = env.SETTINGS_TEMPL[key]
    
    keys_to_rem = []
    for key in settings.keys(): # remove keys not in globvar
        if key not in env.SETTINGS_TEMPL.keys():
            keys_to_rem.append(key)
    
    for key in keys_to_rem:
        settings.pop(key)

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

    if len(ndata_filepaths) != 0 and len(db_exp_data_fpaths) != 0 and len(db_inc_data_fpaths) != 0:
        df_new = data_help.load_and_process_csvs(file_paths=ndata_filepaths, strip_cols=bankconfig.strip_cols,
                                                 data_type=bankconfig.selection)
        util.print_fulldf(df_new)

        
        df_inc_new, df_exp_new = data_help.filter_by_amnt(df_new, col_name=env.AMOUNT, col_name2=env.NULL, 
                                                          bank_name=bankconfig.selection)
        df_inc_new = data_help.add_columns(
            df_inc_new, [env.ADJUSTMENT, env.INC_UUID, env.EXP_UUID])

        df_exp_new = data_help.add_columns(df_exp_new, [env.FILT_STORENAME, env.EXPENSE, 
                                                        env.ADJUSTMENT, env.EXP_UUID, 
                                                        env.INC_UUID])

        df_exp = data_help.load_csvs(file_paths=db_exp_data_fpaths, strip_cols=bankconfig.strip_cols, dtype=bankconfig.exp_dtypes)
        df_inc = data_help.load_csvs(file_paths=db_inc_data_fpaths, strip_cols=bankconfig.strip_cols, dtype=bankconfig.inc_dtypes)
        df_exp = pd.concat([df_exp, df_exp_new])
        df_inc = pd.concat([df_inc, df_inc_new])

    elif len(ndata_filepaths) != 0:
        df_new = data_help.load_and_process_csvs(file_paths=ndata_filepaths, strip_cols=bankconfig.strip_cols,
                                                 data_type=bankconfig.selection)
        df_inc, df_exp = data_help.filter_by_amnt(
            df_new, col_name=env.AMOUNT, col_name2=env.NULL, bank_name=bankconfig.selection)
        df_inc_new = data_help.add_columns(df_inc, [env.ADJUSTMENT, env.INC_UUID, env.EXP_UUID])

        df_exp_new = data_help.add_columns(df_exp, [env.FILT_STORENAME, env.EXPENSE, env.ADJUSTMENT, 
                                                    env.EXP_UUID, env.INC_UUID])

    else:
        return False

    df_exp_recbin = data_help.load_csvs(
        [exp_recbin_path], dtype=bankconfig.exp_dtypes, parse_dates=env.pdates_colname)
    df_inc_recbin = data_help.load_csvs(
        [inc_recbin_path], dtype=bankconfig.inc_dtypes, parse_dates=env.pdates_colname)
    print("New data loaded locally.\n\n")
    print("INCOME\n\n")
    util.print_fulldf(df_inc)
    print("IGNORED INCOME\n\n")
    util.print_fulldf(df_inc_recbin)
    print("EXPENSES\n\n")
    util.print_fulldf(df_exp)
    print("YOUR IGNORED EXPENSES\n\n")
    util.print_fulldf(df_exp_recbin)

    df_exp = data_help.drop_dups(
        df=df_exp, col_names=bankconfig.check_for_dups_cols, ignore_index=True)
    df_inc = data_help.drop_dups(
        df=df_inc, col_names=bankconfig.check_for_dups_cols, ignore_index=True)

    df_exp = data_help.remove_subframe(
        df_to_remove_from=df_exp, df_to_remove=df_exp_recbin, col_names=bankconfig.check_for_dups_cols)
    df_inc = data_help.remove_subframe(
        df_to_remove_from=df_inc, df_to_remove=df_inc_recbin, col_names=bankconfig.check_for_dups_cols)

    print("INCOME WITHOUT DUPS\n\n")
    util.print_fulldf(df_inc)
    print("EXPENSES WITHOUT DUPS\n\n")
    util.print_fulldf(df_exp)

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
    exp_df = data_help.load_csvs(db_exp_data_fpaths, dtype=bankconfig.exp_dtypes,
                                 parse_dates=env.pdates_colname)  # only using on csv db for now. newest will be last? idk verify later.

    exp_df = data_help.drop_for_substring(exp_df, env.BANK_STORENAME, bankconfig.ignorable_transactions,
                                          "\nRemoving the below expense transactions as they are either an internal bank acct transfer, cash advance or credit payment.")
    dates = data_help.extract_months(exp_df[env.DATE], start=False)
    # check for any missing budgets either this month or any month in the data
    expManager.get_budgets(budg_path, exp_path, dates)
    exp_df = expManager.get_expenses_for_rows(exp_df, stor_exp_data_path, 
                                              stor_pair_path, budg_path, bankconfig)
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

def choose_months_in_dfs(df_exp,df_budg,df_inc, years):
    for year in years:
        months = data_help.extract_year_month(df_exp[year].index.to_series())
        months.sort()
        months_to_show = util.select_indices_of_list(f"Which months in {year} do you want to see? 'a' for all: ", list(months), return_matches=True,
                                                        abortchar='q', ret_all_char='a')
        if months_to_show == None:
            return None, None, None, None
        dfs = data_help.drop_dt_indices_not_in_selection(months_to_show, months, [df_exp, df_budg, df_inc])
    
    return dfs[0], dfs[1], dfs[2], months_to_show

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
        "Which of the above year(s) would you like to take a peak at, 'a' for all: ", years, return_matches=True, abortchar='q', 
            ret_all_char='a')
    
    if years_to_show is None:  # select_indices_of_list returns None if user aborts 
        return None

    dfs = data_help.drop_dt_indices_not_in_selection(years_to_show, years, [df_exp, df_budg, df_inc])
    df_exp = dfs[0]
    df_budg = dfs[1]
    df_inc = dfs[2]
    if df_exp is None: # quit condition
        return None

    freq, freq_desc = get_plotting_frequency()
    if freq ==  None:
        return None

    if freq == env.YEAR_FREQ:
        plot_for_date(years, dont_print_cols, exp_dict, df_inc, df_budg,df_exp, settings, 
            notes_dict, freq=freq, freq_desc=freq_desc)
    elif freq == env.MONTH_FREQ:
        df_exp, df_budg, df_inc, months = choose_months_in_dfs(df_exp,df_budg,df_inc, years_to_show)
        if df_exp is None:
            return None
        
        plot_for_date(years, dont_print_cols, exp_dict, df_inc, df_budg, df_exp, 
            settings, notes_dict, freq=env.MONTH_FREQ, freq_desc=freq_desc, months=months)
    elif freq == 'b':
 
        df_exp_mnth, df_budg_mnth, df_inc_mnth, months = choose_months_in_dfs(df_exp,df_budg,df_inc, years_to_show)
        if df_exp_mnth is None:
            return None
        plot_for_date(years, dont_print_cols, exp_dict, df_inc_mnth, df_budg_mnth, df_exp_mnth, 
            settings, notes_dict, freq=env.MONTH_FREQ, freq_desc='month', override_show=True, months=months)
        plot_for_date(years, dont_print_cols, exp_dict, df_inc, 
            df_budg,df_exp, settings, notes_dict, freq=env.YEAR_FREQ, freq_desc='year')
    
    else:
        pass

def get_plotting_frequency():
    sel = util.get_user_input_for_chars("View by month (m) by year (y) or both (b)? (q) aborts. ", ['m', 'y', 'b', 'q'])

    if sel == 'q':
        return None , None
    elif sel == 'm':
        return env.MONTH_FREQ, 'month'
    elif sel == 'y':
        return env.YEAR_FREQ, 'year'
    elif sel == 'b':
        return sel, 'both'

def plot_for_date(years, dont_print_cols, exp_dict, df_inc, df_budg, df_exp, settings, notes_dict, freq, freq_desc,
                    override_show=False, months=None):
    show_plot1 = False
    show_plot2 = True
    if override_show == True:
        show_plot2 = False
    
    if months is not None:
        time_flag = f"{months}"
    else:
        time_flag = f"{years}"
  # filter for the year
    print(f"\nAll Income in {time_flag}. ")
    util.print_fulldf(df_inc, dont_print_cols=dont_print_cols)
    print(f"Income grouped by {freq_desc} and store")
    df_inc_per_freq_stores = df_inc.groupby(
        [pd.Grouper(freq=freq), env.BANK_STORENAME]).sum()
    util.print_fulldf(df_inc_per_freq_stores) 

    df_inc_per_freq= df_inc.groupby(
        [pd.Grouper(freq=freq)]).sum()

    print(f"All budget info in {time_flag}")
    if freq == env.YEAR_FREQ:
        df_budg_per_freq = df_budg.groupby([pd.Grouper(freq=freq)]).sum() # compile for the frequency
    else:
        df_budg_per_freq = df_budg
    df_budg_per_freq = df_budg_per_freq.stack().apply(pd.Series).rename(columns={0: env.BUDGET})  # collapse data into multindex frame
    util.print_fulldf(df_budg_per_freq)
    print(f"All expense transactions in {time_flag}.")
    util.print_fulldf(df_exp, dont_print_cols=dont_print_cols)

    print(f"Totals by store grouped per {freq_desc}.")
    df_exp_stor_per_freq = df_exp.groupby(
        [pd.Grouper(freq=freq), env.EXPENSE, env.FILT_STORENAME]).sum()
    util.print_fulldf(df_exp_stor_per_freq)

    print(f"Totals by expense grouped per {freq_desc} with budgets")
    df_exp_per_freq = df_exp.groupby([pd.Grouper(freq=freq), env.EXPENSE]).sum()
    df_exp_budg_per_freq = pd.concat([df_exp_per_freq, df_budg_per_freq], axis=1)
    df_exp_budg_per_freq[env.AMOUNT] = df_exp_budg_per_freq[env.AMOUNT].fillna(0)
    df_exp_budg_per_freq[env.REMAINING] = df_exp_budg_per_freq[env.BUDGET] - \
        df_exp_budg_per_freq[env.AMOUNT]
    util.print_fulldf(df_exp_budg_per_freq)

    # do not plot in title if none are present
    if len(exp_dict[env.EXPENSES_SUBTRACTED_KEY]) == 0:
        title_templ_for_budg = "\n".join(("%s",
                                    "Income: %s | Expenses: %s | Budget: %s",
                                    "Net Income: %s | Budget Rem.: %s"))
        subtractable_expenses = None
    else:
        title_templ_for_budg = "\n".join(("%s",
                                "Income: %s | Expenses: %s | Budget: %s | Budget without %s : %s ",
                                "Net Income: %s | Budget Rem.: %s | Budget Rem. without %s : %s"))
        subtractable_expenses = exp_dict[env.EXPENSES_SUBTRACTED_KEY]

    budg_plotter(df_exp_budg_per_freq, df_exp_budg_per_freq.groupby(level=0).sum(), df_inc_per_freq, settings=settings, title_templ=title_templ_for_budg, 
                show=show_plot1, sort_by_level=0, notes=notes_dict, subtractable_expenses=subtractable_expenses, tbox_color='wheat', tbox_style='round', 
                tbox_alpha=0.5, year=years, freq_desc=freq_desc)
    title_templ_for_stor_plt = "%s\nIncome: %s | Expenses: %s | Budget: %s\nNet Income: %s | Budget Rem.: %s"
    budg_plotter(df_exp_stor_per_freq, df_exp_budg_per_freq.groupby(level=0).sum(), df_inc_per_freq, settings=settings, title_templ=title_templ_for_stor_plt, 
                show=show_plot2, sort_by_level=0, notes=notes_dict, tbox_color='wheat', tbox_style='round', tbox_alpha=0.5,  year=years,
                freq_desc=freq_desc)

def get_totals(budget_df, df_inc, date_key=None):
    if date_key == None:
        exp_tot = round(budget_df[env.AMOUNT].sum(), 2)
        budg_tot = round(budget_df[env.BUDGET].sum(), 2)
        budg_re = round(budget_df[env.REMAINING].sum(), 2)
        inc_tot = round(df_inc.loc[:, env.AMOUNT].sum(), 2)
        net_inc = round(inc_tot - exp_tot, 2)
    else:
        exp_tot = round(budget_df.loc[date_key, env.AMOUNT].sum(), 2)

        if date_key in df_inc.index:  # detect whether there was income that timeframe.
            inc_tot = round(df_inc.loc[date_key, env.AMOUNT].sum(), 2)
        else:
            inc_tot = 0

        budg_tot = round(budget_df.loc[date_key, env.BUDGET].sum(), 2)
        net_inc = round(inc_tot - exp_tot, 2)
        budg_re = round(budg_tot - exp_tot, 2)

    return exp_tot, budg_tot, budg_re, net_inc, inc_tot

def deduct_subtractables(df, subtractables, date_key, amt1, amt2):
    """Allows the subtraction of subtractables against the multi index

    Args:
        df (Dataframe): pandas df
        subtractables (List): list of items to  subtract off of the remaining budget
        date_key (Str): the date key to slice with, if none, ignore and select all dates
        amt1 (float): general dollar amount to subtract from
        amt2 (float): general dollar amount to subtract from

    Returns:
        float, float : the dollar amounts acquired from the subtractions against amt1 and amt2
    """
    for exp in subtractables:
        if date_key is not None:
            subtr_amnt = round(
                df.loc[(date_key, exp), env.REMAINING].sum(), 2)
        else:
            df_no_date = df.reset_index(level=0, drop=True)
            subtr_amnt = round(
                df_no_date.loc[exp, env.REMAINING].sum(), 2)
        amt1 -= subtr_amnt
        amt2 -= subtr_amnt
    
    return round(amt1, 2), round(amt2, 2)

def get_title(title_templ, df, subtractables, inc_tot, exp_tot, net_inc, budg_tot, budg_re, header, str_date=None):
    if subtractables is not None:  # check for any subtractable expenses when plotting to title
        budg_re_with_subtractions, budg_tot_with_subtractions = deduct_subtractables(df, 
                                                                                    subtractables,
                                                                                    str_date,
                                                                                    budg_re,
                                                                                    budg_tot
                                                                                    )

        title = title_templ % (header, inc_tot, exp_tot,
                                budg_tot, subtractables, budg_tot_with_subtractions, net_inc, 
                                budg_re, subtractables, budg_re_with_subtractions)

    else:
        title = title_templ % (header,
                                inc_tot, exp_tot, budg_tot, net_inc, budg_re)
    
    return title

def budg_plotter(df_to_plot, budget_df, df_inc, settings = None, title_templ="", show=True,
                 sort_by_level=None, notes=None, subtractable_expenses=None, tbox_color=None, tbox_style=None, tbox_alpha=None,
                 year=None, freq_desc=None):
    """
    Given a multindex dataframe, plots the data
    Args:
        df_to_plot : the multiindex df to iterate and plot. 
        budget_df : simplified budget data showing total amount and budget for the month
        df_inc : the income dataframe
        settings : a json object containing plot settings
        title_templ : the unformatted string for formatting
        show : boolean allowing the function to be chained, showing all plots at once at the end.
        sort_by_level : the level of the multiindex to sort by. Note, use n-1 since the first index is dropped for plotting
        notes : Textbox text dict {date : note} to add to figures
        subtractable_expenses : the expenses to subtract when plotting the title information. If none, do not calculate and include in the title
        tbox_color : Colour of textbox, 
        tbox_style : Style of textbox (see matplolib), 
        tbox_alpha : transparency of textbox,
        year : the numeric year
    """
    figsize=settings[env.PLOT_SIZE_KEY]
    if freq_desc == 'year':
        nrows=settings[env.NUM_ROWS_KEY]
        ncols=settings[env.NUM_COLS_KEY]
    elif freq_desc == 'month':
        nrows=settings[env.MONTH_NUM_ROWS_KEY]
        ncols=settings[env.MONTH_NUM_COLS_KEY]

    subfigs_per_fig=nrows*ncols
    parent_titl_font_size = settings[env.PA_FIG_TITL_SIZE_KEY]
    subfig_titl_font_size = settings[env.SUB_FIG_TITL_SIZE_KEY]
    layout_bounds = [0.0, 0.03, 1.0, 0.95]

    plot_idx = 1
    # allows multiindex slicing once sorted.
    df_to_plot.sort_index(level=[0, 1], ascending=[True, True], inplace=True)
    all_exp_tot, all_budg_tot, all_budg_re, all_net_inc, all_inc_tot = get_totals(budget_df, df_inc)
    
    sup_title = get_title(title_templ, df_to_plot, subtractable_expenses, all_inc_tot,
                                        all_exp_tot, all_net_inc, all_budg_tot, all_budg_re, f"{year} summary.")
    
    
    if len(df_to_plot.groupby(level=0)) == 1: # detect if only one plot should be produced, and update settings accordingly
        subfigs_per_fig = 1
        nrows = 1
        ncols = 1
        figsize = settings[env.SINGLE_PLOT_SIZE_KEY]
    
    plt.figure(figsize=figsize, facecolor='white')


    for date, sub_df in df_to_plot.groupby(level=0):
        str_date = date.strftime("%Y-%m-%d")
        date_key = f"{date.year}-{date.month}"

        if plot_idx > subfigs_per_fig:
            # get global title.
            plt.tight_layout(rect=layout_bounds)
            plt.suptitle(sup_title, size=parent_titl_font_size) # title for previous figure
            plt.figure(figsize=figsize, facecolor='white') # create new figure
            plot_idx = 1

        # drop date index for plotting
        sub_df.reset_index(level=0, inplace=True, drop=True)

        if sort_by_level != None:
            sub_df = sub_df.sort_index(level=sort_by_level)

        ax = plt.subplot(nrows, ncols, plot_idx)

        # get the title
        exp_tot, budg_tot, budg_re, net_inc, inc_tot = get_totals(budget_df, df_inc, date_key)
        title = get_title(title_templ, df_to_plot, subtractable_expenses, inc_tot,
                          exp_tot, net_inc, budg_tot, budg_re, f"{freq_desc} ending: {date.month_name()} {date.year}", 
                          str_date)

        ax.set_title(title, size=subfig_titl_font_size)
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

    plt.tight_layout(rect=layout_bounds)
    plt.suptitle(sup_title, size=parent_titl_font_size)

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

    settings = data_help.read_jsonFile(settings_path)

    bankconfig = util.get_bank_conf(settings, settings_path)

    initialize_csvs([exp_recbin_path, inc_recbin_path], 
                    [bankconfig.exp_colnames, bankconfig.inc_colnames])
    print("--- --- --- --- --- --- --- --- --- --- --- --- ---")
    print("--- --- --- -- SHOW ME YOUR MONEY -- --- --- --- --")
    print(f"--- --- --- --- --- V. {env.VERSION} --- --- --- --- --- ---")
    print("WELCOME TO SHOW ME YOUR MONEYYYYY COME ON DOWN!")
    quit = False
    index = 0
    bankconfigreloaded = bankconfig
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
                if index > 0: # reload bank config after first iteration.
                    bankconfigreloaded = util.get_bank_conf(settings, settings_path, abortchar='q')
                if bankconfigreloaded is not None: # check for None type aborts.
                    bankconfig = bankconfigreloaded
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
        
        index += 1


# data_help.gather_store_db(df, os.path.join(sys.path[0], 'exp_stor_db.json'), 'StoreName', 'ExpenseName')
