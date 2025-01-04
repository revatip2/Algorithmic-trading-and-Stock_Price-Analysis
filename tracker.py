import mysql.connector
import datetime
import pandas as pd
import yfinance as yf
from requests.exceptions import HTTPError
from tabulate import tabulate
import numpy as np
import random
from tensorflow.keras.models import load_model
from lstm import preprocess_stock_data

def lstm_forecast(stock_symbol, start_date, end_date):
    print('SS: ',stock_symbol)
    X_train, sc_predict, _, _ = preprocess_stock_data(stock_symbol, '2013-01-01', '2024-01-01', n_past=90, n_future=60)
    name_str = f'models/{stock_symbol}.h5'
    model = load_model(name_str)
    n_future = 60
    n_past = 90
    # start_date = '2024-01-01'  
    datelist_future = pd.date_range( start=start_date, periods=n_future, freq='1d').tolist()
    datelist_future_ = [this_timestamp.date() for this_timestamp in datelist_future]
    predictions_future = model.predict(X_train[-n_future:])
    predictions_train = model.predict(X_train[n_past:])
    predictions_future = model.predict(X_train[-n_future:])
    predictions_train = model.predict(X_train[n_past:])
    # def datetime_to_timestamp(x):
    #     return datetime.strptime(x.strftime('%Y%m%d'), '%Y%m%d')

    y_pred_future = sc_predict.inverse_transform(predictions_future)
    # y_pred_train = sc_predict.inverse_transform(predictions_train)
    pred_fut = pd.DataFrame(y_pred_future, columns=['Open']).set_index(pd.Series(datelist_future))
    return pred_fut.loc[start_date:end_date, 'Open']


def create_portfolio_with_stocks(cursor):
    name = input("Enter portfolio name: ")
    creation_date = datetime.datetime.min.strftime('%Y-%m-%d %H:%M:%S')
    initial_funds = input("Enter initial funds: ")

    cursor.execute("INSERT INTO portfolio (name, creation_date, date, funds) VALUES (%s, %s, %s, %s)", (name, creation_date, creation_date, initial_funds))
    # db_connection.commit()
    
    portfolio_id = cursor.lastrowid
    stocks = input("Enter a list of stocks separated by commas (e.g., AAPL,GOOGL,MSFT): ").split(',')

    # start_date = input("Enter start date for historical data (YYYY-MM-DD): ")
    # end_date = input("Enter end date for historical data (YYYY-MM-DD): ")

    for symbol in stocks:
        try:
            stock_info = yf.Ticker(symbol)
            info = stock_info.info
            cursor.execute("INSERT INTO stocks (date, symbol, shares_held, shares_traded, at_price, portfolio_id) VALUES (%s, %s, 0, 0, 0, %s);", (creation_date, symbol, portfolio_id))
            # db_connection.commit()
            print(f"Stock {symbol} added to Portfolio ID: {portfolio_id}")
        
        except HTTPError as e:
            if e.response.status_code == 404:
                print(f"Invalid symbol: {symbol}. This stock couldn't be added to Portfolio ID {portfolio_id}")
            else:
                print(f"Error processing stock {symbol}: {e}")
        except Exception as e:
            print(f"Error processing stock {symbol}: {e}")

    return portfolio_id


def delete_portfolio(cursor):
    cursor.execute("SELECT DISTINCT id, name FROM portfolio;")
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
    # query = """
    # SELECT 
    #     portfolio.name AS portfolio_name,
    #     portfolio.creation_date,
    #     GROUP_CONCAT(stocks.symbol) AS stock_list,
    #     portfolio.funds AS remaining_funds
    # FROM
    #     portfolio
    # LEFT JOIN
    #     stocks ON portfolio.id = stocks.portfolio_id
    # GROUP BY
    #     portfolio.id, portfolio.name, portfolio.creation_date
    # ORDER BY
    #     portfolio.creation_date DESC;
    # """

    cursor.execute("SELECT * FROM portfolio")
    result = cursor.fetchall()
    df = pd.DataFrame(result)
    print("\nPortfolios:")
    print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))


def min_max_decision(forecast, current_price, shares_held):
    """
    parameters:
        forecast: list of stock values for the next 14 days
        current_price: current stock value
        shares_held: number of shares currently held of this stock
    returns:
       -1: hold
        0: buy or hold, decide in trade() based on remaining funds
        1: sell
    """
    
    # if current_price <= min(forecast):
    #     return 0
    if float(current_price) < max(forecast):
        return 0 
    if float(shares_held) > 0 and float(current_price) >= max(forecast):
        return 1
    if float(shares_held) > 0 and float(current_price) in range(min(forecast), max(forecast)):
        return -1
    else:
        return -1 
    

def moving_avg_forecast(symbol, start_date, end_date):

    stock_info = yf.Ticker(symbol)
    
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    data = stock_info.history(start='2013-01-01', end=today)
    
    market_perf_metrics = pd.DataFrame()
    df = pd.DataFrame(data)
    df['SMA_50'] = df['Close'].rolling(window=50, min_periods=1).mean()
    # df['SMA_200'] = df['Close'].rolling(window=200, min_periods=1).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    # df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df = df.dropna()
    
    # start_date = '2024-01-15'
    # end_date = '2024-01-28'
    
    df = df.loc[start_date:end_date]
    final = (df['SMA_50'] + df['EMA_50']) / 2
    final = final.tolist()
    return final


def get_historical_data(symbol):
    """
    - returns historical data from trading period start date to trading period end date
    """

    stock_info = yf.Ticker(symbol)
    info = stock_info.info

    if 'trailingPegRatio' in info and info['trailingPegRatio'] is not None:
        historical_data = stock_info.history(start=start_date-datetime.timedelta(days=1), end=end_date+datetime.timedelta(days=1))
        if not historical_data.empty:
            return historical_data 
    
    return 0


def trade(portfolio_id, date, start_date, end_date, cursor):

    print("\n\nTrading on: ", date)
    
    cursor.execute("SELECT DISTINCT symbol FROM stocks where portfolio_id=%s",(int(portfolio_id),))
    stocks = cursor.fetchall()

    cursor.execute("SELECT funds FROM portfolio WHERE id=%s ORDER BY DATE DESC LIMIT 1", (int(portfolio_id),))
    remaining_funds = cursor.fetchall()[0][0]
    print("Funds at the beggining of day: ", remaining_funds)
    
    history = get_historical_data(stocks[0][0]) 
    if date not in history.index:
        print("Not a trade day!")
        return
    
    for symbol in stocks:	
            
        forecast_lstm = lstm_forecast(symbol[0], date, end_date)
        forecast_lstm = forecast_lstm.tolist()
        forecast_avg = moving_avg_forecast(symbol[0], date, end_date)
        forecast = [(x + y) / 2 for x, y in zip(forecast_lstm, forecast_avg)]
        print("Forecast: ", forecast)
        
        # stock_data = yf.Ticker(symbol[0])
        # current_price = float(stock_data.info['ask'])
        history = get_historical_data(symbol[0])
        if not isinstance(history, pd.DataFrame):
        	continue
        current_price = history.loc[date]['Open']

        print("Current price: ",current_price)
        
        cursor.execute("SELECT shares_held FROM stocks WHERE symbol=%s ORDER BY date DESC LIMIT 1",symbol)
        shares_held = float(cursor.fetchall()[0][0])
        
        action = min_max_decision(forecast, current_price, shares_held)

        # sell
        if action == 1:
            print("Selling:", symbol[0])
            shares_traded = -fixed_qty 
            shares_held += shares_traded
            cursor.execute("INSERT INTO stocks (date, symbol, shares_held, shares_traded, at_price, portfolio_id) VALUES (%s, %s, %s, %s, %s, %s)", (date, symbol[0], shares_held, shares_traded, current_price, portfolio_id))
            # db_connection.commit()
            remaining_funds += (-shares_traded) * current_price
            
        # buy or hold
        elif action == 0: 
            cost = fixed_qty * current_price
            
            # hold
            if shares_held == fixed_qty: 
                print("Holding:", symbol[0])
                cursor.execute("INSERT INTO stocks (date, symbol, shares_held, shares_traded, at_price, portfolio_id) VALUES (%s, %s, %s, %s, %s, %s)", (date, symbol[0], shares_held, 0, 0, portfolio_id))
                # db_connection.commit()
        
            # buy
            elif shares_held < fixed_qty and remaining_funds >= cost: 
                print("Buying:", symbol[0])
                shares_traded = fixed_qty
                shares_held += shares_traded
                cursor.execute("INSERT INTO stocks (date, symbol, shares_held, shares_traded, at_price, portfolio_id) VALUES (%s, %s, %s, %s, %s, %s)", (date, symbol[0], shares_held, shares_traded, current_price, portfolio_id))
                # db_connection.commit()
                remaining_funds -= shares_traded * current_price
            
            # insufficient funds
            else: 
                print("Insuffiecient funds to buy:", symbol[0])
                cursor.execute("INSERT INTO stocks (date, symbol, shares_held, shares_traded, at_price, portfolio_id) VALUES (%s, %s, %s, %s, %s, %s)", (date, symbol[0], shares_held, shares_traded, current_price, portfolio_id))
                # db_connection.commit()

        # hold
        elif action==-1: 
            print("No action:", symbol[0])
            cursor.execute("INSERT INTO stocks (date, symbol, shares_held, shares_traded, at_price, portfolio_id) VALUES (%s, %s, %s, %s, %s, %s)", (date, symbol[0], shares_held, 0, 0, portfolio_id))
            # db_connection.commit()

                
    cursor.execute("SELECT name, creation_date FROM portfolio WHERE id=%s LIMIT 1", (int(portfolio_id),))
    name, creation_date = cursor.fetchall()[0]
    cursor.execute("INSERT INTO portfolio (id, name, creation_date, date, funds) VALUES (%s, %s, %s, %s, %s)", (portfolio_id, name, creation_date, date, remaining_funds))
    # db_connection.commit()
    print("Funds at the end of day: ", remaining_funds)
    
    return


def portfolio_value(portfolio_id, date, cursor):

    cursor.execute("SELECT DISTINCT symbol FROM stocks WHERE portfolio_id=%s",(int(portfolio_id),))
    stocks = cursor.fetchall()

    portfolio_value = 0
    
    for symbol in stocks:
    
    	if symbol[0] != 'SPY':
    		cursor.execute("SELECT date FROM stocks WHERE symbol =%s ORDER BY date DESC LIMIT 1", symbol)
    		date_his = cursor.fetchall()[0][0]
    		stock_data = yf.Ticker(symbol[0])
    		history = get_historical_data(symbol[0])
    		current_price = history.loc[date_his]['Open']
    		#current_price = float(stock_data.info['ask'])
    		cursor.execute("SELECT shares_held FROM stocks WHERE symbol=%s ORDER BY date DESC LIMIT 1", symbol)
    		shares_held = cursor.fetchall()[0][0]
    		stock_value = float(shares_held) * float(current_price)
    		portfolio_value += stock_value

    return portfolio_value


def simple_individual_return(portfolio_id, date, cursor):

    cursor.execute("SELECT DISTINCT symbol FROM stocks where portfolio_id=%s",(int(portfolio_id),))
    stocks = cursor.fetchall()
    
    returns = {}
    total_returns = 0
    
    
    
    for symbol in stocks:
        
        cursor.execute("SELECT shares_traded, at_price FROM stocks WHERE symbol=%s AND shares_traded IS NOT NULL AND at_price IS NOT NULL;", symbol)
        all_trades = cursor.fetchall()
        individual_returns = []
        bought, invested, returned = 0, 0, 0

        # for returns on previous transactions
        for row in all_trades:
            shares_traded, at_price = row
            
            # shares bought
            if shares_traded > 0:
                invested += (abs(float(shares_traded)) * float(at_price))
                bought = 1

            # shares sold
            elif shares_traded < 0: 
                returned += (abs(float(shares_traded)) * float(at_price))
                if bought == 1:
                    trade_return = (returned - invested)#*100/(invested)
                    individual_returns.append(trade_return)
                    total_returns += trade_return
                    bought, invested, returned = 0, 0, 0 # reset to track new trade

        # for return on shares still held (multiply by current stock price)
        cursor.execute("SELECT shares_held FROM stocks WHERE symbol=%s ORDER BY date DESC LIMIT 1 ", symbol)
        shares_held = float(cursor.fetchall()[0][0])
        cursor.execute("SELECT date FROM stocks WHERE symbol =%s ORDER BY date DESC LIMIT 1", symbol)
        date_his = cursor.fetchall()[0][0]
        if shares_held > 0 and symbol[0] != 'SPY':
            stock_data = yf.Ticker(symbol[0])
            # current_price = float(stock_data.info['ask'])
            history = get_historical_data(symbol[0]) 
           
            current_price = history.loc[date_his]['Open']

            current_return = ((current_price * shares_held) - invested) #* 100 / invested
            individual_returns.append(current_return)

        returns[symbol[0]] = individual_returns

    return returns, total_returns


def calculate_sharpe_ratio(returns, risk_free_rate):
    """
    parameters:
    - returns: list of investment returns
    - risk_free_rate: annual risk-free rate, assumed 0.2 

    returns:
    - sharpe ratio
    """
    average_return = np.mean(returns)
    risk = np.std(returns)
    sharpe_ratio = (average_return - risk_free_rate) / risk
    return sharpe_ratio


def metrics(cursor):

    cursor.execute("SELECT DISTINCT id, name FROM portfolio;")
    portfolios = cursor.fetchall()

    if not portfolios:
        print("No portfolios exist.")
        return

    print("Available Portfolios:")
    for portfolio in portfolios:
        print(f"ID: {portfolio[0]}, Name: {portfolio[1]}")

    p_id = int(input("Enter your choice of portfolio ID: "))

    cursor.execute("SELECT date FROM portfolio WHERE id=%s ORDER BY date DESC LIMIT 1", (int(p_id),))
    date = cursor.fetchall()[0][0]

    pv = portfolio_value(p_id, date, cursor)
    print("PORTFLIO VALUE: ", pv)
    
    returns, total_returns = simple_individual_return(p_id, date, cursor)
    print("INDIVIDUAL RETURNS: ", returns)
    print("TOTAL RETURNS: ", total_returns)
    # {'GOGOL': [5,2,..], 'APPL': [4,1,..], ...}

    flat_returns = np.array([i for r in returns.values() for i in r])
    
    risk_free_rate = 0.2
    sharpe = calculate_sharpe_ratio(flat_returns, risk_free_rate)
    print("SHARPE RATIO: ", sharpe)

    return (pv,returns,sharpe)


def main_menu(cursor):
    print("\nPortfolio Management System")
    print("1. Create a new portfolio with stocks")
    print("2. Display portfolios and stocks")
    print("3. Remove portfolio")
    print("4. Trade")
    print("5. View metrics")
    print("6. Train Models")
    print("7. Exit")
    choice = input("Enter your choice: ")
    return choice


if __name__ == "__main__":

    sql_user = input("enter mysql username: ")
    sql_pass = input("enter mysql password: ")
    

    db_connection = mysql.connector.connect(
        host="localhost",
        user=sql_user,
        password=sql_pass,
        database="stocks_portfolio_2"
    )
    cursor = db_connection.cursor()

    while True:
        choice = main_menu(cursor)

        if choice == '1':
            create_portfolio_with_stocks(cursor)
            db_connection.commit()
            print("\nPortfolio created.\n")

        elif choice == '2':
            display_portfolios(cursor)

        elif choice == '3':
            delete_portfolio(cursor)
            db_connection.commit()
            print("\nPortfolio created.\n")

        elif choice == '4':
            cursor.execute("SELECT DISTINCT id, name FROM portfolio;")
            portfolios = cursor.fetchall()

            if not portfolios:
                print("No portfolios exist.")
                continue

            print("Available Portfolios:")
            for portfolio in portfolios:
                print(f"ID: {portfolio[0]}, Name: {portfolio[1]}")

            p_id = int(input("Enter your choice of portfolio ID: "))
            start_date_str = input("Enter the start date (YYYY-MM-DD): ")
            end_date_str = input("Enter the end date (YYYY-MM-DD): ")
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")

            fixed_qty = 1
            current_date = start_date
            while current_date <= end_date:
                trade(p_id, current_date, start_date, end_date, cursor)
                current_date += datetime.timedelta(days=1)
            db_connection.commit()
                
        elif choice == '5':
        	start = '2024-01-14'
        	start_date = datetime.datetime.strptime(start, "%Y-%m-%d")
        	end = '2024-01-31'
        	end_date = datetime.datetime.strptime(end, "%Y-%m-%d")
        	metrics(cursor)
        	
        elif choice == '6':
        	exec(open('model_training.py').read())

        elif choice == '7':
            print("Bye!")
            break

