import unittest
import pandas as pd
import numpy as np
from pattern_detector import PatternDetector
import talib

class TestPatternDetector(unittest.TestCase):

    def setUp(self):
        # Create a mock DataFrame for testing
        # This data needs to be carefully constructed to test specific scenarios
        # For simplicity, let's create a linear increasing trend with a dip for a cup
        data = {
            'open_time': pd.to_datetime(pd.date_range(start='2024-01-01', periods=500, freq='1min')),
            'open': np.linspace(100, 150, 500),
            'high': np.linspace(101, 151, 500),
            'low': np.linspace(99, 149, 500),
            'close': np.linspace(100.5, 150.5, 500),
            'volume': np.random.randint(100, 1000, 500)
        }
        self.mock_df = pd.DataFrame(data).set_index('open_time')

        # Manually inject a "cup" like structure for testing purposes
        # A simple V-shape for now, will need to be parabolic for proper R^2 test
        self.mock_df.loc[self.mock_df.index[100:200], 'close'] = np.concatenate([
            np.linspace(120, 110, 50), # Downward slope
            np.linspace(110, 120, 50)  # Upward slope
        ])
        self.mock_df.loc[self.mock_df.index[100:200], 'high'] = self.mock_df['close'][100:200] + 1
        self.mock_df.loc[self.mock_df.index[100:200], 'low'] = self.mock_df['close'][100:200] - 1
        self.mock_df.loc[self.mock_df.index[100:200], 'open'] = self.mock_df['close'][100:200]

        # Add ATR and avg_candle_size, which are used by the detector
        self.mock_df['avg_candle_size'] = (self.mock_df['high'] - self.mock_df['low']).mean()
        self.mock_df['ATR'] = talib.ATR(self.mock_df['high'], self.mock_df['low'], self.mock_df['close'], timeperiod=14)
        
        self.detector = PatternDetector(self.mock_df.copy())

    def test_parabolic_curve_fit(self):
        # Test a perfectly parabolic shape
        x_perfect = np.arange(100)
        y_perfect = 0.01 * x_perfect**2 - 1.0 * x_perfect + 50
        
        # Create a DataFrame segment for this perfect cup
        perfect_cup_data = pd.DataFrame({
            'close': y_perfect,
            'high': y_perfect + 1,
            'low': y_perfect - 1,
            'open': y_perfect,
            'volume': 100
        }, index=pd.to_datetime(pd.date_range(start='2024-01-01', periods=100, freq='1min')))
        perfect_cup_data['avg_candle_size'] = 1.0
        perfect_cup_data['ATR'] = 1.0 # Mock ATR for this test

        # Use a temporary detector instance for this specific test case
        temp_detector = PatternDetector(perfect_cup_data)

        r_squared, _ = temp_detector._fit_parabolic_cup(perfect_cup_data['close'])
        self.assertGreater(r_squared, 0.95, "Should fit a perfect parabola with high R^2")

        # Test a V-shaped curve (low R^2)
        x_vshape = np.arange(100)
        y_vshape = np.concatenate([np.linspace(100, 50, 50), np.linspace(50, 100, 50)])
        
        vshape_cup_data = pd.DataFrame({
            'close': y_vshape,
            'high': y_vshape + 1,
            'low': y_vshape - 1,
            'open': y_vshape,
            'volume': 100
        }, index=pd.to_datetime(pd.date_range(start='2024-01-01', periods=100, freq='1min')))
        vshape_cup_data['avg_candle_size'] = 1.0
        vshape_cup_data['ATR'] = 1.0 # Mock ATR for this test

        temp_detector_v = PatternDetector(vshape_cup_data)
        r_squared_v, _ = temp_detector_v._fit_parabolic_cup(vshape_cup_data['close'])
        self.assertLess(r_squared_v, 0.7, "Should have low R^2 for a V-shape")


    def test_detect_patterns_no_pattern(self):
        # Test case where no pattern exists in simple linear data
        data = {
            'open_time': pd.to_datetime(pd.date_range(start='2024-01-01', periods=200, freq='1min')),
            'open': np.linspace(100, 200, 200),
            'high': np.linspace(101, 201, 200),
            'low': np.linspace(99, 199, 200),
            'close': np.linspace(100.5, 200.5, 200),
            'volume': np.random.randint(100, 1000, 200)
        }
        df_no_pattern = pd.DataFrame(data).set_index('open_time')
        df_no_pattern['avg_candle_size'] = (df_no_pattern['high'] - df_no_pattern['low']).mean()
        df_no_pattern['ATR'] = talib.ATR(df_no_pattern['high'], df_no_pattern['low'], df_no_pattern['close'], timeperiod=14)

        detector_no_pattern = PatternDetector(df_no_pattern)
        patterns = detector_no_pattern.detect_patterns()
        self.assertEqual(len(patterns), 0, "Should detect no patterns in linear data")

    def test_detect_patterns_with_valid_pattern(self):
        # Create a dataset with a clear cup and handle pattern
        # This is a highly simplified example; real patterns are more complex.
        
        # Cup: parabolic dip
        cup_len = 100
        cup_start_price = 100
        cup_bottom_price = 90
        cup_prices = np.linspace(cup_start_price, cup_bottom_price, cup_len // 2)
        cup_prices = np.concatenate((cup_prices, np.linspace(cup_bottom_price, cup_start_price, cup_len // 2)))

        # Add parabolic curve to make it smooth for R^2
        x_cup = np.arange(cup_len)
        a, b, c = np.polyfit(x_cup, cup_prices, 2)
        cup_prices_parabolic = a * x_cup**2 + b * x_cup + c

        # Handle: slight retrace and sideways
        handle_len = 20
        handle_start_price = cup_prices_parabolic[-1]
        handle_prices = np.linspace(handle_start_price - 2, handle_start_price - 1, handle_len)

        # Breakout: strong move up
        breakout_len = 5
        breakout_prices = np.linspace(handle_prices[-1], handle_prices[-1] + 5, breakout_len)

        # Combine for full data
        total_len = 50 + cup_len + handle_len + breakout_len + 50 # Pre/post padding
        full_prices = np.linspace(95, 100, 50) # Pre-cup
        full_prices = np.concatenate((full_prices, cup_prices_parabolic))
        full_prices = np.concatenate((full_prices, handle_prices))
        full_prices = np.concatenate((full_prices, breakout_prices))
        full_prices = np.concatenate((full_prices, np.linspace(full_prices[-1], full_prices[-1] + 2, 50))) # Post-breakout

        data = {
            'open_time': pd.to_datetime(pd.date_range(start='2024-01-01', periods=total_len, freq='1min')),
            'open': full_prices,
            'high': full_prices + 0.5,
            'low': full_prices - 0.5,
            'close': full_prices,
            'volume': np.random.randint(100, 1000, total_len)
        }
        mock_df_pattern = pd.DataFrame(data).set_index('open_time')
        mock_df_pattern['avg_candle_size'] = (mock_df_pattern['high'] - mock_df_pattern['low']).mean()
        mock_df_pattern['ATR'] = talib.ATR(mock_df_pattern['high'], mock_df_pattern['low'], mock_df_pattern['close'], timeperiod=14)

        detector_with_pattern = PatternDetector(mock_df_pattern)
        patterns = detector_with_pattern.detect_patterns()
        
        # Assertions to check if at least one pattern is detected and its properties
        self.assertGreaterEqual(len(patterns), 1, "Should detect at least one pattern")
        
        # You can add more specific assertions here based on the expected characteristics
        # of the manually constructed pattern, e.g., cup duration, handle duration, R^2.
        # For example:
        first_pattern = patterns[0]
        self.assertTrue(first_pattern['cup_duration'] >= 30 and first_pattern['cup_duration'] <= 300)
        self.assertTrue(first_pattern['handle_duration'] >= 5 and first_pattern['handle_duration'] <= 50)
        self.assertGreater(first_pattern['r_squared_cup'], 0.85)
        self.assertEqual(first_pattern['status'], 'Valid')


if __name__ == '__main__':
    unittest.main()