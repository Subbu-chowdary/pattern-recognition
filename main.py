import pandas as pd
import os
try:
    import talib
except ImportError:
    print("Error: TA-Lib is not installed. Please install it using 'pip install TA-Lib' after installing the TA-Lib C library via Homebrew ('brew install ta-lib') or manually. See https://mrjbq7.github.io/ta-lib/install.html for details.")
    exit(1)

from pattern_detector import PatternDetector
# Import the plotting function
from plot_utils import plot_pattern 

def main():
    data_dir = 'data'
    patterns_dir = 'patterns' # Directory for saving images
    raw_data_path = os.path.join(data_dir, 'raw_data.csv')
    preprocessed_data_path = os.path.join(data_dir, 'preprocessed_data.csv')
    report_file = 'report.csv'

    # Create patterns directory if it doesn't exist
    os.makedirs(patterns_dir, exist_ok=True)

    # Load data
    if not os.path.exists(raw_data_path):
        print(f"Error: {raw_data_path} not found. Please run your data fetching/generation script (e.g., fetch_data.py or generate_synthetic_data.py) first.")
        return

    df = pd.read_csv(raw_data_path, index_col='open_time', parse_dates=True)
    print(f"Loaded {len(df)} records from {raw_data_path}")

    # Preprocess data (ensure ATR is calculated on float values and numpy arrays for TA-Lib)
    df['avg_candle_size'] = (df['high'] - df['low']).mean()
    # It's important to pass numpy arrays to TA-Lib
    df['ATR'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
    df.to_csv(preprocessed_data_path)
    print(f"Preprocessed data saved to {preprocessed_data_path}")

    # Initialize pattern detector with the preprocessed DataFrame
    detector = PatternDetector(df.copy()) # Pass a copy to avoid SettingWithCopyWarning if detector modifies it

    # Detect and label patterns
    print("Starting pattern detection and labelling...")
    detected_patterns = detector.detect_patterns()
    print(f"Detected and labelled {len(detected_patterns)} patterns.")

    # Filter for valid patterns and plot the first 30 (or all if less than 30)
    valid_patterns_to_plot = [p for p in detected_patterns if p['status'] == 'Valid']
    
    plot_count = 0
    for i, pattern_info in enumerate(valid_patterns_to_plot):
        if plot_count >= 30: # Only plot up to 30 patterns
            break
        
        plot_pattern(df, pattern_info, plot_count + 1, output_dir=patterns_dir, interactive=False)
        plot_count += 1

    # Generate validation summary report
    report_data = detected_patterns
    report_df = pd.DataFrame(report_data)
    report_df.to_csv(report_file, index=False)
    print(f"Validation summary report saved to {report_file}")
    print(f"Successfully processed {len(report_df)} patterns (including invalid ones).")
    print(f"Successfully plotted {plot_count} valid patterns.")

if __name__ == "__main__":
    main()