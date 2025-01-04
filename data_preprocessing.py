import yfinance as yf
import mysql.connector
from datetime import datetime
import pandas as pd
from tabulate import tabulate
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
import numpy as np 
from scraper import scrape_symbols

def calculate_financial_metrics(stock_info):
    financial_metrics = pd.DataFrame()

    try:
        financial_metrics['Earnings_Yield'] = [stock_info['trailingEps'] / stock_info['currentPrice']]
    except KeyError:
        financial_metrics['Earnings_Yield'] = [float('nan')]

    try:
        financial_metrics['Dividend_Payout_Ratio'] = [stock_info['dividendRate'] / stock_info['trailingEps']]
    except KeyError:
        financial_metrics['Dividend_Payout_Ratio'] = [float('nan')]

    try:
        financial_metrics['PEG_Ratio'] = [stock_info['trailingPE'] / stock_info['earningsQuarterlyGrowth']]
    except KeyError:
        financial_metrics['PEG_Ratio'] = [float('nan')]

    return financial_metrics



def calculate_time_metrics(stock_info):
    time_metrics = pd.DataFrame()

    try:
        time_metrics['Year'] = [pd.to_datetime(stock_info['lastFiscalYearEnd'], unit='s').year]
    except KeyError:
        time_metrics['Year'] = [float('nan')]

    try:
        time_metrics['Month'] = [pd.to_datetime(stock_info['lastFiscalYearEnd'], unit='s').month]
    except KeyError:
        time_metrics['Month'] = [float('nan')]

    try:
        time_metrics['Day'] = [pd.to_datetime(stock_info['lastFiscalYearEnd'], unit='s').day]
    except KeyError:
        time_metrics['Day'] = [float('nan')]

    try:
        time_metrics['Quarter'] = [pd.to_datetime(stock_info['mostRecentQuarter'], unit='s').quarter]
    except KeyError:
        time_metrics['Quarter'] = [float('nan')]

    return time_metrics



def calculate_volume_metrics(stock_info):
    volume_metrics = pd.DataFrame()

    try:
        volume_metrics['Bid_Ask_Size_Ratio'] = [stock_info['bidSize'] / stock_info['askSize']]
    except KeyError:
        volume_metrics['Bid_Ask_Size_Ratio'] = [float('nan')]

    return volume_metrics


def calculate_price_metrics(stock_info):
    price_metrics = pd.DataFrame()

    try:
        price_metrics['Percentage_Change_from_Previous_Close'] = [(stock_info['currentPrice'] - stock_info['previousClose']) / stock_info['previousClose']]
    except KeyError:
        price_metrics['Percentage_Change_from_Previous_Close'] = [float('nan')]

    return price_metrics


def calculate_market_cap_metrics(stock_info):
    market_cap_metrics = pd.DataFrame()

    try:
        market_cap_metrics['Market_Cap_per_Employee'] = [stock_info['marketCap'] / stock_info['fullTimeEmployees']]
    except KeyError:
        market_cap_metrics['Market_Cap_per_Employee'] = [float('nan')]

    try:
        market_cap_metrics['Enterprise_Value_to_Revenue_Ratio'] = [stock_info['enterpriseValue'] / stock_info['totalRevenue']]
    except KeyError:
        market_cap_metrics['Enterprise_Value_to_Revenue_Ratio'] = [float('nan')]

    return market_cap_metrics



def calculate_analyst_recommendation_metrics(stock_info):
    analyst_metrics = pd.DataFrame()

    recommendation_mapping = {'buy': 1, 'hold': 2, 'sell': 3}

    try:
        recommendation = recommendation_mapping.get(stock_info['recommendationKey'], 0)
    except KeyError:
        recommendation = 0

    analyst_metrics['Recommendation'] = [recommendation]

    return analyst_metrics



def calculate_executive_compensation_metrics(stock_info):
    exec_comp_metrics = pd.DataFrame()

    try:
        total_compensation_ratio = stock_info['companyOfficers'][0]['totalPay'] / stock_info['marketCap']
    except (KeyError, IndexError):
        total_compensation_ratio = None

    exec_comp_metrics['Total_Compensation_Ratio'] = [total_compensation_ratio]

    return exec_comp_metrics



def calculate_dividend_metrics(stock_info):
    dividend_metrics = pd.DataFrame()

    try:
        dividend_yield = stock_info['dividendYield']
        five_year_avg_yield = stock_info['fiveYearAvgDividendYield']

        if pd.notna(dividend_yield) and pd.notna(five_year_avg_yield) and five_year_avg_yield != 0:
            dividend_metrics['Dividend_Yield_to_5Year_Avg'] = [dividend_yield / five_year_avg_yield]
        else:
            dividend_metrics['Dividend_Yield_to_5Year_Avg'] = [None]

    except KeyError:
        dividend_metrics['Dividend_Yield_to_5Year_Avg'] = [None]

    return dividend_metrics



def calculate_liquidity_metrics(stock_info):
    liquidity_metrics = pd.DataFrame()

    try:
        average_volume = stock_info.get('averageVolume', None)
        shares_outstanding = stock_info.get('sharesOutstanding', None)

        if pd.notna(average_volume) and pd.notna(shares_outstanding) and shares_outstanding != 0:
            liquidity_metrics['Liquidity_Ratio'] = [average_volume / shares_outstanding]
        else:
            liquidity_metrics['Liquidity_Ratio'] = [None]

    except Exception as e:
        print(f"Error: {e}")
        liquidity_metrics['Liquidity_Ratio'] = [None]

    return liquidity_metrics    

def calculate_earnings_metrics(stock_info):
    earnings_metrics = pd.DataFrame()

    try:
        trailing_eps = stock_info.get('trailingEps', None)
        current_price = stock_info.get('currentPrice', None)
        revenue_per_share = stock_info.get('revenuePerShare', None)

        if pd.notna(trailing_eps) and pd.notna(current_price) and pd.notna(revenue_per_share) and current_price != 0:
            earnings_metrics['Earnings_Yield'] = [trailing_eps / current_price]
            earnings_metrics['Earnings_to_Price_Ratio'] = [trailing_eps / current_price]
            earnings_metrics['Price_to_Sales_Ratio'] = [current_price / revenue_per_share]
        else:
            earnings_metrics['Earnings_Yield'] = [None]
            earnings_metrics['Earnings_to_Price_Ratio'] = [None]
            earnings_metrics['Price_to_Sales_Ratio'] = [None]

    except Exception as e:
        print(f"Error: {e}")
        earnings_metrics['Earnings_Yield'] = [None]
        earnings_metrics['Earnings_to_Price_Ratio'] = [None]
        earnings_metrics['Price_to_Sales_Ratio'] = [None]

    return earnings_metrics

def calculate_market_performance_metrics(stock_info):
    market_perf_metrics = pd.DataFrame()

    if 'history' in stock_info:
        df = pd.DataFrame(stock_info['history'])

        df['RSI'] = calculate_rsi(df)

        df['SMA_50'] = df['Close'].rolling(window=50, min_periods=1).mean()
        df['SMA_200'] = df['Close'].rolling(window=200, min_periods=1).mean()

        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

        df = df.dropna()

        market_perf_metrics['RSI'] = df['RSI']
        market_perf_metrics['SMA_50'] = df['SMA_50']
        market_perf_metrics['SMA_200'] = df['SMA_200']
        market_perf_metrics['EMA_50'] = df['EMA_50']
        market_perf_metrics['EMA_200'] = df['EMA_200']

    return market_perf_metrics

def calculate_rsi(data, column='Close', window=14):
    if column in data:
        delta = data[column].diff(1)
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        avg_gains = gains.rolling(window=window, min_periods=1).mean()
        avg_losses = losses.rolling(window=window, min_periods=1).mean()
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
    else:
        rsi = np.nan

    return rsi


db_connection = mysql.connector.connect(
    host="localhost",
    user="sam",
    password="pass246",
    database="stocks_portfolio"
)

cursor = db_connection.cursor()

cursor.execute("SELECT symbol FROM stocks")
stocks = [row[0] for row in cursor.fetchall()]
print('Stocks: ',stocks)
cursor.close()
db_connection.close()

all_data = []

for symbol in stocks:
    stock_info = yf.Ticker(symbol).info

    volume_metrics = calculate_volume_metrics(stock_info)
    price_metrics = calculate_price_metrics(stock_info)
    market_cap_metrics = calculate_market_cap_metrics(stock_info)
    analyst_metrics = calculate_analyst_recommendation_metrics(stock_info)
    exec_comp_metrics = calculate_executive_compensation_metrics(stock_info)
    dividend_metrics = calculate_dividend_metrics(stock_info)
    market_perf_metrics = calculate_market_performance_metrics(stock_info)
    liquidity_metrics = calculate_liquidity_metrics(stock_info)
    earnings_metrics = calculate_earnings_metrics(stock_info)
    time_metrics = calculate_time_metrics(stock_info)
    financial_metrics = calculate_financial_metrics(stock_info)

    stock_data = pd.concat([
        volume_metrics,
        price_metrics,
        market_cap_metrics,
        analyst_metrics,
        exec_comp_metrics,
        dividend_metrics,
        market_perf_metrics,
        liquidity_metrics,
        time_metrics,
        earnings_metrics,
        financial_metrics
    ], axis=1)

    stock_data['Symbol'] = symbol

    all_data.append(stock_data)

final_dataset = pd.concat(all_data, ignore_index=True)
# a = final_dataset.to_csv('a.csv')
# print(final_dataset.isnull().sum())
# print("Columns with null values:")
# print(null_columns)
print(final_dataset)
