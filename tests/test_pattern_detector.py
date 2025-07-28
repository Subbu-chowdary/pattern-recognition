import unittest
import pandas as pd
import numpy as np
from pattern_detector import PatternDetector
import talib

class TestPatternDetector(unittest.TestCase):
    def setUp(self):
        # Synthetic data with a valid cup and handle pattern
        cup_len = 100
        handle_len = 20
        breakout_len = 5
        x_cup = np.arange(cup_len)
        cup_prices = 0.01 * x_cup**2 - 1.0 * x_cup + 100  # Parabolic cup
        handle_prices = np.linspace(cup_prices[-1] - 2, cup_prices[-1] - 1, handle_len)
        breakout_prices = np.linspace(handle_prices[-1], handle_prices[-1] + 5, breakout_len)
        total_len = 50 + cup_len + handle_len + breakout_len + 50
        full_prices = np.concatenate([
            np.linspace(95, 100, 50),
            cup_prices,
            handle_prices,
            breakout_prices,
            np.linspace(breakout_prices[-1], breakout_prices[-1] + 2, 50)
        ])
        data = {
            'open_time': pd.date_range(start='2024-01-01', periods=total_len, freq='1min'),
            'open': full_prices,
            'high': full_prices + 0.5,
            'low': full_prices - 0.5,
            'close': full_prices,
            'volume': np.random.randint(100, 1000, total_len)
        }
        self.df = pd.DataFrame(data).set_index('open_time')
        self.detector = PatternDetector(self.df)

    def test_parabolic_fit(self):
        cup_prices = self.df['close'].iloc[50:150]
        r_squared, _ = self.detector._fit_parabolic_cup(cup_prices)
        self.assertGreater(r_squared, 0.85, "Should fit parabolic cup with high R^2")

    def test_invalid_v_shape(self):
        v_shape = np.concatenate([np.linspace(100, 90, 50), np.linspace(90, 100, 50)])
        df_v = self.df.copy()
        df_v['close'].iloc[50:150] = v_shape
        df_v['high'].iloc[50:150] = v_shape + 0.5
        df_v['low'].iloc[50:150] = v_shape - 0.5
        detector = PatternDetector(df_v)
        r_squared, _ = detector._fit_parabolic_cup(df_v['close'].iloc[50:150])
        self.assertLess(r_squared, 0.7, "V-shape should have low R^2")

    def test_valid_pattern(self):
        patterns = self.detector.detect_patterns()
        self.assertGreaterEqual(len(patterns), 1, "Should detect at least one pattern")
        p = patterns[0]
        self.assertTrue(p['cup_duration'] >= 30 and p['cup_duration'] <= 300)
        self.assertTrue(p['handle_duration'] >= 5 and p['handle_duration'] <= 50)
        self.assertGreater(p['r_squared_cup'], 0.85)
        self.assertEqual(p['status'], 'Valid')

    def test_invalid_handle_too_long(self):
        df_long_handle = self.df.copy()
        df_long_handle['close'].iloc[150:201] = np.linspace(98, 97, 51)
        detector = PatternDetector(df_long_handle)
        patterns = detector.detect_patterns()
        if patterns:
            self.assertEqual(patterns[0]['status'], 'Invalid')
            self.assertEqual(patterns[0]['reason'], 'Handle too long')

if __name__ == '__main__':
    unittest.main()