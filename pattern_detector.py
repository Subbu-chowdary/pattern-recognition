import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import talib
from datetime import datetime

# --- Global parabolic_curve function for consistency and easier access ---
def parabolic_curve(x, a, b, c):
    """Parabolic function for cup fitting."""
    return a * x**2 + b * x + c

class PatternDetector:
    def __init__(self, data):
        self.data = data
        self.data['avg_candle_size'] = (self.data['high'] - self.data['low']).mean()
        # Ensure ATR is calculated on numpy arrays for TA-Lib
        self.data['ATR'] = talib.ATR(self.data['high'].values, self.data['low'].values, self.data['close'].values, timeperiod=14)

    def _parabolic_curve_fit_func(self, x, a, b, c): # Renamed to avoid confusion with internal method
        return parabolic_curve(x, a, b, c)

    def _fit_parabolic_cup(self, cup_prices):
        """Fits a parabolic curve to the cup prices and returns R^2 and popt."""
        x = np.arange(len(cup_prices))
        try:
            popt, pcov = curve_fit(self._parabolic_curve_fit_func, x, cup_prices)
            y_pred = self._parabolic_curve_fit_func(x, *popt)
            ss_res = np.sum((cup_prices - y_pred)**2)
            ss_tot = np.sum((cup_prices - np.mean(cup_prices))**2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0 # Avoid division by zero
            return r_squared, popt
        except (RuntimeError, ValueError):
            return -1.0, None # Indicate fit failure

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

        # Start scanning from a reasonable index to allow lookback for max_cup_duration
        start_scan_idx = max_cup_duration 
        for i in range(start_scan_idx, n): # Loop through potential right rim end points
            # Look for cup to the left of i (right rim)
            # j is the potential start of the cup
            for j in range(max(0, i - max_cup_duration), i - min_cup_duration + 1): # Iterate backwards from right to left
                # Ensure segment indices are valid
                if j < 0: 
                    continue # Skip if segment goes out of bounds

                cup_segment = self.data.iloc[j:i+1]
                cup_prices = cup_segment['close']

                if len(cup_prices) < min_cup_duration or len(cup_prices) > max_cup_duration:
                    continue # Ensure cup duration rules are met

                # Find the lowest point in the cup segment (potential cup bottom)
                cup_bottom_idx_in_segment = cup_prices.idxmin()
                cup_bottom_price = cup_prices.min()
                cup_bottom_timestamp = cup_segment.index[cup_segment.index.get_loc(cup_bottom_idx_in_segment)] # Get actual timestamp

                # Cup formation check: smooth, rounded bottom (R^2 for parabolic fit)
                r_squared, popt_params = self._fit_parabolic_cup(cup_prices) # Capture popt_params here
                if r_squared is None or r_squared < 0.85: # Not a smooth parabolic shape (V-shaped)
                    continue

                # Identify left and right rims
                left_rim_price = cup_segment['high'].iloc[0]
                right_rim_price = cup_segment['high'].iloc[-1]

                # Rims at similar price levels (within 10%)
                if abs(left_rim_price - right_rim_price) / ((left_rim_price + right_rim_price) / 2) > 0.10:
                    continue

                cup_depth = max(left_rim_price, right_rim_price) - cup_bottom_price
                if cup_depth < 2 * self.data['avg_candle_size'].iloc[i]: # Check cup depth against average candle size
                    continue

                # Now look for the handle after the cup
                # k is the potential end of the handle
                for k in range(i + min_handle_duration, i + max_handle_duration + 1):
                    if k >= n: # Ensure handle segment does not go out of bounds
                        continue

                    handle_segment = self.data.iloc[i:k+1]
                    handle_high = handle_segment['high'].max()
                    handle_low = handle_segment['low'].min()

                    # Handle high must be below or equal to left/right rim
                    if handle_high > max(left_rim_price, right_rim_price):
                        continue

                    # Handle retraces no more than 40% of cup depth
                    handle_retrace_amount = (max(left_rim_price, right_rim_price) - handle_high)
                    if handle_retrace_amount > 0.40 * cup_depth:
                        continue

                    # Invalidation: Handle breaks below cup bottom
                    if handle_low < cup_bottom_price:
                        continue

                    # Invalidation: Handle lasts longer than 50 candles (handled by loop range, but redundant check)
                    if len(handle_segment) > max_handle_duration:
                        continue

                    # Check for breakout after the handle
                    breakout_start_idx = k + 1
                    breakout_window = 10 # Define a small window for breakout (e.g., 5-10 candles after handle)
                    breakout_end_idx = min(k + breakout_window, n - 1)

                    breakout_segment = self.data.iloc[breakout_start_idx:breakout_end_idx+1]
                    
                    breakout_candle = None
                    if not breakout_segment.empty:
                        breakout_threshold = handle_high
                        for l in range(len(breakout_segment)):
                            current_candle = breakout_segment.iloc[l]
                            # A bullish breakout candle is one that closes significantly above the handle high
                            if current_candle['close'] > breakout_threshold + 1.5 * current_candle['ATR']:
                                breakout_candle = current_candle
                                break
                    
                    if breakout_candle is None: # No breakout after handle formation within window
                        # Capture as invalid pattern if no breakout or no breakout segment
                        pattern = self._create_pattern(
                            cup_segment, handle_segment, None, # No breakout candle
                            r_squared, popt_params, cup_bottom_timestamp,
                            cup_depth, len(cup_segment),
                            handle_high - handle_low, len(handle_segment),
                            left_rim_price, right_rim_price, cup_bottom_price,
                            handle_high, None, # No breakout price
                            'Invalid', 'No valid breakout candle found after handle'
                        )
                        patterns.append(pattern)
                        continue # Move to next possible handle/cup, as this one didn't breakout

                    # If all conditions met, it's a valid pattern
                    pattern = self._create_pattern(
                        cup_segment, handle_segment, breakout_candle,
                        r_squared, popt_params, cup_bottom_timestamp, # Pass popt_params and cup_bottom_timestamp
                        cup_depth, len(cup_segment),
                        handle_high - handle_low, len(handle_segment),
                        left_rim_price, right_rim_price, cup_bottom_price,
                        handle_high, breakout_candle['close'],
                        'Valid', ''
                    )
                    patterns.append(pattern)
                    
                    # To avoid overlapping patterns, move the main loop index past the detected pattern
                    # This ensures distinct patterns and improves efficiency.
                    i = breakout_end_idx 
                    break # Break from handle loop to find next cup from new starting point
                else: # This else belongs to the inner 'for k' loop, meaning no valid handle found
                    continue # Continue outer loop to check for next cup
                break # Break from cup loop to find next cup from new starting point (due to 'i = breakout_end_idx')
        return patterns

    def _create_pattern(self, cup_segment, handle_segment, breakout_candle,
                        r_squared, popt_params, cup_bottom_timestamp, # Added parameters
                        cup_depth, cup_duration, handle_depth, handle_duration,
                        left_rim_price, right_rim_price, cup_bottom_price, # Ensure these are present
                        handle_high_price, breakout_price, # Ensure these are present
                        status, reason):
        """Creates a pattern dictionary with labeled data."""
        return {
            'start_time': cup_segment.index[0],
            # Corrected line: Check if breakout_candle is not None
            'end_time': breakout_candle.name if breakout_candle is not None else handle_segment.index[-1],
            'cup_start_idx': self.data.index.get_loc(cup_segment.index[0]),
            'cup_end_idx': self.data.index.get_loc(cup_segment.index[-1]),
            'handle_start_idx': self.data.index.get_loc(handle_segment.index[0]),
            'handle_end_idx': self.data.index.get_loc(handle_segment.index[-1]),
            'breakout_candle_idx': self.data.index.get_loc(breakout_candle.name) if breakout_candle is not None else None,
            'cup_depth': cup_depth,
            'cup_duration': cup_duration,
            'handle_depth': handle_depth,
            'handle_duration': handle_duration,
            'r_squared_cup': r_squared,
            'popt': popt_params.tolist() if popt_params is not None else None, # Store popt as list for JSON compatibility
            'cup_bottom_timestamp': cup_bottom_timestamp,
            'left_rim_price': left_rim_price,
            'right_rim_price': right_rim_price,
            'cup_bottom_price': cup_bottom_price,
            'handle_high_price': handle_high_price,
            'breakout_price': breakout_price,
            'breakout_candle_timestamp': breakout_candle.name if breakout_candle is not None else None,
            'status': status,
            'reason': reason
        }