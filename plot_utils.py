

import plotly.graph_objects as go
import os
import numpy as np
from scipy.optimize import curve_fit

def _parabolic_curve(x, a, b, c):
    """Parabolic function for cup fitting."""
    return a * x**2 + b * x + c

def plot_pattern(data, pattern_info, pattern_id, output_dir="patterns", interactive=False):
    """
    Plots a detected Cup and Handle pattern and saves it as an image.
    Shows R² of the parabolic cup fit on the chart.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Extract indices
    cup_start_idx = pattern_info['cup_start_idx']
    cup_end_idx = pattern_info['cup_end_idx']
    handle_start_idx = pattern_info['handle_start_idx']
    handle_end_idx = pattern_info['handle_end_idx']
    breakout_candle_idx = pattern_info['breakout_candle_idx']

    # Define plot range
    plot_start_idx = max(0, cup_start_idx - 20)
    plot_end_idx = min(len(data) - 1, breakout_candle_idx + 20)
    plot_data = data.iloc[plot_start_idx:plot_end_idx+1].copy()

    # Create candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=plot_data.index,
        open=plot_data['open'],
        high=plot_data['high'],
        low=plot_data['low'],
        close=plot_data['close'],
        name='OHLC'
    )])

    # Plot Cup Arc with R² calculation
    cup_segment_data = data.iloc[cup_start_idx:cup_end_idx+1]
    cup_prices = cup_segment_data['close'].values
    x_cup = np.arange(len(cup_prices))

    try:
        popt, _ = curve_fit(_parabolic_curve, x_cup, cup_prices)
        y_fit = _parabolic_curve(x_cup, *popt)

        # Calculate R²
        ss_res = np.sum((cup_prices - y_fit) ** 2)
        ss_tot = np.sum((cup_prices - np.mean(cup_prices)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        # Add Cup Arc line
        fig.add_trace(go.Scatter(
            x=cup_segment_data.index,
            y=y_fit,
            mode='lines',
            name=f'Cup Arc (R²={r_squared:.3f})',
            line=dict(color='blue', width=2)
        ))

        # Add R² annotation at cup bottom
        cup_bottom_ts = cup_segment_data.index[np.argmin(cup_prices)]
        fig.add_annotation(
            x=cup_bottom_ts,
            y=min(cup_prices),
            text=f"R²={r_squared:.3f}",
            showarrow=False,
            font=dict(color="blue", size=12, family="Arial"),
            yshift=-30
        )

    except (RuntimeError, ValueError):
        print(f"Could not fit parabolic curve for pattern {pattern_id} during plotting.")

    # Mark Cup Rims
    fig.add_trace(go.Scatter(
        x=[data.index[cup_start_idx], data.index[cup_end_idx]],
        y=[pattern_info['left_rim_price'], pattern_info['right_rim_price']],
        mode='markers',
        marker=dict(symbol='circle', size=10, color='purple'),
        name='Cup Rims'
    ))

    # Mark Cup Bottom
    fig.add_trace(go.Scatter(
        x=[cup_segment_data.index[np.argmin(cup_prices)]],
        y=[pattern_info['cup_bottom_price']],
        mode='markers',
        marker=dict(symbol='star', size=12, color='green'),
        name='Cup Bottom'
    ))

    # Mark Handle
    handle_segment_data = data.iloc[handle_start_idx:handle_end_idx+1]
    fig.add_trace(go.Scatter(
        x=handle_segment_data.index,
        y=handle_segment_data['close'],
        mode='lines',
        name='Handle',
        line=dict(color='orange', width=2)
    ))
    fig.add_shape(
        type="line",
        x0=handle_segment_data.index[0], y0=pattern_info['handle_high_price'],
        x1=handle_segment_data.index[-1], y1=pattern_info['handle_high_price'],
        line=dict(color="red", width=1, dash="dash"),
        name="Handle Resistance"
    )

    # Mark Breakout
    breakout_candle_data = data.iloc[breakout_candle_idx]
    fig.add_vline(
        x=breakout_candle_data.name,
        line_width=2, line_dash="dash", line_color="green", name="Breakout Candle"
    )
    fig.add_annotation(
        x=breakout_candle_data.name, y=breakout_candle_data['high'],
        text="Breakout", showarrow=True, arrowhead=2, ax=0, ay=-40
    )

    fig.update_layout(
        title=f"Cup and Handle Pattern {pattern_id}",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=600,
        width=1000,
        hovermode="x unified"
    )

    # Save images
    filename_png = os.path.join(output_dir, f"cup_handle_{pattern_id}.png")
    fig.write_image(filename_png, scale=2)
    print(f"Saved {filename_png}")

    if interactive:
        filename_html = os.path.join(output_dir, f"cup_handle_{pattern_id}.html")
        fig.write_html(filename_html)
        print(f"Saved interactive plot to {filename_html}")
