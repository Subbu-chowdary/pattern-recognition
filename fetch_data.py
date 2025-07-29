
# import pandas as pd
# from binance.client import Client
# import os
# from datetime import datetime

# API_KEY = os.getenv('BINANCE_API_KEY', 'your_api_key')
# API_SECRET = os.getenv('BINANCE_API_SECRET', 'your_api_secret')

# client = Client(API_KEY, API_SECRET)

# def fetch_binance_futures_klines(symbol, interval, start_str, end_str=None):
#     print(f"Fetching {symbol} {interval} data from {start_str} to {end_str or 'now'}...")
#     try:
#         klines = client.futures_historical_klines(
#             symbol=symbol,
#             interval=interval,
#             start_str=start_str,
#             end_str=end_str
#         )
#     except Exception as e:
#         print(f"Error fetching data: {e}")
#         return None

#     df = pd.DataFrame(klines, columns=[
#         'open_time', 'open', 'high', 'low', 'close', 'volume',
#         'close_time', 'quote_asset_volume', 'number_of_trades',
#         'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
#     ])
#     df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
#     df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
#     df = df[['open_time', 'open', 'high', 'low', 'close', 'volume']]
#     df.set_index('open_time', inplace=True)
#     print(f"Fetched {len(df)} candles.")
#     return df

# if __name__ == "__main__":
#     symbol = 'BTCUSDT'
#     interval = '1m'
#     start_date = '2024-10-01'
#     end_date = '2025-01-01'
#     data_dir = 'data'
#     os.makedirs(data_dir, exist_ok=True)
#     file_path = os.path.join(data_dir, 'raw_data.csv')
#     df = fetch_binance_futures_klines(symbol, interval, start_date, end_date)
#     if df is not None:
#         df.to_csv(file_path)
#         print(f"Raw data saved to {file_path}")

import pandas as pd
from binance.client import Client
import os
from datetime import datetime, timedelta

API_KEY = os.getenv('BINANCE_API_KEY', 'your_api_key')
API_SECRET = os.getenv('BINANCE_API_SECRET', 'your_api_secret')

client = Client(API_KEY, API_SECRET)

def fetch_binance_futures_klines(symbol, interval, start_str, end_str=None):
    """
    Fetches historical klines (OHLCV) data from Binance Futures with pagination.
    """
    print(f"Fetching {symbol} {interval} data from {start_str} to {end_str or 'now'}...")
    klines = []
    start_time = datetime.strptime(start_str, '%Y-%m-%d')
    end_time = datetime.strptime(end_str, '%Y-%m-%d') if end_str else datetime.now()

    while start_time < end_time:
        chunk_end_time = min(start_time + timedelta(minutes=500), end_time)
        try:
            chunk_klines = client.futures_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_time.strftime('%Y-%m-%d %H:%M:%S'),
                end_str=chunk_end_time.strftime('%Y-%m-%d %H:%M:%S')
            )
            klines.extend(chunk_klines)
            print(f"Fetched {len(chunk_klines)} candles up to {chunk_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            start_time = chunk_end_time
        except Exception as e:
            print(f"Error fetching data: {e}")
            break

    if not klines:
        print("No data fetched.")
        return None

    df = pd.DataFrame(klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    df = df[['open_time', 'open', 'high', 'low', 'close', 'volume']]
    df.set_index('open_time', inplace=True)
    print(f"Total fetched {len(df)} candles.")
    return df

if __name__ == "__main__":
    symbol = 'BTCUSDT'
    interval = '1m'
    start_date = '2024-01-01'
    end_date = '2024-01-30'
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, 'raw_data.csv')
    df = fetch_binance_futures_klines(symbol, interval, start_date, end_date)
    if df is not None:
        df.to_csv(file_path)
        print(f"Raw data saved to {file_path}")

