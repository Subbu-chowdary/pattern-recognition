# import plotly.graph_objects as go
# from plotly.offline import plot
# import os
# import pandas as pd
# import numpy as np
# from scipy.optimize import curve_fit

# def _parabolic_curve(x, a, b, c):
#     """Parabolic function for cup fitting."""
#     return a * x**2 + b * x + c

# def plot_pattern(data, pattern_info, pattern_id, output_dir="patterns", interactive=False):
#     """
#     Plots a detected Cup and Handle pattern and saves it as an image.
#     Optionally generates an interactive HTML plot.
#     """
#     os.makedirs(output_dir, exist_ok=True)

#     # Extract relevant data for the pattern
#     cup_start_idx = pattern_info['cup_start_idx']
#     cup_end_idx = pattern_info['cup_end_idx']
#     handle_start_idx = pattern_info['handle_start_idx']
#     handle_end_idx = pattern_info['handle_end_idx']
#     breakout_candle_idx = pattern_info['breakout_candle_idx']

#     # Determine the plotting range: from a bit before cup start to a bit after breakout
#     plot_start_idx = max(0, cup_start_idx - 20)
#     plot_end_idx = min(len(data) - 1, breakout_candle_idx + 20)
#     plot_data = data.iloc[plot_start_idx:plot_end_idx+1].copy()

#     fig = go.Figure(data=[go.Candlestick(
#         x=plot_data.index,
#         open=plot_data['open'],
#         high=plot_data['high'],
#         low=plot_data['low'],
#         close=plot_data['close'],
#         name='OHLC'
#     )])

#     # Plot the cup arc
#     cup_segment_data = data.iloc[cup_start_idx:cup_end_idx+1]
#     cup_prices = cup_segment_data['close']
#     x_cup = np.arange(len(cup_prices))

#     # Re-fit parabola for plotting with full cup segment to ensure smooth arc
#     try:
#         popt, _ = curve_fit(_parabolic_curve, x_cup, cup_prices)
#         y_fit = _parabolic_curve(x_cup, *popt)
#         # Shift x_cup to match the actual datetime index for plotting
#         x_cup_datetime = cup_segment_data.index
#         fig.add_trace(go.Scatter(
#             x=x_cup_datetime,
#             y=y_fit,
#             mode='lines',
#             name='Cup Arc',
#             line=dict(color='blue', width=2)
#         ))
#     except (RuntimeError, ValueError):
#         print(f"Could not fit parabolic curve for pattern {pattern_id} during plotting.")

#     # Mark Cup Rims
#     fig.add_trace(go.Scatter(
#         x=[data.index[cup_start_idx], data.index[cup_end_idx]],
#         y=[pattern_info['left_rim_price'], pattern_info['right_rim_price']],
#         mode='markers',
#         marker=dict(symbol='circle', size=10, color='purple'),
#         name='Cup Rims'
#     ))

#     # Mark Cup Bottom
#     cup_bottom_ts = data.iloc[data.index.get_loc(cup_segment_data.index[0]) + np.argmin(cup_prices)].name
#     fig.add_trace(go.Scatter(
#         x=[cup_bottom_ts],
#         y=[pattern_info['cup_bottom_price']],
#         mode='markers',
#         marker=dict(symbol='star', size=12, color='green'),
#         name='Cup Bottom'
#     ))

#     # Mark Handle
#     handle_segment_data = data.iloc[handle_start_idx:handle_end_idx+1]
#     fig.add_trace(go.Scatter(
#         x=handle_segment_data.index,
#         y=handle_segment_data['close'],
#         mode='lines',
#         name='Handle',
#         line=dict(color='orange', width=2)
#     ))
#     fig.add_shape(type="line",
#         x0=handle_segment_data.index[0], y0=pattern_info['handle_high_price'],
#         x1=handle_segment_data.index[-1], y1=pattern_info['handle_high_price'],
#         line=dict(color="red", width=1, dash="dash"),
#         name="Handle Resistance"
#     )


#     # Mark Breakout Zone
#     breakout_candle_data = data.iloc[breakout_candle_idx]
#     fig.add_vline(x=breakout_candle_data.name, line_width=2, line_dash="dash", line_color="green", name="Breakout Candle")
#     fig.add_annotation(
#         x=breakout_candle_data.name, y=breakout_candle_data['high'],
#         text="Breakout", showarrow=True, arrowhead=2, ax=0, ay=-40
#     )


#     fig.update_layout(
#         title=f"Cup and Handle Pattern {pattern_id}",
#         xaxis_title="Time",
#         yaxis_title="Price",
#         xaxis_rangeslider_visible=False,
#         template="plotly_white",
#         height=600,
#         width=1000,
#         hovermode="x unified"
#     )

#     filename_png = os.path.join(output_dir, f"cup_handle_{pattern_id}.png")
#     fig.write_image(filename_png, scale=2) # Scale for better resolution
#     print(f"Saved {filename_png}")

#     if interactive:
#         filename_html = os.path.join(output_dir, f"cup_handle_{pattern_id}.html")
#         fig.write_html(filename_html)
#         print(f"Saved interactive plot to {filename_html}")

import matplotlib.pyplot as plt

def plot_pattern(df, pattern, filename):
    start, end = pattern['start'], pattern['end']
    df_slice = df.iloc[start:end+1]
    plt.figure(figsize=(12, 5))
    plt.plot(df_slice['timestamp'], df_slice['close'], label='Close Price')

    # Mark key points
    keys = ['left_rim', 'bottom', 'right_rim', 'handle_end', 'breakout']
    for key in keys:
        idx = pattern[key] - start
        if 0 <= idx < len(df_slice):
            plt.plot(df_slice.iloc[idx]['timestamp'], df_slice.iloc[idx]['close'], 'o', label=key)

    plt.title('Cup and Handle Pattern')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)
    plt.close()
