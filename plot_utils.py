# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import pandas as pd
# import os
# import numpy as np # Essential for numpy functions like np.arange

# # Define parabolic_curve locally for plot_utils to ensure it's always available
# def parabolic_curve(x, a, b, c):
#     return a * x**2 + b * x + c

# def plot_pattern(df, pattern_info, pattern_id, output_dir="patterns", interactive=False):
#     """
#     Plots a detected Cup and Handle pattern with its components.
#     Saves the plot as a PNG image or displays it interactively.
#     """
#     # Ensure output directory exists
#     os.makedirs(output_dir, exist_ok=True)

#     # Extract pattern details using original column names from PatternDetector
#     cup_start_idx = pattern_info['cup_start_idx']
#     cup_end_idx = pattern_info['cup_end_idx']
#     handle_start_idx = pattern_info['handle_start_idx']
#     handle_end_idx = pattern_info['handle_end_idx']
#     breakout_candle_idx = pattern_info['breakout_candle_idx']

#     # Get segments from the original DataFrame using index locations
#     # Show some context before cup and after breakout
#     full_segment_start_idx = cup_start_idx - 20 
#     full_segment_end_idx = breakout_candle_idx + 20 if breakout_candle_idx is not None else handle_end_idx + 20
    
#     # Ensure indices are within bounds of the DataFrame
#     full_segment_start_idx = max(0, full_segment_start_idx)
#     full_segment_end_idx = min(len(df) - 1, full_segment_end_idx)

#     # Slice the DataFrame for the plot
#     plot_df = df.iloc[full_segment_start_idx : full_segment_end_idx + 1].copy()

#     # Get cup segment for plotting the parabolic arc
#     cup_segment_for_plot = df.iloc[cup_start_idx : cup_end_idx + 1]
#     x_cup = np.arange(len(cup_segment_for_plot))
    
#     # Using popt from pattern_info
#     popt_params = pattern_info.get('popt') # Use .get() for safety
    
#     cup_arc_y_pred = None
#     if popt_params and len(popt_params) == 3: # Ensure popt_params are valid
#         a, b, c = popt_params
#         cup_arc_y_pred = parabolic_curve(x_cup, a, b, c)

#     # Create subplots (OHLC and Volume)
#     fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
#                         vertical_spacing=0.1, row_heights=[0.7, 0.3])

#     # Add OHLC candles
#     fig.add_trace(go.Candlestick(x=plot_df.index,
#                                  open=plot_df['open'],
#                                  high=plot_df['high'],
#                                  low=plot_df['low'],
#                                  close=plot_df['close'],
#                                  name='OHLC'), row=1, col=1)

#     # Add Cup Arc if parameters are available
#     if cup_arc_y_pred is not None:
#         cup_arc_x_start = cup_segment_for_plot.index[0]
#         cup_arc_x = pd.date_range(start=cup_arc_x_start, periods=len(cup_arc_y_pred), freq='1min')
#         fig.add_trace(go.Scatter(x=cup_arc_x, y=cup_arc_y_pred, mode='lines',
#                                  line=dict(color='blue', width=2), name='Cup Arc'), row=1, col=1)

#     # Mark Rims
#     fig.add_trace(go.Scatter(x=[pattern_info['start_time']], y=[pattern_info['left_rim_price']],
#                              mode='markers', marker=dict(color='purple', size=10),
#                              name='Left Rim'), row=1, col=1)
    
#     right_rim_timestamp = df.index[cup_end_idx] # Correctly get timestamp for right rim
#     fig.add_trace(go.Scatter(x=[right_rim_timestamp], y=[pattern_info['right_rim_price']],
#                              mode='markers', marker=dict(color='purple', size=10),
#                              name='Right Rim'), row=1, col=1)
    
#     # Mark Cup Bottom
#     fig.add_trace(go.Scatter(x=[pattern_info['cup_bottom_timestamp']], y=[pattern_info['cup_bottom_price']],
#                              mode='markers', marker=dict(color='green', size=12, symbol='star'),
#                              name='Cup Bottom'), row=1, col=1)

#     # Highlight Handle
#     handle_plot_df = df.iloc[handle_start_idx : handle_end_idx + 1]
#     fig.add_trace(go.Scatter(x=handle_plot_df.index, y=handle_plot_df['close'], mode='lines',
#                              line=dict(color='orange', width=3), name='Handle'), row=1, col=1)

#     # Mark Breakout
#     if pattern_info['breakout_candle_timestamp']:
#         breakout_x = pattern_info['breakout_candle_timestamp']
#         breakout_y = pattern_info['breakout_price']
        
#         # Draw a line from handle high to breakout point
#         handle_end_timestamp = df.index[handle_end_idx]
#         fig.add_shape(type="line",
#                       x0=handle_end_timestamp, y0=pattern_info['handle_high_price'],
#                       x1=breakout_x, y1=breakout_y,
#                       line=dict(color="green", width=2, dash="dash"),
#                       row=1, col=1)
#         fig.add_annotation(x=breakout_x, y=breakout_y,
#                            text="Breakout", showarrow=True, arrowhead=2,
#                            xanchor='left', yanchor='bottom', bgcolor="rgba(255, 255, 255, 0.7)",
#                            font=dict(color="green", size=10), row=1, col=1)

#     # Add Volume
#     fig.add_trace(go.Bar(x=plot_df.index, y=plot_df['volume'], name='Volume', marker_color='grey'), row=2, col=1)

#     # Update layout
#     fig.update_layout(
#         title=f'Cup and Handle Pattern {pattern_id} - R²: {pattern_info["r_squared_cup"]:.2f}',
#         xaxis_rangeslider_visible=False,
#         height=600, width=900,
#         hovermode="x unified",
#         margin=dict(l=20, r=20, t=50, b=20),
#         template="plotly_white"
#     )
#     fig.update_yaxes(title_text="Price", row=1, col=1)
#     fig.update_yaxes(title_text="Volume", row=2, col=1)

#     # Save or show plot
#     filename_png = os.path.join(output_dir, f'cup_handle_{pattern_id:02d}.png')
#     if not interactive:
#         try:
#             fig.write_image(filename_png, scale=2) # Scale for better resolution
#             # print(f"Plotting and saving pattern {pattern_id:02d} to {filename_png}...") # Already printed in main.py
#         except Exception as e:
#             print(f"Error saving image for pattern {pattern_id}: {e}")
#             print("Please ensure Kaleido is correctly installed. You might need to run 'pip install kaleido' and ensure Chrome is accessible to Kaleido.")
#             print("If you continue to face issues, you can try running 'kaleido.get_chrome_sync()' in a Python interpreter.")
#     else:
#         fig.show()

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os
import numpy as np

# Define parabolic_curve locally for plot_utils to ensure it's always available
def parabolic_curve(x, a, b, c):
    return a * x**2 + b * x + c

def plot_pattern(df, pattern_info, pattern_id, output_dir="patterns", interactive=False):
    """
    Plots a detected Cup and Handle pattern with its components.
    Saves the plot as a PNG image or displays it interactively.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Extract pattern details using original column names from PatternDetector
    cup_start_idx = pattern_info['cup_start_idx']
    cup_end_idx = pattern_info['cup_end_idx']
    handle_start_idx = pattern_info['handle_start_idx']
    handle_end_idx = pattern_info['handle_end_idx']
    breakout_candle_idx = pattern_info['breakout_candle_idx']

    # Get segments from the original DataFrame using index locations
    # Show some context before cup and after breakout
    full_segment_start_idx = cup_start_idx - 20
    full_segment_end_idx = breakout_candle_idx + 20 if breakout_candle_idx is not None else handle_end_idx + 20
    
    # Ensure indices are within bounds of the DataFrame
    full_segment_start_idx = max(0, full_segment_start_idx)
    full_segment_end_idx = min(len(df) - 1, full_segment_end_idx)

    # Slice the DataFrame for the plot
    plot_df = df.iloc[full_segment_start_idx : full_segment_end_idx + 1].copy()

    # Get cup segment for plotting the parabolic arc
    cup_segment_for_plot = df.iloc[cup_start_idx : cup_end_idx + 1]
    x_cup = np.arange(len(cup_segment_for_plot))
    
    # Using popt from pattern_info
    popt_params = pattern_info.get('popt') # Use .get() for safety
    
    cup_arc_y_pred = None
    if popt_params and len(popt_params) == 3: # Ensure popt_params are valid
        a, b, c = popt_params
        cup_arc_y_pred = parabolic_curve(x_cup, a, b, c)

    # Create subplots (OHLC and Volume)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.1, row_heights=[0.7, 0.3])

    # Add OHLC candles
    fig.add_trace(go.Candlestick(x=plot_df.index,
                                 open=plot_df['open'],
                                 high=plot_df['high'],
                                 low=plot_df['low'],
                                 close=plot_df['close'],
                                 name='OHLC'), row=1, col=1)

    # Add Cup Arc if parameters are available
    if cup_arc_y_pred is not None:
        cup_arc_x_start = cup_segment_for_plot.index[0]
        cup_arc_x = pd.date_range(start=cup_arc_x_start, periods=len(cup_arc_y_pred), freq='1min')
        fig.add_trace(go.Scatter(x=cup_arc_x, y=cup_arc_y_pred, mode='lines',
                                 line=dict(color='blue', width=2), name='Cup Arc'), row=1, col=1)

    # Mark Rims
    fig.add_trace(go.Scatter(x=[pattern_info['start_time']], y=[pattern_info['left_rim_price']],
                             mode='markers', marker=dict(color='purple', size=10),
                             name='Left Rim'), row=1, col=1)
    
    right_rim_timestamp = df.index[cup_end_idx] # Correctly get timestamp for right rim
    fig.add_trace(go.Scatter(x=[right_rim_timestamp], y=[pattern_info['right_rim_price']],
                             mode='markers', marker=dict(color='purple', size=10),
                             name='Right Rim'), row=1, col=1)
    
    # Mark Cup Bottom
    fig.add_trace(go.Scatter(x=[pattern_info['cup_bottom_timestamp']], y=[pattern_info['cup_bottom_price']],
                             mode='markers', marker=dict(color='green', size=12, symbol='star'),
                             name='Cup Bottom'), row=1, col=1)

    # Highlight Handle
    handle_plot_df = df.iloc[handle_start_idx : handle_end_idx + 1]
    fig.add_trace(go.Scatter(x=handle_plot_df.index, y=handle_plot_df['close'], mode='lines',
                             line=dict(color='orange', width=3), name='Handle'), row=1, col=1)

    # Mark Breakout
    if pattern_info['breakout_candle_timestamp']:
        breakout_x = pattern_info['breakout_candle_timestamp']
        breakout_y = pattern_info['breakout_price']
        
        # Draw a line from handle high to breakout point
        handle_end_timestamp = df.index[handle_end_idx]
        fig.add_shape(type="line",
                      x0=handle_end_timestamp, y0=pattern_info['handle_high_price'],
                      x1=breakout_x, y1=breakout_y,
                      line=dict(color="green", width=2, dash="dash"),
                      row=1, col=1)
        fig.add_annotation(x=breakout_x, y=breakout_y,
                           text="Breakout", showarrow=True, arrowhead=2,
                           xanchor='left', yanchor='bottom', bgcolor="rgba(255, 255, 255, 0.7)",
                           font=dict(color="green", size=10), row=1, col=1)

    # Add Volume
    fig.add_trace(go.Bar(x=plot_df.index, y=plot_df['volume'], name='Volume', marker_color='grey'), row=2, col=1)

    # Update layout
    fig.update_layout(
        title=f'Cup and Handle Pattern {pattern_id} - R²: {pattern_info["r_squared_cup"]:.2f}',
        xaxis_rangeslider_visible=False,
        height=600, width=900,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
        template="plotly_white"
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    # Save or show plot
    filename_png = os.path.join(output_dir, f'cup_handle_{pattern_id:02d}.png')
    if not interactive:
        try:
            fig.write_image(filename_png, scale=2) # Scale for better resolution
        except Exception as e:
            print(f"Error saving image for pattern {pattern_id}: {e}")
            print("Please ensure Kaleido is correctly installed. You might need to run 'pip install kaleido' and ensure Chrome is accessible to Kaleido.")
    else:
        fig.show()