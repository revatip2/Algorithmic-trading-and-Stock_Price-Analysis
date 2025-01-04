import yfinance as yf
import mysql.connector
from datetime import datetime
import pandas as pd
from tabulate import tabulate
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from scraper import scrape_symbols




# def create_portfolio_with_stocks(cursor):
#     name = input("Enter portfolio name: ")
#     creation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     cursor.execute("INSERT INTO portfolio (name, creation_date) VALUES (%s, %s)", (name, creation_date))
#     portfolio_id = cursor.lastrowid

#     stocks = input("Enter a list of stocks separated by commas (e.g., AAPL,GOOGL,MSFT): ").split(',')

#     start_date = input("Enter start date for historical data (YYYY-MM-DD): ")
#     end_date = input("Enter end date for historical data (YYYY-MM-DD): ")

#     for symbol in stocks:
#         try:
#             stock_info = yf.Ticker(symbol)
#             # info = stock_info.info
#             historical_data = stock_info.history(start=start_date, end=end_date)
            
#             if not historical_data.empty:
#                 print(f"\nHistorical data for {symbol} between {start_date} and {end_date}:\n")
#                 table = pd.DataFrame({
#                     'Close Price': historical_data['Close']
#                 })
#                 print(table)
#                 cursor.execute("INSERT INTO stocks (portfolio_id, symbol) VALUES (%s, %s)", (portfolio_id, symbol))
#             else:
#                 print(f"\nStock {symbol} does not exist.")
#         except Exception as e:
#             print(f"Error processing stock {symbol}: {e}")

#     return portfolio_id
def create_portfolio_with_stocks(cursor):
    name = input("Enter portfolio name: ")
    creation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO portfolio (name, creation_date) VALUES (%s, %s)", (name, creation_date))
    portfolio_id = cursor.lastrowid

    stocks = input("Enter a list of stocks separated by commas (e.g., AAPL,GOOGL,MSFT): ").split(',')

    start_date = input("Enter start date for historical data (YYYY-MM-DD): ")
    end_date = input("Enter end date for historical data (YYYY-MM-DD): ")

    for symbol in stocks:
        try:
            stock_info = yf.Ticker(symbol)
            info = stock_info.info

            if 'trailingPegRatio' in info and info['trailingPegRatio'] is not None:
                historical_data = stock_info.history(start=start_date, end=end_date)

                if not historical_data.empty:
                    print(f"\nHistorical data for {symbol} between {start_date} and {end_date}:\n")
                    table = pd.DataFrame({
                        'Close Price': historical_data['Close']
                    })
                    print(table)
                    cursor.execute("INSERT INTO stocks (portfolio_id, symbol) VALUES (%s, %s)", (portfolio_id, symbol))
                    print(f"Stock {symbol} added to Portfolio ID: {portfolio_id}")
                else:
                    print(f"\nHistorical data for {symbol} does not exist.")
            else:
                print(f"Invalid symbol: {symbol}. This stock couldn't be added to Portfolio ID: {portfolio_id}")
        except HTTPError as e:
            if e.response.status_code == 404:
                print(f"Invalid symbol: {symbol}. This stock couldn't be added to Portfolio ID {portfolio_id}")
            else:
                print(f"Error processing stock {symbol}: {e}")
        except Exception as e:
            print(f"Error processing stock {symbol}: {e}")

    return portfolio_id


def add_stock_to_portfolio(cursor):
    cursor.execute("SELECT id, name FROM portfolio;")
    print(cursor.fetchall())
    portfolio_id = int(input("\nEnter the portfolio ID you want to add stocks to: "))
    stocks = input("Enter a list of stocks separated by commas (e.g., AAPL,GOOGL,MSFT): ").split(',')

    for symbol in stocks:
        try:
            stock_info = yf.Ticker(symbol)
            info = stock_info.info

            if 'trailingPegRatio' in info and info['trailingPegRatio'] is not None:
                cursor.execute("INSERT INTO stocks (portfolio_id, symbol) VALUES (%s, %s)", (portfolio_id, symbol))
                print(f"Stock {symbol} added to Portfolio ID: {portfolio_id}")
            else:
                print(f"Invalid symbol: {symbol}. This stock couldn't be added to Portfolio ID: {portfolio_id}")
        except HTTPError as e:
            if e.response.status_code == 404:
                print(f"Invalid symbol: {symbol}. This stock couldn't be added to Portfolio ID {portfolio_id}")
            else:
                print(f"Error adding {symbol} to Portfolio ID {portfolio_id}.")
        except mysql.connector.Error as e:
            if e.errno == 1062:
                print(f"Stock {symbol} already exists in Portfolio ID {portfolio_id}")
            else:
                print(f"Error adding {symbol} to Portfolio ID {portfolio_id}: {e}")
        except Exception as e:
            print(f"Error adding {symbol} to Portfolio ID {portfolio_id}.")

def remove_stock(cursor):
    cursor.execute("SELECT id, name FROM portfolio;")
    print(cursor.fetchall())
    portfolio_id = int(input("\nEnter the portfolio ID you want to remove stocks from: "))
    stocks = input("Enter a list of stocks separated by commas (e.g., AAPL,GOOGL,MSFT): ").split(',')
    for symbol in stocks:
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE portfolio_id = %s AND symbol = %s", (portfolio_id, symbol))
        count = cursor.fetchone()[0]
        if count > 0:
            cursor.execute("DELETE FROM stocks WHERE portfolio_id = %s AND symbol = %s", (portfolio_id, symbol))
            print(f"Stock {symbol} has been removed from Portfolio ID {portfolio_id}")
        else:
            print(f"Stock {symbol} doesn't exist in Portfolio ID {portfolio_id}.")

def delete_portfolio(cursor):
    cursor.execute("SELECT id, name FROM portfolio;")
    portfolios = cursor.fetchall()

    if not portfolios:
        print("No portfolios exist to delete.")
        return

    print("Available Portfolios:")
    for portfolio in portfolios:
        print(f"ID: {portfolio[0]}, Name: {portfolio[1]}")

    portfolio_id_to_delete = int(input("\nDeleting a portfolio will delete all stocks listed in it. Enter the ID of the portfolio you want to delete: "))

    cursor.execute("DELETE FROM stocks WHERE portfolio_id = %s", (portfolio_id_to_delete,))
    cursor.execute("DELETE FROM portfolio WHERE id = %s", (portfolio_id_to_delete,))

    print(f"\nPortfolio ID {portfolio_id_to_delete} has been deleted.")


def display_portfolios(cursor):
    query = """
    SELECT
        
        portfolio.name AS portfolio_name,
        portfolio.creation_date,
        GROUP_CONCAT(stocks.symbol) AS stock_list
    FROM
        portfolio
    LEFT JOIN
        stocks ON portfolio.id = stocks.portfolio_id
    GROUP BY
        portfolio.id, portfolio.name, portfolio.creation_date
    ORDER BY
        portfolio.creation_date DESC;
    """

    cursor.execute(query)
    result = cursor.fetchall()
    df = pd.DataFrame(result)
    print("\nPortfolios and their Stocks:")
    print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))


def main_menu(cursor):
    print("\nPortfolio Management System")
    # print("1. View watchlists")
    print("1. Create a new portfolio with stocks")
    if at_least_one_portfolio_exists(cursor):
        print("2. Add stocks to an existing portfolio")
        print("3. Remove stocks from an existing portfolio")
        print("4. Remove portfolio")
        print("5. Display portfolios and stocks")
    print("6. Exit")
    print("7. View watchlist")
    choice = input("Enter your choice: ")
    return choice

def at_least_one_portfolio_exists(cursor):
    cursor.execute("SELECT COUNT(*) FROM portfolio;")
    count = cursor.fetchone()[0]
    return count > 0

if __name__ == "__main__":
    db_connection = mysql.connector.connect(
        host="localhost",
        user="sam",
        password="pass246",
        database="stocks_portfolio"
    )
    cursor = db_connection.cursor()
    while True:
        choice = main_menu(cursor)

        # if choice == '1':
        #     sym = display_watchlist()
        #     print('Symbols: ',sym )

        if choice == '1':
            create_portfolio_with_stocks(cursor)
            db_connection.commit()
            print("\nPortfolio created.\n")

        elif choice == '2':
            add_stock_to_portfolio(cursor)
            db_connection.commit()

        elif choice == '3':
            remove_stock(cursor)
            db_connection.commit()

        elif choice == '4':
            delete_portfolio(cursor)
            db_connection.commit()

        elif choice == '5':
            display_portfolios(cursor)
            db_connection.commit()

        elif choice == '6':
            print("\nExiting Portfolio Management System.")
            break

        elif choice == '7':
            print('a. Banking and Finance\n')
            print('b. Video Games\n')
            print('c. e-commerce\n')
            print('d. Biotech and Drugs\n')
            print('e. Oil and Gas\n')
            selected = input('Please select the watchlist to view stocks symbols:\n')

            if selected.lower() == 'a':
                scrape_symbols("https://finance.yahoo.com/u/yahoo-finance/watchlists/bank-and-financial-services-stocks/")
            elif selected.lower() == 'b':
                scrape_symbols("https://finance.yahoo.com/u/yahoo-finance/watchlists/video-game-stocks ")
            elif selected.lower() == 'c':
                scrape_symbols("https://finance.yahoo.com/u/yahoo-finance/watchlists/e-commerce-stocks/")
            elif selected.lower() == 'd':
                scrape_symbols("https://finance.yahoo.com/u/yahoo-finance/watchlists/biotech-and-drug-stocks")
            elif selected.lower() == 'e':
                scrape_symbols("https://finance.yahoo.com/u/yahoo-finance/watchlists/oil-and-gas-stocks ")
            else:
                print("Invalid selection. Please choose a valid option.")

        else:
            print("\nInvalid choice. Please re-enter.")

    cursor.close()
    db_connection.close()
