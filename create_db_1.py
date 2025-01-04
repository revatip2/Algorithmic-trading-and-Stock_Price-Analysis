import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='sam',
    password='pass246'
)
cursor = conn.cursor()

cursor.execute('''
    CREATE DATABASE IF NOT EXISTS stocks_portfolio;
''')
               
conn = mysql.connector.connect(
    host='localhost',
    user='sam',
    password='pass246',
    database='stocks_portfolio'
)

cursor = conn.cursor()

cursor.execute('''
    use stocks_portfolio;
'''
)
               
cursor.execute('''
    CREATE TABLE IF NOT EXISTS portfolio (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        creation_date DATETIME NOT NULL
        )
    
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS stocks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        portfolio_id INT,
        symbol VARCHAR(255) NOT NULL,
        FOREIGN KEY (portfolio_id) REFERENCES portfolio(id),
        UNIQUE KEY unique_portfolio_symbol (portfolio_id, symbol)
    )
''')

conn.commit()
conn.close()
