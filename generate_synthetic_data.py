import pandas as pd
import numpy as np
import talib
import os
from datetime import datetime, timedelta
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score

def parabolic_curve(x, a, b, c):
    """Parabolic function for cup shape."""
    return a * x**2 + b * x + c

def generate_cup_and_handle_segment(cup_duration, handle_duration, breakout_duration, base_price, avg_candle_size):
    """Generate a single Cup and Handle pattern meeting validation rules."""
    # Cup: Parabolic shape
    cup_x = np.arange(cup_duration)
    cup_depth = np.random.uniform(2.5, 5) * avg_candle_size
    a = cup_depth / (cup_duration / 2)**2
    cup_prices = parabolic_curve(cup_x, -a, a * cup_duration, base_price - cup_depth)
    
    # Verify parabolic fit (R² > 0.85)
    popt, _ = curve_fit(parabolic_curve, cup_x, cup_prices)
    r2 = r2_score(cup_prices, parabolic_curve(cup_x, *popt))
    if r2 < 0.85:
        a *= 1.1
        cup_prices = parabolic_curve(cup_x, -a, a * cup_duration, base_price - cup_depth)
    
    # Ensure rims are within 10% of each other
    left_rim = cup_prices[0]
    right_rim = cup_prices[-1]
    attempts = 0
    while abs(left_rim - right_rim) / ((left_rim + right_rim) / 2) > 0.1 and attempts < 5:
        cup_prices += np.random.uniform(-avg_candle_size * 0.1, avg_candle_size * 0.1, cup_duration)
        left_rim = cup_prices[0]
        right_rim = cup_prices[-1]
        attempts += 1
    if attempts >= 5:
        cup_prices[-1] = left_rim * np.random.uniform(0.95, 1.05)

    # Handle: Downward or sideways consolidation
    handle_retrace = np.random.uniform(0.1, 0.4) * cup_depth
    handle_prices = np.linspace(right_rim, right_rim - handle_retrace, handle_duration)
    handle_prices += np.random.normal(0, avg_candle_size * 0.1, handle_duration)
    handle_high = np.max(handle_prices)
    
    # Breakout: Sharp upward move
    atr = avg_candle_size * 1.5
    breakout_target = handle_high + 1.5 * atr
    breakout_prices = np.linspace(handle_high, breakout_target, breakout_duration)
    breakout_prices += np.random.normal(0, avg_candle_size * 0.05, breakout_duration)
    
    # Combine prices
    prices = np.concatenate([cup_prices, handle_prices, breakout_prices])
    segment_length = cup_duration + handle_duration + breakout_duration
    ohlc = {
        'open': prices + np.random.uniform(-avg_candle_size * 0.2, avg_candle_size * 0.2, segment_length),
        'high': prices + np.random.uniform(avg_candle_size * 0.1, avg_candle_size * 0.5, segment_length),
        'low': prices - np.random.uniform(avg_candle_size * 0.1, avg_candle_size * 0.5, segment_length),
        'close': prices + np.random.uniform(-avg_candle_size * 0.2, avg_candle_size * 0.2, segment_length)
    }
    
    # Volume: Decrease at cup bottom, increase at rims, spike on breakout
    volume = np.ones(segment_length) * 100
    first_half = (cup_duration + 1) // 2
    second_half = cup_duration - first_half
    if first_half > 0 and second_half > 0:
        volume[:cup_duration] = np.concatenate([np.linspace(150, 80, first_half), np.linspace(80, 150, second_half)])
    volume[cup_duration:cup_duration + handle_duration] = 100
    volume[-breakout_duration:] = np.random.uniform(200, 300, breakout_duration)
    
    return ohlc, volume

def generate_synthetic_data(start_time='2024-01-01', end_time='2024-01-08', num_patterns=30):
    """Generate synthetic OHLCV data with 30 Cup and Handle patterns (reduced to ~10,000 candles)."""
    print(f"Generating synthetic Cup and Handle data from {start_time} to {end_time}...")
    
    start_time = datetime.strptime(start_time, '%Y-%m-%d')
    end_time = datetime.strptime(end_time, '%Y-%m-%d')
    
    timestamps = pd.date_range(start=start_time, end=end_time, freq='1min')
    total_candles = len(timestamps)  # Approx 10,080 candles (1 week)
    
    np.random.seed(42)
    base_price = 50000
    avg_candle_size = 50
    price_trend = np.random.normal(0, avg_candle_size, total_candles).cumsum() + base_price
    price_trend += np.linspace(0, 500, total_candles)  # Smaller trend for shorter period
    
    data = {
        'open': price_trend,
        'high': price_trend + np.random.uniform(0, avg_candle_size * 0.5, total_candles),
        'low': price_trend - np.random.uniform(0, avg_candle_size * 0.5, total_candles),
        'close': price_trend + np.random.uniform(-avg_candle_size * 0.2, avg_candle_size * 0.2, total_candles),
        'volume': np.random.uniform(100, 200, total_candles)
    }
    df = pd.DataFrame(data, index=timestamps)
    df.index.name = 'open_time'
    
    min_gap = 200  # Reduced gap to fit 30 patterns in 10,000 candles
    pattern_indices = np.sort(np.random.choice(range(500, total_candles - 500, min_gap), num_patterns, replace=False))
    
    for idx in pattern_indices:
        cup_duration = np.random.randint(30, 301)
        handle_duration = np.random.randint(5, 51)
        breakout_duration = 10
        segment_length = cup_duration + handle_duration + breakout_duration
        
        if idx + segment_length > total_candles:
            continue
        
        ohlc, volume = generate_cup_and_handle_segment(
            cup_duration, handle_duration, breakout_duration, df['close'].iloc[idx], avg_candle_size
        )
        
        df.iloc[idx:idx + segment_length, df.columns.get_loc('open')] = ohlc['open']
        df.iloc[idx:idx + segment_length, df.columns.get_loc('high')] = ohlc['high']
        df.iloc[idx:idx + segment_length, df.columns.get_loc('low')] = ohlc['low']
        df.iloc[idx:idx + segment_length, df.columns.get_loc('close')] = ohlc['close']
        df.iloc[idx:idx + segment_length, df.columns.get_loc('volume')] = volume
    
    df['avg_candle_size'] = (df['high'] - df['low']).mean()
    df['ATR'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
    
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)
    raw_data_path = os.path.join(data_dir, 'raw_data.csv')
    preprocessed_data_path = os.path.join(data_dir, 'preprocessed_data.csv')
    
    df_raw = df[['open', 'high', 'low', 'close', 'volume']].copy()
    df_raw.to_csv(raw_data_path)
    print(f"Raw data saved to {raw_data_path}")
    
    df.to_csv(preprocessed_data_path)
    print(f"Preprocessed data saved to {preprocessed_data_path}")
    
    print(f"Synthetic data generated: {len(df)} candles with {num_patterns} patterns.")
    return df

if __name__ == "__main__":
    df = generate_synthetic_data()