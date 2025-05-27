import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb, to_hex
import plotly.graph_objects as go
import base64
from io import BytesIO
from wordcloud import WordCloud
from itertools import cycle

# Generate colors palett with interpolation
def adjust_palette(num_colors=21, palette_name="tab20"):
    """
    Generates a palette of colors with `num_colors` using interpolation if necessary.
    
    Parameters:
        num_colors (int): Number of colors to generate.
        palette_name (str): Name of the matplotlib colormap.
        
    Returns:
        list: A list of hexadecimal color codes.
    """
    original_palette = cm.get_cmap(palette_name)
    original_size = original_palette.N

    if num_colors <= original_size:
        # Directly map evenly spaced indices from the original palette
        return [to_hex(original_palette(i)) for i in range(num_colors)]
    
    # Convert the original palette to an array of RGB colors
    rgb_palette = np.array([to_rgb(original_palette(i / (original_size - 1))) for i in range(original_size)])
    
    # Interpolation step for additional colors
    step = ( original_size - 1 ) / ( num_colors - 1 )
    interpolated_palette = []

    for i in range(num_colors):
        num_rep = i * step
        low_color_id = int(num_rep)
        upp_color_id = min(low_color_id + 1, original_size - 1)
        weight = num_rep - low_color_id
      
        interpolated_color = (1 - weight) * rgb_palette[low_color_id] + weight * rgb_palette[upp_color_id]
        interpolated_palette.append(to_hex(interpolated_color))

    return interpolated_palette

# This function creates a reusable Plotly figure with a centered message for empty data scenarios.
def empty_figure(message="Sin datos"):
    """
    Returns a reusable Plotly figure with a centered message for empty data scenarios.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=18),
        xref="paper", yref="paper",
        xanchor="center", yanchor="middle"
    )
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400
    )
    return fig

# This function calculates the aggregation interval and normalizes the start and end datetimes.
def calculate_interval_and_range(start, end):
    """
    Determines the aggregation interval (1h, 1d...) and normalizes start/end datetimes.
    """
    time_delta = (end - start).total_seconds()

    if time_delta <= 86400:
        interval = "1h"
        start = start.replace(minute=0, second=0, microsecond=0)
        end = end.replace(minute=0, second=0, microsecond=0)
    else:
        interval = "1d"
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = end.replace(hour=0, minute=0, second=0, microsecond=0)

    return interval, start, end


def assign_color_sequence(df, palette):
    """
    Assigns colors to categories based on frequency (most frequent first).
    """
    family_order = df.groupby("family")["count"].sum().sort_values(ascending=False).index
    color_map = {fam: palette[i % len(palette)] for i, fam in enumerate(family_order)}
    return color_map


def make_ordered_color_func(frequencies, cmap_name="tab20"):
    """
    Creates a color function that assigns colors in order of frequency using a matplotlib colormap.
    """
    # Get ordered list of colors from colormap
    colors = [to_hex(c) for c in plt.get_cmap(cmap_name).colors]

    # Sort words by descending frequency
    sorted_words = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
    word_order = [word for word, _ in sorted_words]

    # Cycle through colors if not enough unique values
    color_cycle = cycle(colors)
    color_map = {word: next(color_cycle) for word in word_order}

    def color_func(word, *args, **kwargs):
        return color_map.get(word, "#888888")

    return color_func


def generate_wordcloud(frequencies, theme = "light"):
    """
    Generates a WordCloud image and returns it as a base64-encoded PNG string.

    Parameters:
    - frequencies (dict): a dictionary of terms and their corresponding frequencies.
    - theme (str): visual theme of the cloud ("light" or "dark").

    Returns:
    - str: base64-encoded string representing the generated PNG image.
    """

    # Set background color based on theme
    bg_color = "white" if theme == "light" else "#212529"

    # Create the WordCloud instance
    wc = WordCloud(
        width=800,
        height=400,
        background_color=bg_color,
        prefer_horizontal=1.0,  # Force horizontal layout
    ).generate_from_frequencies(frequencies)

    wc.recolor(color_func=make_ordered_color_func(frequencies, "tab20"))

    # Save the image into a memory buffer
    buffer = BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")  # Remove axes for clean appearance
    plt.tight_layout()
    plt.savefig(buffer, format="png", facecolor=bg_color)
    plt.close()

    # Encode the PNG image in base64 to embed it in Dash as HTML img src
    return base64.b64encode(buffer.getvalue()).decode()