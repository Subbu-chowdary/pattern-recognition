# Cup and Handle Pattern Detection

This project implements a system to detect "Cup and Handle" patterns in Binance Futures 1-minute OHLCV data. The system aims for at least 99% accuracy in pattern identification and provides visual outputs and a detailed validation report.

## Objective

The primary objective is to identify valid "Cup and Handle" patterns based on defined formation logic and validation rules, visualize them, and generate a summary report.

## Features

- Fetches historical 1-minute OHLCV data for Binance Futures (BTCUSDT).
- Implements robust "Cup and Handle" pattern detection logic.
- Validates patterns against specific criteria (cup depth, duration, handle retrace, R^2 for cup shape, breakout).
- Generates high-quality plots of detected patterns with marked cup, handle, and breakout zones.
- Saves cropped pattern images using Kaleido for smooth rendering.
- Produces a CSV report summarizing each detected pattern's characteristics and validation status.

## How It Works

1. **Data Acquisition:**  
   The system fetches historical 1-minute OHLCV data for Binance Futures (BTCUSDT) using `fetch_data.py`. This data is saved in the `data/` directory.

2. **Preprocessing:**  
   The raw data is preprocessed to add technical indicators such as ATR (Average True Range) and average candle size, which are used for validation.

3. **Pattern Detection:**  
   The main detection logic (in `pattern_detector.py`) scans the data for segments that match the "Cup and Handle" formation rules. It fits a parabolic curve to candidate cup segments, checks rim similarity, cup depth, handle retrace, and breakout criteria.

4. **Validation:**  
   Each detected pattern is validated against strict rules (see below). Invalid patterns are discarded or flagged with a reason.

5. **Visualization:**  
   For each valid pattern, a plot is generated using Plotly, marking the cup arc, handle, and breakout zone. Images are saved using Kaleido in the `patterns/` directory.

6. **Reporting:**  
   A summary CSV report (`report.csv`) is generated, listing all detected patterns with their statistics and validation status.

## Pattern Formation Logic

### Cup

- A smooth, rounded bottom shape.
- Left and right rims (swing highs) at roughly similar price levels.
- Volume may decrease towards the bottom of the cup and pick up near the rim.

### Handle

- A short consolidation after the cup.
- Typically sloped downward or sideways.
- Lower high than cup rims.

### Breakout

- Bullish breakout occurs above the handle's upper resistance.

## Validation Rules

- Cup depth must be at least 2x average candle size (1m).
- Cup duration: 30 to 300 candles.
- Handle duration: 5 to 50 candles.
- Handle high must be below or equal to left/right rim.
- Handle must retrace no more than 40% of cup depth.
- Smooth curve fit for the cup with a parabolic shape ($R^2 > 0.85$).
- Price breakout must exceed handle high with at least $1.5 \times ATR(14)$.
- Volume spike on breakout preferred (optional but a bonus).

## Invalidation Rules

- Handle breaks below cup bottom.
- Handle lasts longer than 50 candles.
- Cup is V-shaped, not U-shaped (low R^2 fit).
- No breakout after handle formation.
- Rim levels differ more than 10%.

## Required Deliverables

1.  **Cup and Handle Detection Code:** Identifies at least 30 distinct valid patterns from Binance Futures 1-minute OHLCV data (2024-01-01 to 2025-01-01).
2.  **Pattern Plotting and Cropping:** For each valid pattern, a smooth arc plot for the cup, clearly marked handle and breakout zone, saved as a cropped image using `kaleido` (filename: `cup_handle_<pattern_id>.png`).
3.  **Validation Summary Report:** JSON/CSV file (`report.csv`) with stats for each pattern: start/end time, cup depth/duration, handle depth/duration, R^2 value, breakout candle timestamp, valid/invalid flag with reason (if invalid).

## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/cup_handle_detector.git
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
    Run `fetch_data.py` to download Binance Futures 1-minute OHLCV data for BTCUSDT from 2024-01-01 to 2025-01-01. This will save `raw_data.csv` in the `data/` directory.

    ```bash
    python fetch_data.py
    ```

2.  **Run the Main Detection Script:**
    Execute `main.py` to perform pattern detection, plotting, and report generation. This script will save cropped images in the `patterns/` directory and `report.csv` in the root directory.
    ```bash
    python main.py
    ```

## Project Structure

The project will be evaluated based on:

- **Accuracy of pattern detection:** Aiming for 99% accuracy.
- **Code quality:** structure, clarity, and efficiency.
- **Visual clarity of plotted charts**.
- **Correct application of validation/invalidation logic**.
- **Robustness:** Handling edge cases and noisy data.
