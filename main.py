import pandas as pd
import os
from pattern_detector import PatternDetector
from plot_utils import plot_pattern
import numpy as np
import talib

def preprocess_data(df):
    """
    Adds necessary indicators to the DataFrame.
    """
    df['avg_candle_size'] = (df['high'] - df['low']).mean()
    df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    return df

def main():
    data_dir = 'data'
    raw_data_path = os.path.join(data_dir, 'raw_data.csv')
    preprocessed_data_path = os.path.join(data_dir, 'preprocessed_data.csv')
    patterns_dir = 'patterns'
    report_file = 'report.csv'

    # Load data
    if not os.path.exists(raw_data_path):
        print(f"Error: {raw_data_path} not found. Please run fetch_data.py first.")
        return

    df = pd.read_csv(raw_data_path, index_col='open_time', parse_dates=True)
    print(f"Loaded {len(df)} records from {raw_data_path}")

    # Preprocess data
    df = preprocess_data(df)
    df.to_csv(preprocessed_data_path)
    print(f"Preprocessed data saved to {preprocessed_data_path}")

    # Initialize pattern detector
    detector = PatternDetector(df)

    # Detect patterns
    print("Starting pattern detection...")
    detected_patterns = detector.detect_patterns()
    print(f"Detected {len(detected_patterns)} potential patterns.")

    # Filter for valid patterns and generate report
    valid_patterns = []
    report_data = []

    pattern_count = 0
    for i, pattern in enumerate(detected_patterns):
        # The detection logic within PatternDetector.detect_patterns already incorporates
        # most validation and invalidation rules directly.
        # We just need to add a 'pattern_id' for reporting and plotting.
        
        # Ensure we only process and save up to 30 valid patterns
        if pattern_count >= 30:
            break

        pattern_id = f"{pattern_count + 1:02d}"
        pattern['pattern_id'] = pattern_id
        valid_patterns.append(pattern)

        # Plot and save image
        print(f"Plotting and saving pattern {pattern_id}...")
        plot_pattern(df, pattern, pattern_id, output_dir=patterns_dir, interactive=False)
        pattern_count += 1

        # Prepare report entry
        report_entry = {
            'pattern_id': pattern['pattern_id'],
            'start_time': pattern['start_time'],
            'end_time': pattern['end_time'],
            'cup_depth': pattern['cup_depth'],
            'cup_duration': pattern['cup_duration'],
            'handle_depth': pattern['handle_depth'],
            'handle_duration': pattern['handle_duration'],
            'r_squared_cup': pattern['r_squared_cup'],
            'breakout_candle_timestamp': pattern['breakout_candle_timestamp'],
            'status': pattern['status'],
            'reason': pattern['reason']
        }
        report_data.append(report_entry)

    # Generate validation summary report
    report_df = pd.DataFrame(report_data)
    report_df.to_csv(report_file, index=False)
    print(f"Validation summary report saved to {report_file}")
    print(f"Successfully identified and saved {pattern_count} valid patterns.")

if __name__ == "__main__":
    main()