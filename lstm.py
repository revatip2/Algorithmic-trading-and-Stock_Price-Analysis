# Import modules and packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
from datetime import datetime
import yfinance as yf
from keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint, TensorBoard
from sklearn.preprocessing import StandardScaler
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout
from keras.optimizers import Adam
import mysql.connector



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

def calculate_market_performance_metrics(stock_info):
    market_perf_metrics = pd.DataFrame()
    # print(stock_info)
    df = pd.DataFrame(stock_info)
    # print(df)

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

def preprocess_stock_data(stock_symbol, start_date, end_date, n_past=90, n_future=60):
    # Fetch stock information
    stock_info = yf.Ticker(stock_symbol)
    dataset_train = stock_info.history(start=start_date, end=end_date)
    dataset_train = dataset_train.iloc[1:]
    
    
    # Calculate market performance metrics
    market_perf_metrics = calculate_market_performance_metrics(dataset_train)
    dataset_train = dataset_train.iloc[1:]
    # Merge market performance metrics with the training dataset
    dataset_train.reset_index(inplace=True)
    # print(dataset_train)
    # print(market_perf_metrics)
    dataset_train = dataset_train.merge(market_perf_metrics)
    
    cols = list(dataset_train)[1:]
    datelist_train = list(dataset_train['Date'])
    dataset_train = dataset_train.set_index('Date')

    # Convert dataset_train to a suitable format
    dataset_train = dataset_train[cols].astype(str)
    for i in cols:
        for j in range(0, len(dataset_train)):
            dataset_train[i][j] = dataset_train[i][j].replace(',', '')
    dataset_train = dataset_train.astype(float)
    training_set = dataset_train.values

    # Feature scaling
    sc = StandardScaler()
    training_set_scaled = sc.fit_transform(training_set)
    sc_predict = StandardScaler()
    sc_predict.fit_transform(training_set[:, 0:1])

    # Prepare X_train and y_train
    X_train = []
    y_train = []
    
    for i in range(n_past, len(training_set_scaled) - n_future + 1):
        X_train.append(training_set_scaled[i - n_past:i, 0:dataset_train.shape[1] - 1])
        y_train.append(training_set_scaled[i + n_future - 1:i + n_future, 0])

    X_train, y_train = np.array(X_train), np.array(y_train)

    return X_train, sc_predict, dataset_train, y_train

def model_init(stock_symbol, n_past, dataset_train, X_train, y_train):
    model = Sequential()
    model.add(LSTM(units=64, return_sequences=True, input_shape=(n_past, dataset_train.shape[1]-1)))
    model.add(LSTM(units=10, return_sequences=False))
    model.add(Dropout(0.25))
    model.add(Dense(units=1, activation='linear'))
    model.compile(optimizer = Adam(learning_rate=0.01), loss='mean_squared_error')
    rlr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, verbose=1)
    mcp = ModelCheckpoint(filepath='weights.h5', monitor='val_loss', verbose=1, save_best_only=True, save_weights_only=True)
    tb = TensorBoard('logs')
    history = model.fit(X_train, y_train, shuffle=True, epochs=100, callbacks=[rlr, mcp, tb], validation_split=0.2, verbose=1, batch_size=128)
    name_str = f'{stock_symbol}.h5'
    model.save(name_str)

# stock_symbol = 'EA'
# start_date = '2013-01-01'
# end_date = '2024-01-01'

# X_train, sc_predict, dataset_train, y_train = preprocess_stock_data(stock_symbol, start_date, end_date)
# model_init(stock_symbol, n_past=90, dataset_train=dataset_train, X_train=X_train, y_train=y_train)


# Final code
# sql_user = input("Enter MySQL username:\n")
# sql_pass = input("Enter MySQL password:\n")

# conn = mysql.connector.connect(
#     host='localhost',
#     user=sql_user,
#     password=sql_pass,
#     database='stocks_portfolio_2'
# )
# cursor = conn.cursor()

# fetch_symbols_query = 'SELECT DISTINCT symbol FROM stocks;'
# cursor.execute(fetch_symbols_query)
# symbols_result = cursor.fetchall()

# if symbols_result:
#     symbols = [symbol[0] for symbol in symbols_result]
# print(symbols)
# start_date = '2013-01-01'
# end_date = '2024-01-01'

# for stock_symbol in symbols:
#     X_train, sc_predict, dataset_train, y_train = preprocess_stock_data(stock_symbol, start_date, end_date)
#     model_init(stock_symbol,n_past=90, dataset_train=dataset_train, X_train=X_train, y_train=y_train)

