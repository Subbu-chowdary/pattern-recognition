# Cup and Handle Pattern Detection

This project implements a system to detect "Cup and Handle" patterns in Binance Futures 1-minute OHLCV data. The system aims for at least 99% accuracy in pattern identification and provides visual outputs and a detailed validation report.

## Objective

The primary objective is to identify valid "Cup and Handle" patterns based on defined formation logic and validation rules, visualize them, and generate a summary report.

## Features

- [cite_start]Fetches historical 1-minute OHLCV data for Binance Futures (BTCUSDT)[cite: 33].
- Implements robust "Cup and Handle" pattern detection logic.
- Validates patterns against specific criteria (cup depth, duration, handle retrace, R^2 for cup shape, breakout).
- [cite_start]Generates high-quality plots of detected patterns with marked cup, handle, and breakout zones[cite: 37, 38].
- [cite_start]Saves cropped pattern images using Kaleido for smooth rendering[cite: 4, 39].
- [cite_start]Produces a CSV report summarizing each detected pattern's characteristics and validation status[cite: 42].

## [cite_start]Pattern Formation Logic [cite: 5]

### [cite_start]Cup [cite: 6]

- [cite_start]A smooth, rounded bottom shape[cite: 7].
- [cite_start]Left and right rims (swing highs) at roughly similar price levels[cite: 8].
- [cite_start]Volume may decrease towards the bottom of the cup and pick up near the rim[cite: 9].

### [cite_start]Handle [cite: 10]

- [cite_start]A short consolidation after the cup[cite: 11].
- [cite_start]Typically sloped downward or sideways[cite: 12].
- [cite_start]Lower high than cup rims[cite: 13].

### [cite_start]Breakout [cite: 14]

- [cite_start]Bullish breakout occurs above the handle's upper resistance[cite: 15].

## [cite_start]Validation Rules [cite: 16]

- [cite_start]Cup depth must be at least 2x average candle size (1m)[cite: 17].
- [cite_start]Cup duration: 30 to 300 candles[cite: 18].
- [cite_start]Handle duration: 5 to 50 candles[cite: 19].
- [cite_start]Handle high must be below or equal to left/right rim[cite: 20].
- [cite_start]Handle must retrace no more than 40% of cup depth[cite: 21].
- [cite_start]Smooth curve fit for the cup with a parabolic shape ($R^2 > 0.85$)[cite: 22].
- [cite_start]Price breakout must exceed handle high with at least $1.5 \times ATR(14)$[cite: 23].
- [cite_start]Volume spike on breakout preferred (optional but a bonus)[cite: 24].

## [cite_start]Invalidation Rules [cite: 25]

- [cite_start]Handle breaks below cup bottom[cite: 26].
- [cite_start]Handle lasts longer than 50 candles[cite: 27].
- [cite_start]Cup is V-shaped, not U-shaped (low R^2 fit)[cite: 28].
- [cite_start]No breakout after handle formation[cite: 29].
- [cite_start]Rim levels differ more than 10%[cite: 30].

## Required Deliverables

1.  [cite_start]**Cup and Handle Detection Code:** Identifies at least 30 distinct valid patterns from Binance Futures 1-minute OHLCV data (2024-01-01 to 2025-01-01)[cite: 33, 34].
2.  [cite_start]**Pattern Plotting and Cropping:** For each valid pattern, a smooth arc plot for the cup [cite: 37][cite_start], clearly marked handle and breakout zone [cite: 38][cite_start], saved as a cropped image using `kaleido` (filename: `cup_handle_<pattern_id>.png`)[cite: 39, 40].
3.  [cite_start]**Validation Summary Report:** JSON/CSV file (`report.csv`) with stats for each pattern: start/end time [cite: 43][cite_start], cup depth/duration [cite: 44][cite_start], handle depth/duration [cite: 45][cite_start], R^2 value [cite: 46][cite_start], breakout candle timestamp [cite: 47][cite_start], valid/invalid flag with reason (if invalid)[cite: 48].

## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/your-username/cup_handle_detector.git](https://github.com/your-username/cup_handle_detector.git)
    cd cup_handle_detector
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    _Note: TA-Lib requires a separate installation. Please refer to [TA-Lib's official installation guide](https://mrjbq7.github.io/ta-lib/install.html) for your operating system._

## Usage

1.  **Fetch Data:**
    [cite_start]Run `fetch_data.py` to download Binance Futures 1-minute OHLCV data for BTCUSDT from 2024-01-01 to 2025-01-01[cite: 33]. This will save `raw_data.csv` in the `data/` directory.

    ```bash
    python fetch_data.py
    ```

2.  **Run the Main Detection Script:**
    Execute `main.py` to perform pattern detection, plotting, and report generation. This script will save cropped images in the `patterns/` directory and `report.csv` in the root directory.
    ```bash
    python main.py
    ```

## Project Structure
