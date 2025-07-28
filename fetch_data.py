import pandas as pd
from binance.client import Client
import os
from datetime import datetime

# Binance API configuration (replace with your actual API keys or environment variables)
# It's recommended to use environment variables for security.
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

client = Client(API_KEY, API_SECRET)

def fetch_binance_futures_klines(symbol, interval, start_str, end_str=None):
    """
    Fetches historical klines (OHLCV) data from Binance Futures.
    """
    print(f"Fetching {symbol} {interval} data from {start_str} to {end_str if end_str else 'now'}...")
    klines = client.futures_historical_klines(
        symbol=symbol,
        interval=interval,
        start_str=start_str,
        end_str=end_str
    )

    df = pd.DataFrame(klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])

    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)

    df = df[['open_time', 'open', 'high', 'low', 'close', 'volume']]
    df.set_index('open_time', inplace=True)
    print(f"Fetched {len(df)} candles.")
    return df

if __name__ == "__main__":
    symbol = 'BTCUSDT'
    interval = '1m'
    start_date = '2024-01-01'
    end_date = '2025-01-01' # Fetch up to but not including this date

    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, 'raw_data.csv')

    df = fetch_binance_futures_klines(symbol, interval, start_date, end_date)
    df.to_csv(file_path)
    print(f"Raw data saved to {file_path}")