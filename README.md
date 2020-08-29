# showMeTheMoney v1.5
An CLI app used for inputting banking data and plotting graphs for budgeting purposes.

### Dependencies

1. Scotiabank is the only banking platform (as of right now) that the program parses
2. pandas, matplotlib, numpy

### Setup

1. clone the repository [showMeTheMoney](https://github.com/cboin1996/showMeTheMoney.git) into the folder you want
```bash
git clone https://github.com/cboin1996/showMeTheMoney.git
```
2. navigate to the folder and:  
  - (optional) if using virtual env  
    ```bash 
    python -m venv venv
    venv\Scripts\activate - windows
    source\venv\activate - linux/mac
    ```
  - Run setup script
    ```bash 
    python setup.py install
    ```
### Run
```bash
python showMoney.py
```

### Overview
showMeTheMoney is setup to: initialize all of its directories needed to store your banking data, create a database to remember stores, expenses, and budgeting data.

When first running the application, you will be prompted to input your expense categories.  The app uses these expense categories to
help you setup a budget for each month.  The app is designed to learn stores as you input data, so the first month of data you feed it will result in you working through the creation of your database.

#### To import data
Importing data is as easy as downloading a .csv for any given time period from your credit, debit, or both accounts.  You must 
put the csv files (as many as you need, the app detects how many and adjusts accordingly) into the folder data/new to import them. I recommend
creating a desktop shortcut to the 'data/new' folder. Once the data is within that folder,run the program and type 'i' to begin an import.

If it is your first time importing, like stated before, the program will walk you through the creation of your database as it runs into stores it has not seen before.
If it detects data in a month that does not have a budget preset, it prompt you to copy a previous budget or create a new one.
The app applies regex searched to bank strings in order to simplify the store names down as best it can (to reduce the amount of times a user must input a new store).
If regex fails, the app will prompt the user to either create a new storename for the program to remember the store by, or choose an existing store to match to in the future.

If an expense does not exist for a store, the user will be prompted to add an expense (or a couple) selected from the expense list created at runtime.

This way, the data is related and structured in a way that the editor may be used to make changes. 

The structured datasets are split into a csv for expenses and income, found in the 'data\db' folder.

One the program has launched an import, the raw data banking files are not deleted, but rather moved to the 'data\archive' folder.
If for whatever reason you need to reimport, you can copy the files you need from 'data\archive' into 'data\new', or you could recover a backup manually.

Lastly, do not worry about overlapping data.  The app will detect any duplicate data while importing and drop the duplicates keeping one of the duped transactions.

By the time you have imported a months worth of data, you will find importing data quicker, as it will run into fewer and fewer stores it does not know.

If you have several expenses declared for a store, the app will allow you to choose which expense goes with the stores transaction.

#### Viewing data
Viewing data is done through selecting the 'v' option at the main menu.  The app will load your expenses, income and budget information in order
to create plots for each month in a user selected year. 

#### Understanding your database
There are several files used by the app to track your data.  These files are automatically backed up upon importing of new data, or when you
enter the editor menu.  

The 'lib' folder contains four files: expenses.json, Budget.json, storePairs.json, and lastly storesWithExpenses.json.

Each file plays a crucial role in the parsing of raw bank data, and is considered your apps's brain.  

- expenses.json  
  - contains the list of expenses declared  
- Budget.json  
  - contains monthly budgets with money amounts paired to the expenses from expenses.json  
- storePairs.json  
  - Used as the hub to remember all the variable storenames and relate them to a single storename
  - e.g. amazon transactions show up as amaz\*on, or amaz\*on mkt\*pl etc.  These are hard to predict and filter for, so the app asks the user to match these tougher storenames to either an existing one or create a new one.  This way, if that storename shows up again, the app knows how to handle it, and what epenses go with it.  
- storesWithExpenses.json  
  - Used to pair the storenames declared by the user to expenses selected from expenses.json  

The 'db' folder contains two sub folders.. one for income and one for expenses.  Upon import, the raw data is filtered and split into income and expenses, and saved in these respective folders

#### Making changes to your data
A lot of work was put into ensuring that your data may be managed.  

The editor provides the following functionality:  

- storename editing  
  - changing of storenames  
- budget editing  
  - changing the dollar amounts in a month's budget  
- expense editing  
  - add an expense to expenses.json  
  - edit an expenses name  
  - pair expense(s) to stores  
  - delete an expense from the entire database  
  - edit an expense within the data frame  
- database editing (db/expenses/ or db/income/)  
  - Delete a row from the database  

Its important to understand that the editor should be the only way the user edits any data.  The databases are all related to each other.  
If you were to manually change an expense name you would have to find and replace the change manually across all databases.  Using the editor makes editing simple (at least to me).  

#### Managing Backups, and what if the app is running slow?
Any backups generated by the app are stored in the 'backups' folder, with a timestamp name in the form 'year_month_day__hour_min_sec'.   
Inside a backup folder are all files related to the database, structured in such a way the the user may just copy/replace the subfolders of the backup into the 'data\db' and 'lib' folder, replacing whatever is there.

The only way I could see your app running slow is if you transaction databases (.csv's) for expenses and income become very large.  All transactions are stored in two csvs, for the entire time you use the app.  Every few years I recommend moving your 'data\db' folder and saving it somewhere safe.  By removing this folder, upon import the app will start a new database for your transactions, likely reducing computation time.  If you ever want to view your old data again, just swap your new database with the old one and run the program.

Do not fret however, starting a new 'data\db' folder has no effect on your previously saved stores, expenses and budgets. Those records will still be used to filter and make your life easy with your fresh transaction database.  


