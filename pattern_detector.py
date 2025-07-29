
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import talib

class PatternDetector:
    def __init__(self, data,
                 min_cup_duration=30,
                 max_cup_duration=300,
                 min_handle_duration=5,
                 max_handle_duration=50,
                 min_r2=0.85,
                 skip_days_after_pattern=1,
                 one_pattern_per_day=True):
        
        self.data = data.copy()
        self.min_cup_duration = min_cup_duration
        self.max_cup_duration = max_cup_duration
        self.min_handle_duration = min_handle_duration
        self.max_handle_duration = max_handle_duration
        self.min_r2 = min_r2
        self.skip_days_after_pattern = skip_days_after_pattern
        self.one_pattern_per_day = one_pattern_per_day

        # Precompute average candle size & ATR once
        self.avg_candle_size = (self.data['high'] - self.data['low']).mean()
        self.data['ATR'] = talib.ATR(
            self.data['high'],
            self.data['low'],
            self.data['close'],
            timeperiod=14
        )

        # Precompute timestamp arrays for faster searching
        self.timestamps = self.data.index.to_numpy()
        self.timestamps_int = self.data.index.view(np.int64)

    def _parabolic_curve(self, x, a, b, c):
        return a * x**2 + b * x + c

    def _fit_parabolic_cup(self, cup_prices):
        """Fits a parabolic curve and returns R²."""
        x = np.arange(len(cup_prices))
        try:
            popt, _ = curve_fit(self._parabolic_curve, x, cup_prices)
            y_pred = self._parabolic_curve(x, *popt)
            ss_res = np.sum((cup_prices - y_pred) ** 2)
            ss_tot = np.sum((cup_prices - np.mean(cup_prices)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            return r_squared, popt
        except (RuntimeError, ValueError):
            return -1.0, None

    def detect_patterns(self):
        patterns = []
        n = len(self.data)
        # Start from the earliest index which can possibly form a cup
        i = self.min_cup_duration  
        last_detected_day = None

        # For speed, grab local copies of columns where possible
        prices_close = self.data['close'].values
        atr_vals = self.data['ATR'].values

        # Use a while loop to allow index skipping after a detected pattern
        while i < n - self.max_handle_duration - 11:  # buffer for handle & breakout
            cup_found = False
            # Bound the cup search indices
            j_start = max(0, i - self.max_cup_duration)
            j_end = i - self.min_cup_duration
            for j in range(j_end, j_start - 1, -1):
                cup_segment = self.data.iloc[j:i+1]
                if len(cup_segment) < self.min_cup_duration:
                    continue

                cup_prices = cup_segment['close'].values
                cup_bottom_local = np.argmin(cup_prices)
                cup_bottom_price = cup_prices[cup_bottom_local]

                r_squared, _ = self._fit_parabolic_cup(cup_prices)
                if r_squared < self.min_r2:
                    continue

                # Rims from cup segment
                left_rim_price = cup_segment['high'].iloc[0]
                right_rim_price = cup_segment['high'].iloc[-1]
                if abs(left_rim_price - right_rim_price) / ((left_rim_price + right_rim_price) / 2) > 0.10:
                    continue

                cup_depth = max(left_rim_price, right_rim_price) - cup_bottom_price
                # Use precomputed avg_candle_size instead of per-index DataFrame lookup
                if cup_depth < 2 * self.avg_candle_size:
                    continue

                # Now search for a valid handle
                for k in range(i + self.min_handle_duration, min(i + self.max_handle_duration, n - 11) + 1):
                    handle_segment = self.data.iloc[i:k+1]
                    handle_high = handle_segment['high'].max()
                    handle_low = handle_segment['low'].min()

                    if handle_high > max(left_rim_price, right_rim_price):
                        continue
                    handle_retrace = max(left_rim_price, right_rim_price) - handle_low
                    if handle_retrace > 0.40 * cup_depth:
                        continue
                    if handle_low < cup_bottom_price:
                        continue

                    # Detect breakout in a fixed 10-candle window after handle end
                    breakout_segment = self.data.iloc[k+1:min(k+11, n)]
                    # Use vectorized comparison on breakout_segment
                    cond = breakout_segment['close'] > handle_high + 1.5 * breakout_segment['ATR']
                    if not cond.any():
                        continue

                    # Ensure bullish breakout occurs above handle's upper resistance
                    breakout_price = breakout_segment.loc[cond.idxmax(), 'close']
                    if breakout_price <= handle_high:
                        continue

                    # Use the index label directly instead of re-indexing
                    breakout_idx = cond.idxmax()
                    pattern_day = cup_segment.index[0].date()
                    if self.one_pattern_per_day and last_detected_day == pattern_day:
                        continue

                    pattern = {
                        'start_time': cup_segment.index[0],
                        'end_time': breakout_idx,
                        'cup_start_idx': j,
                        'cup_end_idx': i,
                        'handle_start_idx': i,
                        'handle_end_idx': k,
                        'breakout_candle_idx': self.data.index.get_loc(breakout_idx),
                        'cup_depth': cup_depth,
                        'cup_duration': len(cup_segment),
                        'handle_depth': handle_high - handle_low,
                        'handle_duration': len(handle_segment),
                        'r_squared_cup': r_squared,
                        'left_rim_price': left_rim_price,
                        'right_rim_price': right_rim_price,
                        'cup_bottom_price': cup_bottom_price,
                        'handle_high_price': handle_high,
                        'breakout_price': breakout_price,
                        'breakout_candle_timestamp': breakout_idx,
                        'status': 'Valid',
                        'reason': ''
                    }
                    patterns.append(pattern)
                    last_detected_day = pattern_day
                    # Skip ahead after a pattern is found using precomputed timestamps
                    skip_time = pd.Timestamp(breakout_idx) + pd.Timedelta(days=self.skip_days_after_pattern)
                    future_idx = np.searchsorted(self.timestamps_int, np.int64(skip_time.value))
                    i = max(future_idx, k + 1)
                    cup_found = True
                    break  # Exit handle loop once valid handle is found
                if cup_found:
                    break  # Cup found, move to next candidate starting at new i
            if not cup_found:
                i += 1  # If no cup/handle detected, move forward one step

        return patterns