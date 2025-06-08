import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb, to_hex
import plotly.graph_objects as go
import base64
from io import BytesIO
from wordcloud import WordCloud
from itertools import cycle
import copy
import plotly.io as pio

# Generate colors palett with interpolation
def adjust_palette(num_colors=21, palette_name="tab20"):
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

# This function creates a reusable Plotly figure with a centered 
# #message for empty data scenarios.
def empty_figure(message="Sin datos"):
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

# Calculates the aggregation interval and normalizes 
# the start and end datetimes.
def calculate_interval_and_range(start, end):
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

# Assigns colors to categories based on their 
# frequency in a DataFrame.
def assign_color_sequence(df, palette):
    family_order = df.groupby("family")["count"].sum().sort_values(ascending=False).index
    color_map = {fam: palette[i % len(palette)] for i, fam in enumerate(family_order)}
    return color_map

# Creates a color function for word clouds that assigns 
# colors based on word frequency.
def make_ordered_color_func(frequencies, cmap_name="tab20"):
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

# Generates a word cloud image from a frequency dictionary.
def generate_wordcloud(frequencies, screen_width, theme = "light"):
    # Set background color based on theme
    bg_color = "white" if theme == "light" else "#212529"

    # Resposive 
    if screen_width<576:
        width=400
        height=500
    else:
        width=800
        height=400

    wc = WordCloud(
        width=width,
        height=height,
        background_color=bg_color,
        prefer_horizontal=1.0,  # Force horizontal layout
    ).generate_from_frequencies(frequencies)

    wc.recolor(color_func=make_ordered_color_func(frequencies, "tab20"))

    # Save the image into a memory buffer
    buffer = BytesIO()
    wc.to_image().save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    return img_base64

# Customize template object in map dark mode render
def custom_dark_template(custom_template):
    FONT_DARK_COLOR="#333333"
    custom_template.layout.legend.font.color = FONT_DARK_COLOR
    custom_template.layout.legend.title.font.color = FONT_DARK_COLOR

    custom_template.data["scattermap"] = [
        go.Scattermap(
            textfont=dict(color=FONT_DARK_COLOR)
        )
    ]
    return custom_template

# Secure copy from layout template
def build_safe_template(template_name: str) -> go.layout.Template:
    tpl = pio.templates[template_name]

    layout = copy.deepcopy(tpl.layout) if tpl.layout else go.Layout()

    data = {}
    for k in dir(tpl.data):
        if not k.startswith("_") and hasattr(tpl.data, k):
            v = getattr(tpl.data, k)
            if isinstance(v, tuple):  # solo tipos de traza
                data[k] = copy.deepcopy(v)

    t = go.layout.Template(layout=layout)
    for k, v in data.items():
        t.data[k] = v
    return t