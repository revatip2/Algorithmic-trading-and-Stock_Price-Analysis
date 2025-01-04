# Import modules and packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import datetime
import yfinance as yf
from keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint, TensorBoard
from sklearn.preprocessing import StandardScaler
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout
from keras.optimizers import Adam
import mysql.connector
from lstm import preprocess_stock_data

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
    name_str = f'models/{stock_symbol}.h5'
    model.save(name_str)

sql_user = input("Enter MySQL username:\n")
sql_pass = input("Enter MySQL password:\n")

conn = mysql.connector.connect(
    host='localhost',
    user=sql_user,
    password=sql_pass,
    database='stocks_portfolio_2'
)
cursor = conn.cursor()

fetch_symbols_query = 'SELECT DISTINCT symbol FROM stocks;'
cursor.execute(fetch_symbols_query)
symbols_result = cursor.fetchall()

if symbols_result:
    symbols = [symbol[0] for symbol in symbols_result]
print(symbols)
start_date = '2013-01-01'
end_date = '2024-01-01'

for stock_symbol in symbols:
    X_train, sc_predict, dataset_train, y_train = preprocess_stock_data(stock_symbol, start_date, end_date)
    model_init(stock_symbol,n_past=90, dataset_train=dataset_train, X_train=X_train, y_train=y_train)
