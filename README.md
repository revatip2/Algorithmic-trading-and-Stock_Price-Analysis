# Stock Portfolio Management System

## Overview
This repository contains a comprehensive stock portfolio management system designed to facilitate stock tracking, portfolio management, web scraping for stock watchlists, financial metrics calculation, and trading strategy implementation using machine learning techniques. The system integrates multiple modules to allow the user to manage portfolios, perform trading, and evaluate performance based on various financial metrics.

### Key Features:
- **Database Setup**: MySQL-based database for storing portfolio and stock data.
- **Portfolio Management**: Create, update, and delete portfolios. Add or remove stocks from portfolios.
- **Web Scraping**: Fetch stock symbols from Yahoo Finance watchlists.
- **Financial Metrics Calculation**: Calculate various stock metrics like RSI, SMA, Market Cap per Employee, Dividend Yield, Earnings Yield, and more.
- **Trading Strategy**: Implement a trading strategy based on LSTM neural networks and historical stock data.
- **LSTM Model Training**: Train models to predict stock prices and make buy/sell/hold decisions.

## Files

### 1. `create_db.py`
Facilitates the setup of a MySQL database named `stocks_portfolio` for managing portfolios. Creates tables `portfolio` and `stocks` for storing:
- **portfolio**: id, name, creation_date
- **stocks**: id, portfolio_id, symbol

### 2. `menu.py`
A simple command-line user interface to interact with the portfolio database. Features include:
- Create new portfolio and add stocks
- Add/remove stocks to/from existing portfolios
- Delete entire portfolio along with its stocks
- Display existing portfolios and associated stocks
- Web scrape Yahoo Finance watchlist stock symbols for various sectors

### 3. `scraper.py`
A module for web scraping, designed to extract stock symbols from a given URL containing a table of stock data. Uses BeautifulSoup for parsing HTML and Selenium for dynamic content scraping.

### 4. `data_preprocessing.py`
Fetches stock symbols from the database and uses the `yfinance` library to calculate the following financial and market metrics for each stock:
- **Volume Metrics**: Bid-Ask Size Ratio
- **Price Metrics**: Percentage Change from Previous Close
- **Market Cap Metrics**: Market Cap per Employee, Enterprise Value to Revenue Ratio
- **Analyst Recommendation**: Recommendation
- **Executive Compensation**: Total Compensation Ratio
- **Dividend Metrics**: Dividend Yield to 5-Year Avg.
- **Market Performance**: RSI, SMA (50, 200), EMA (50, 200)
- **Liquidity Metrics**: Liquidity Ratio
- **Earnings Metrics**: Earnings Yield, Earnings to Price Ratio, Price to Sales Ratio
- **Time Metrics**: Year, Month, Day, Quarter
- **Financial Metrics**: Earnings Yield, Dividend Payout Ratio, PEG Ratio

### 5. `lstm.py`
Implements Long Short-Term Memory (LSTM) neural networks for stock price prediction. This module:
- Defines functions for calculating market performance metrics like RSI, SMA, and EMA.
- Fetches and preprocesses stock data using Yahoo Finance API (`yfinance`).
- Trains an LSTM model to predict future stock prices based on historical data.

### 6. `tracker.py`
Implements a trading strategy using LSTM predictions. Features:
- Loads the trained LSTM model and tracks stock data.
- Portfolio creation and management (add/remove stocks, delete portfolios).
- Executes daily trading decisions based on simple buy/sell/hold strategy.
- Calculates portfolio value, stock returns, and Sharpe ratio for performance evaluation.

### 7. `model_training.py`
Trains the LSTM model for each stock symbol by fetching historical stock data. It:
- Initializes and trains LSTM models using multiple layers, dropout, and dense layers.
- Uses callbacks like early stopping, learning rate reduction, and model checkpoints.
- Saves the trained models as `.h5` files for future predictions.
- Requires MySQL credentials to fetch stock symbols and train models iteratively.

## Prerequisites
- **MySQL Server**: Installed and running.
- **Python 3.x**: Ensure Python is installed on your system.
- **Required Python Libraries**: `mysql.connector`, `yfinance`, `pandas`,`tabulate`, `requests`, `beautifulsoup4`,`selenium`, `numpy`, `tensorflow`, `keras`, `matplotlib`

Adjust database connection details and the `GeckoDriver` executable path as needed.

## Setup Instructions

### 1. **Database Setup**
Run `create_db.py` to set up the MySQL database and tables:
```bash
python3 create_db.py
```
## 2. Portfolio Management
Run `menu.py` to interact with the portfolio system and perform actions like creating portfolios, adding/removing stocks, and displaying portfolios:

```bash
python3 menu.py
```
Follow the on-screen menu to perform various portfolio management tasks.

## 3. Stock Data Preprocessing
Run `data_preprocessing.py` to fetch stock symbols from the database and calculate financial metrics:

```bash
python3 data_preprocessing.py
```
This will generate a `stocks_dataset.csv` containing calculated metrics for each stock.

## 4. Model Training
Run `model_training.py` to train LSTM models for each stock symbol. This step is essential for the first execution:

```bash
python3 model_training.py
```
This will save trained models as .h5 files.

## 5. Trading Strategy Execution
Run `tracker.py` to execute the trading strategy based on LSTM predictions:

```bash
python3 tracker.py
```
Follow the on-screen menu to manage portfolios, create new portfolios, add stocks, and perform trades.


