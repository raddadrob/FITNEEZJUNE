from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from alpha_vantage.timeseries import TimeSeries

app = Flask(__name__)

# Set your Alpha Vantage API key
api_key = 'WWTOKNZVMMAFYJ0N'

# Initialize Alpha Vantage TimeSeries object
ts = TimeSeries(key=api_key, output_format='pandas')

# Function to get real-time data
def get_real_time_data(symbol):
    data, _ = ts.get_quote_endpoint(symbol)
    return data

# Function to calculate indicators
def calculate_indicators(df):
    df['MA20'] = df['05. price'].rolling(window=20, min_periods=1).mean()
    df['MA50'] = df['05. price'].rolling(window=50, min_periods=1).mean()
    delta = df['05. price'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    short_ema = df['05. price'].ewm(span=12, adjust=False).mean()
    long_ema = df['05. price'].ewm(span=26, adjust=False).mean()
    df['MACD'] = short_ema - long_ema
    df['Signal Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Buy'] = np.where((df['MA20'] > df['MA50']) & (df['RSI'] < 30) & (df['MACD'] > df['Signal Line']), 1, 0)
    df['Sell'] = np.where((df['MA20'] < df['MA50']) & (df['RSI'] > 70) & (df['MACD'] < df['Signal Line']), 1, 0)
    return df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data', methods=['POST'])
def get_data():
    symbol = request.form['symbol']
    df = pd.DataFrame()
    data = get_real_time_data(symbol)
    df = df.append(data, ignore_index=True)
    df = calculate_indicators(df)
    df_json = df.to_json(orient='records')
    return df_json

if __name__ == '__main__':
    app.run(debug=True)
