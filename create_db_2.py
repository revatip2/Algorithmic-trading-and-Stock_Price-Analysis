# SAMPLE DATA

# INSERT INTO portfolio (name, creation_date, date, funds) 
# VALUES
#     ('googl_only', '2024-01-14 00:00:00', '2024-01-14 00:00:00', 1000);

# INSERT INTO stocks (date, symbol, shares_held, shares_traded, at_price, portfolio_id) 
# VALUES 
#     ('2024-01-14 00:00:00', 'GOOGL', 0, 0, 0, 1);


import mysql.connector

sql_user = input("enter mysql username: ")
sql_pass = input("enter mysql password: ")

conn = mysql.connector.connect(
    host='localhost',
    user=sql_user,
    password=sql_pass
)
cursor = conn.cursor()

cursor.execute('''
    CREATE DATABASE IF NOT EXISTS stocks_portfolio_2;
''')
               
conn = mysql.connector.connect(
    host='localhost',
    user=sql_user,
    password=sql_pass,
    database='stocks_portfolio_2'
)

cursor = conn.cursor()

cursor.execute('''
    use stocks_portfolio_2;
'''
)

# ADDED INITIAL FUNDS               
cursor.execute('''
    CREATE TABLE IF NOT EXISTS portfolio (
        id INT AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        creation_date DATETIME NOT NULL,
        date DATETIME NOT NULL,
        funds FLOAT,
        PRIMARY KEY (id, name, date)
    )
''')

# ONE ROW PER DAY
# shares_held is total shares still held after performing the trade/action (if any) on a particular date
# shares_traded is +N if bought, and -N is sold, 0 if held (no action)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS stocks (
        id INT AUTO_INCREMENT PRIMARY KEY,       
        date DATETIME NOT NULL,
        symbol VARCHAR(255) NOT NULL,
        shares_held FLOAT,
        shares_traded FLOAT,
        at_price FLOAT,
        portfolio_id INT,
        FOREIGN KEY (portfolio_id) REFERENCES portfolio(id),
        UNIQUE KEY unique_portfolio_symbol (portfolio_id, symbol, date)
    )
''')

conn.commit()
conn.close()

