import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import linregress
import talib

class PatternDetector:
    def __init__(self, data):
        self.data = data
        self.data['avg_candle_size'] = (self.data['high'] - self.data['low']).mean()
        self.data['ATR'] = talib.ATR(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)

    def _parabolic_curve(self, x, a, b, c):
        """Parabolic function for cup fitting."""
        return a * x**2 + b * x + c

    def _fit_parabolic_cup(self, cup_prices):
        """Fits a parabolic curve to the cup prices and returns R^2."""
        x = np.arange(len(cup_prices))
        try:
            popt, pcov = curve_fit(self._parabolic_curve, x, cup_prices)
            y_pred = self._parabolic_curve(x, *popt)
            ss_res = np.sum((cup_prices - y_pred)**2)
            ss_tot = np.sum((cup_prices - np.mean(cup_prices))**2)
            r_squared = 1 - (ss_res / ss_tot)
            return r_squared, popt
        except RuntimeError:
            return -1.0, None # Indicate fit failure
        except ValueError:
            return -1.0, None # Indicate fit failure

    def _find_swing_highs_lows(self, segment, window=5):
        """Finds significant swing highs and lows in a price segment."""
        # Simple local max/min for swing points
        swing_highs = []
        swing_lows = []
        for i in range(window, len(segment) - window):
            if segment['high'].iloc[i] == segment['high'].iloc[i-window:i+window+1].max():
                swing_highs.append(segment.iloc[i].name)
            if segment['low'].iloc[i] == segment['low'].iloc[i-window:i+window+1].min():
                swing_lows.append(segment.iloc[i].name)
        return swing_highs, swing_lows

    def detect_patterns(self):
        """
        Detects Cup and Handle patterns in the data.
        Returns a list of dictionaries, each representing a detected pattern.
        """
        patterns = []
        n = len(self.data)
        min_cup_duration = 30  # candles
        max_cup_duration = 300 # candles
        min_handle_duration = 5  # candles
        max_handle_duration = 50 # candles

        for i in range(n):
            # Try to find the cup bottom
            # This is a simplification; a real implementation would use more sophisticated methods
            # to identify potential cup structures, possibly involving significant swing lows.
            # For demonstration, we'll iterate and look for cup characteristics.

            # Assume 'i' is the potential right rim of the cup
            # Look for a cup to the left of 'i'
            for j in range(i - min_cup_duration, i - max_cup_duration - 1, -1):
                if j < 0:
                    continue

                cup_segment = self.data.iloc[j:i+1]
                cup_prices = cup_segment['close']

                if len(cup_prices) < min_cup_duration: # Ensure cup duration
                    continue

                # Find the lowest point in the cup segment (potential cup bottom)
                cup_bottom_idx = cup_prices.idxmin()
                cup_bottom_price = cup_prices.min()
                cup_bottom_pos = cup_segment.index.get_loc(cup_bottom_idx)

                # Cup formation check: smooth, rounded bottom (R^2 for parabolic fit)
                r_squared, popt = self._fit_parabolic_cup(cup_prices)
                if r_squared < 0.85: #
                    continue # Not a smooth parabolic shape (V-shaped)

                # Identify left and right rims
                # Left rim is the start of the cup segment
                left_rim_idx = cup_segment.index[0]
                left_rim_price = cup_segment['high'].iloc[0]
                # Right rim is the end of the cup segment
                right_rim_idx = cup_segment.index[-1]
                right_rim_price = cup_segment['high'].iloc[-1]

                # Rims at similar price levels
                if abs(left_rim_price - right_rim_price) / ((left_rim_price + right_rim_price) / 2) > 0.10: #
                    continue

                cup_depth = max(left_rim_price, right_rim_price) - cup_bottom_price
                if cup_depth < 2 * self.data['avg_candle_size'].iloc[i]: #
                    continue

                # Now look for the handle after the cup
                for k in range(i + min_handle_duration, i + max_handle_duration + 1):
                    if k >= n:
                        continue

                    handle_segment = self.data.iloc[i:k+1]
                    handle_high = handle_segment['high'].max()
                    handle_low = handle_segment['low'].min()

                    # Handle high must be below or equal to left/right rim
                    if handle_high > max(left_rim_price, right_rim_price):
                        continue

                    # Handle retraces no more than 40% of cup depth
                    handle_retrace = (max(left_rim_price, right_rim_price) - handle_high)
                    if handle_retrace > 0.40 * cup_depth:
                        continue

                    # Handle breaks below cup bottom
                    if handle_low < cup_bottom_price:
                        continue

                    # Handle lasts longer than 50 candles
                    if len(handle_segment) > max_handle_duration:
                        continue

                    # Check for breakout after the handle
                    breakout_start_idx = k + 1
                    # Define a small window for breakout (e.g., 5-10 candles after handle)
                    breakout_window = 10
                    breakout_end_idx = min(k + breakout_window, n - 1)

                    breakout_segment = self.data.iloc[breakout_start_idx:breakout_end_idx+1]
                    if breakout_segment.empty:
                        continue

                    # Breakout occurs above handle's upper resistance
                    # The resistance for breakout is the handle high
                    breakout_threshold = handle_high

                    breakout_candle = None
                    for l in range(len(breakout_segment)):
                        current_candle = breakout_segment.iloc[l]
                        # A bullish breakout candle is one that closes significantly above the handle high
                        if current_candle['close'] > breakout_threshold + 1.5 * current_candle['ATR']: #
                            breakout_candle = current_candle
                            break
                    
                    if breakout_candle is None: # No breakout after handle formation
                        continue

                    # If all conditions met, it's a potential pattern
                    pattern = {
                        'start_time': cup_segment.index[0],
                        'end_time': breakout_candle.name,
                        'cup_start_idx': self.data.index.get_loc(cup_segment.index[0]),
                        'cup_end_idx': self.data.index.get_loc(cup_segment.index[-1]),
                        'handle_start_idx': self.data.index.get_loc(handle_segment.index[0]),
                        'handle_end_idx': self.data.index.get_loc(handle_segment.index[-1]),
                        'breakout_candle_idx': self.data.index.get_loc(breakout_candle.name),
                        'cup_depth': cup_depth,
                        'cup_duration': len(cup_segment),
                        'handle_depth': handle_high - handle_low,
                        'handle_duration': len(handle_segment),
                        'r_squared_cup': r_squared,
                        'left_rim_price': left_rim_price,
                        'right_rim_price': right_rim_price,
                        'cup_bottom_price': cup_bottom_price,
                        'handle_high_price': handle_high,
                        'breakout_price': breakout_candle['close'],
                        'breakout_candle_timestamp': breakout_candle.name,
                        'status': 'Valid',
                        'reason': ''
                    }
                    patterns.append(pattern)
                    # To avoid overlapping patterns, move the main loop index past the detected pattern
                    i = breakout_end_idx
                    break # Break from handle loop to find next cup from new starting point
                else: # This else belongs to the inner 'for k' loop, meaning no valid handle found
                    continue
                break # Break from cup loop to find next cup from new starting point
        return patterns


# import numpy as np
# import pandas as pd
# from scipy.signal import argrelextrema
# from scipy.stats import linregress

# def is_parabolic_shape(y_vals, tolerance=0.85):
#     x = np.arange(len(y_vals))
#     coeffs = np.polyfit(x, y_vals, 2)
#     y_fit = np.polyval(coeffs, x)
#     residual = y_vals - y_fit
#     ss_res = np.sum(residual**2)
#     ss_tot = np.sum((y_vals - np.mean(y_vals))**2)
#     r_squared = 1 - (ss_res / ss_tot if ss_tot else 0)
#     return r_squared >= tolerance

# def detect_patterns(df):
#     df = df.copy()
#     df['close'] = df['close'].astype(float)
#     patterns = []

#     for i in range(30, len(df) - 100):  # start at 30 to leave space for cup
#         window = df.iloc[i:i+300]
#         closes = window['close'].values

#         # Detect local minima (potential cup bottoms)
#         minima_idx = argrelextrema(closes, np.less_equal, order=5)[0]
#         maxima_idx = argrelextrema(closes, np.greater_equal, order=5)[0]

#         if len(minima_idx) == 0 or len(maxima_idx) < 2:
#             continue

#         for bottom in minima_idx:
#             left_candidates = maxima_idx[maxima_idx < bottom]
#             right_candidates = maxima_idx[maxima_idx > bottom]

#             if len(left_candidates) == 0 or len(right_candidates) == 0:
#                 continue

#             left = left_candidates[-1]
#             right = right_candidates[0]

#             # Validation: Cup shape
#             cup_range = closes[left:right + 1]
#             if len(cup_range) < 30 or len(cup_range) > 300:
#                 continue

#             avg_candle = np.mean(np.abs(np.diff(closes)))
#             cup_depth = max(closes[left], closes[right]) - closes[bottom]
#             if cup_depth < 2 * avg_candle:
#                 continue

#             if not is_parabolic_shape(cup_range):
#                 continue

#             # Detect handle
#             handle_start = right
#             handle_end = handle_start + 50 if handle_start + 50 < len(closes) else len(closes) - 1
#             handle_prices = closes[handle_start:handle_end]

#             if len(handle_prices) < 5:
#                 continue

#             handle_peak = np.max(handle_prices)
#             handle_trough = np.min(handle_prices)
#             handle_retrace = (handle_peak - handle_trough) / cup_depth

#             if handle_peak > closes[right] or handle_retrace > 0.4:
#                 continue

#             # Breakout detection
#             breakout_idx = handle_end + np.argmax(closes[handle_end:handle_end+10] > handle_peak)
#             if breakout_idx == 0:
#                 continue

#             global_idx = i + left
#             pattern = {
#                 "start": i + left,
#                 "left_rim": i + left,
#                 "bottom": i + bottom,
#                 "right_rim": i + right,
#                 "handle_end": i + handle_end,
#                 "breakout": i + handle_end + breakout_idx,
#                 "end": i + handle_end + breakout_idx
#             }
#             patterns.append(pattern)

#     return patterns