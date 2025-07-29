import unittest
import pandas as pd
import numpy as np
from pattern_detector import PatternDetector
import talib

class TestPatternDetector(unittest.TestCase):
    def setUp(self):
        # Create mock data with a valid cup and handle pattern
        cup_len = 100
        cup_start_price = 100
        cup_bottom_price = 90
        cup_prices = np.concatenate([
            np.linspace(cup_start_price, cup_bottom_price, cup_len // 2),
            np.linspace(cup_bottom_price, cup_start_price, cup_len // 2)
        ])
        x_cup = np.arange(cup_len)
        a, b, c = np.polyfit(x_cup, cup_prices, 2)
        cup_prices = a * x_cup**2 + b * x_cup + c
        handle_len = 20
        handle_start_price = cup_prices[-1]
        handle_prices = np.linspace(handle_start_price, handle_start_price - 2, handle_len)  # Retrace < 40%
        breakout_len = 5
        breakout_prices = np.linspace(handle_prices[-1], handle_prices[-1] + 5, breakout_len)  # Larger breakout
        total_len = 50 + cup_len + handle_len + breakout_len + 50
        full_prices = np.concatenate([
            np.linspace(95, 100, 50),
            cup_prices,
            handle_prices,
            breakout_prices,
            np.linspace(breakout_prices[-1], breakout_prices[-1] + 2, 50)
        ])
        data = {
            'open_time': pd.to_datetime(pd.date_range(start='2024-01-01', periods=total_len, freq='1min')),
            'open': full_prices,
            'high': full_prices + 0.5,
            'low': full_prices - 0.5,
            'close': full_prices,
            'volume': np.concatenate([
                np.linspace(200, 100, 50),
                np.linspace(100, 50, cup_len // 2),
                np.linspace(50, 100, cup_len // 2),
                np.ones(handle_len) * 80,
                np.array([150, 200, 250, 200, 150]),  # Adjusted breakout volume
                np.ones(50) * 100
            ])
        }
        self.mock_df = pd.DataFrame(data).set_index('open_time')
        self.mock_df['avg_candle_size'] = (self.mock_df['high'] - self.mock_df['low']).mean()
        self.mock_df['ATR'] = talib.ATR(self.mock_df['high'], self.mock_df['low'], self.mock_df['close'], timeperiod=14)
        self.detector = PatternDetector(self.mock_df)

    def test_parabolic_curve_fit(self):
        x = np.arange(100)
        y = 0.01 * x**2 - 0.5 * x + 100
        r_squared, _ = self.detector._fit_parabolic_cup(y)
        self.assertGreater(r_squared, 0.95, "Should fit a perfect parabola with high R^2")
        y_vshape = np.concatenate([np.linspace(100, 50, 20), np.linspace(50, 100, 20)])
        y_vshape = np.pad(y_vshape, (30, 30), mode='edge')
        r_squared_v, _ = self.detector._fit_parabolic_cup(y_vshape)
        self.assertLess(r_squared_v, 0.7, "Should have low R^2 for a V-shape")

    def test_handle_retrace(self):
        mock_df = self.mock_df.copy()
        handle_start_idx = 150
        handle_end_idx = 170
        cup_depth = 100 - 90
        mock_df.loc[mock_df.index[handle_start_idx:handle_end_idx], 'close'] = np.linspace(100, 85, 20)  # Retrace = 15
        mock_df.loc[mock_df.index[handle_start_idx:], 'high'] = mock_df['close'][handle_start_idx:] + 0.5
        mock_df.loc[mock_df.index[handle_start_idx:], 'low'] = mock_df['close'][handle_start_idx:] - 0.5
        detector = PatternDetector(mock_df)
        patterns = detector.detect_patterns()
        self.assertTrue(any(p['reason'] == "Handle retraces more than 40% of cup depth" for p in patterns),
                        "Should detect handle retrace > 40%")

    def test_volume_validation(self):
        cup_segment = self.mock_df.iloc[50:150]
        breakout_candle = self.mock_df.iloc[170]
        valid, reason = self.detector._validate_volume(cup_segment, breakout_candle)
        self.assertTrue(valid, "Volume validation should pass for synthetic data")
        invalid_candle = pd.Series({'volume': 50}, index=['volume'])
        valid, reason = self.detector._validate_volume(cup_segment, invalid_candle)
        self.assertFalse(valid, "Should fail due to low breakout volume")

    def test_no_pattern(self):
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
        detector = PatternDetector(df_no_pattern)
        patterns = detector.detect_patterns()
        self.assertEqual(len(patterns), 0, "Should detect no patterns in linear data")

    def test_valid_pattern(self):
        patterns = self.detector.detect_patterns()
        self.assertGreaterEqual(len([p for p in patterns if p['status'] == 'Valid']), 1,
                               "Should detect at least one valid pattern")
        if patterns:
            p = next(p for p in patterns if p['status'] == 'Valid')
            self.assertTrue(30 <= p['cup_duration'] <= 300, f"Cup duration {p['cup_duration']} out of range")
            self.assertTrue(5 <= p['handle_duration'] <= 50, f"Handle duration {p['handle_duration']} out of range")
            self.assertGreater(p['r_squared_cup'], 0.75, f"R² {p['r_squared_cup']} below threshold")
            self.assertEqual(p['status'], 'Valid', "Pattern should be valid")

if __name__ == '__main__':
    unittest.main()