# showMeTheMoney
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
showMeTheMoney is setup to initialize all of its directories needed to store your banking data, create a database to remember stores, expenses, and budgeting data.

When first running the application, you will be prompted to input your expenses categories.  The app uses these expense categories to
help you setup a budget for each month you have data imported, and relate stores to expenses.  The app is designed to learn stores
as you input data, so the first month of data you feed it will result in you working through the creation of your database.

#### To import data
Importing data is as easy as downloading a .csv for any given period for your credit, debit, or both accounts at your bank.  You must 
put the csv files (as many as you need, the app detects how many and adjusts accordingly) into the folder data/new. I recommend
creating a desktop shortcut to the 'data/new' folder. Once the data is within that folder, within the programs main  menu input 'i' to begin an import.

If its your first time importing, like stated before, the program will walk you through the creation of a database as it runs into stores it has not seen before.
If it detects data in a month that does not have a budget preset, it prompt you to copy a previous budget or create a new one.
The app applies regex searched to bank strings in order to simplify the store names down as best it can (to reduce the amount of times a user must input a new store).
If regex fails, the app will prompt the user to either create a new storename for the bank's, or choose an existing store to match to in the future.

In the same way, if an expense does not exist for a store, the user will be prompted to add an expense (or a couple) selected from the expense list created at runtime.

This way, the data is related and structured, so that the editor may be used to make changes. 

The structured datasets are split into a csv for expenses and income, found in the 'data\db' folder.

One the program has launched an import, the raw data banking files are not deleted, but rather moved to the 'data\archive' folder.
If for whatever reason you need to reimport, the data will be there, or you could recover a backup manually.

Lastly, do not worry about overlapping data.  The app will detect any duplicate data while importing and drop the duplicates keeping on of the duped transactions.

By the time you have imported a months worth of data, you will find the app very quick to use as it will run into fewer and fewer new stores.

If you have several expenses declared for a store, the app will allow you to choose with expense goes with the stores transaction.

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
  - Used as the hub for remember all the variable storenames and relating them to a single storename
  - e.g. amazon transactions show up as amaz\*on, or amaz\*on mkt*pl etc.  These are hard to predict and filter for, so the app asks the user to match these tougher storenames to either an existing one or create a new one.  This way, if that storename shows up again, the app knows how to handle it, and what epenses go with it.  
- storesWithExpenses.json  
  - Used to pair the storenames declared by the user to expenses selected from expenses.json  

The 'db' folder contains two sub folders.. one for income and one for expenses.  Upon import, the raw data is filtered and split into income and expenses, and saved in these respective folders

#### Making changes to your data
A lot of work was put into ensuring that your data may be managed.  From experience, I found it a pain to manually remove entries and try to ensure I entered the exact same name from expenses.json into a particular cell of the data.  

The editor provides the following functionality:  

- storename editing  
  - changing of storenames  
- budget editing  
  - changing the dollar amounts in a month's budget  
- expense editing  
  - add an expense to expenses.json  
  - edit an expenses name  
  - pair expense(s) to stores  
  - delete an expense from the database  
  - edit an expense within the data frame  
- database editing (db/expenses/ or db/income/)  
  - Delete a row from the database  

Its important to understand that the editor should be the only way the user edits any data.  The databases are all related to each other somehow, and so if you were to manually change an expense name you would have to find and replace the change manually across all databases for example.  Using the editor makes editing simple (at least to me).  

#### Managing Backups, and what if the app is running slow?
Any backups generated by the app are stored in the 'backups' folder, with timestamp name represented by the year_month_day__hour_min_sec.   
Inside a backup folder are all files related to the database, structured in such a way the the user may just copy/replace the backup into the 'data' and 'lib' folder.  

The only way I could see your app running slow is partially my fault, since I was lazy and did not want to create separate transaction databases for income and expense based on time amounts.  All transactions are stored in two csvs, for the entire time you use the app.  What I recommend, is that after a few years taking the 'data\db' folder and saving it somewhere safe.  By removing this folder, upon import the app will start a new database for your transactions, likely reducing computation time.  

Do not fret however, starting a new 'data\db' folder has no effect on your previously saved stores, expenses and budgets. Those records will still be used to filter and make your life easy with your  new transaction database.  


