import numpy as np
import pandas as pd
import plotly.graph_objects as go

from pramaan import settings as s

DEMAND = "#007AFF"
SUPPLY = "#2C2C2E"
INK = "#1C1C1E"
MUTED = "#6E6E73"
GRID = "#EDEDF0"
SURFACE = "#FFFFFF"
STATUS_COLOUR = {"Shortage": "#D70015", "Watch (falling)": "#C93400", "Balanced": "#248A3D", "Watch (rising)": "#0071A4", "Oversupply": "#8944AB"}
BAND_TINT = {"Shortage": "rgba(215,0,21,.06)", "Watch (falling)": "rgba(201,52,0,.06)", "Balanced": "rgba(36,138,61,.05)", "Watch (rising)": "rgba(0,113,164,.06)", "Oversupply": "rgba(137,68,171,.06)"}
DIVERGING = [[0.0, "#D70015"], [0.25, "#EFA3A3"], [0.5, "#F2F2F4"], [0.75, "#C9A6DB"], [1.0, "#8944AB"]]
SOURCE_COLOUR = {"portal": "#007AFF", "ncs": "#30B0C7", "industry": "#FF9500", "eshram": "#AF52DE"}
CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "zoomIn2d", "zoomOut2d"], "toImageButtonOptions": {"format": "png", "scale": 2}}

TN_OUTLINE = [
    (79.9, 13.55), (80.35, 13.45), (80.30, 13.0), (80.18, 12.5), (79.86, 11.9), (79.85, 11.3), (79.85, 10.8), (79.86, 10.3),
    (79.3, 10.25), (79.0, 9.6), (78.6, 9.2), (78.2, 8.9), (77.95, 8.4), (77.55, 8.08), (77.2, 8.3), (77.2, 8.9),
    (77.3, 9.5), (77.2, 10.0), (76.9, 10.4), (76.75, 10.8), (76.6, 11.3), (76.3, 11.5), (76.6, 11.7), (77.0, 11.85),
    (77.4, 12.1), (77.6, 12.7), (78.2, 12.8), (78.5, 13.1), (78.9, 13.0), (79.3, 13.5), (79.9, 13.55),
]


def base(figure, height=320, legend=True, top=None):
    figure.update_layout(
        template="simple_white", paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, height=height,
        margin=dict(l=6, r=10, t=top if top is not None else (44 if legend else 10), b=6),
        font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, system-ui, Noto Sans Tamil, Noto Sans Devanagari, Arial, sans-serif", size=12, color=INK),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="top", y=1.0, yref="container", xanchor="left", x=0.01, font=dict(size=11.5, color=MUTED)),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor="#D2D2D7", font=dict(color=INK, size=12)),
        bargap=0.3, barcornerradius=3,
    )
    figure.update_xaxes(showgrid=False, linecolor="#D2D2D7", tickcolor="#D2D2D7", tickfont=dict(color=MUTED))
    figure.update_yaxes(gridcolor=GRID, linecolor="#D2D2D7", tickcolor="#D2D2D7", tickfont=dict(color=MUTED), zeroline=False)
    return figure


def scaled(ratio):
    return np.log2(np.clip(ratio, 0.25, 4.0))


def colour_bar(title):
    return dict(title=dict(text=title, side="right", font=dict(size=11)), tickvals=[-1.585, -1, 0, 1, 1.585], ticktext=["0.33", "0.5", "1.0", "2.0", "3.0"], thickness=10, len=0.75, outlinewidth=0)


UNMET = [[0.0, "#F4E9E7"], [0.5, "#E3A493"], [1.0, "#9C2B2B"]]


def district_map(summary, selected, colour_title, hover):
    figure = go.Figure()
    xs, ys = zip(*TN_OUTLINE)
    figure.add_scatter(x=xs, y=ys, mode="lines", fill="toself", fillcolor="#F3F5F9", line=dict(color="#D5DBE5", width=1.5), hoverinfo="skip", showlegend=False)
    size = 26 + 38 * np.sqrt(summary["demand"] / summary["demand"].max())
    figure.add_scatter(
        x=summary["x"], y=summary["y"], mode="markers+text",
        marker=dict(size=size, color=summary["unmet_share"] * 100, colorscale=UNMET, cmin=0, cmax=max(30.0, float(summary["unmet_share"].max()) * 100),
                    colorbar=dict(title=dict(text=colour_title, side="right", font=dict(size=11)), ticksuffix="%", thickness=10, len=0.75, outlinewidth=0),
                    line=dict(color=[INK if d == selected else SURFACE for d in summary["district"]], width=[3 if d == selected else 2 for d in summary["district"]])),
        text=summary["district"], textposition="bottom center", textfont=dict(size=12, color=INK),
        customdata=summary[["district", "demand", "supply", "unmet", "shortages"]].values,
        hovertemplate=hover + "<extra></extra>", showlegend=False,
    )
    figure.update_xaxes(visible=False, range=[76.0, 80.9])
    figure.update_yaxes(visible=False, range=[7.8, 13.9], scaleanchor="x", scaleratio=1)
    return base(figure, height=470, legend=False, top=6)


def opportunity_grid(gaps, districts, trades, short_names, ratio_title, hover):
    frame = gaps.copy()
    frame["col"] = frame["trade"].map({t: i for i, t in enumerate(trades)})
    frame["row"] = frame["district"].map({d: i for i, d in enumerate(districts)})
    figure = go.Figure(go.Scatter(
        x=frame["col"], y=frame["row"], mode="markers+text",
        marker=dict(symbol="square", size=46, color=scaled(frame["ratio"]), colorscale=DIVERGING, cmin=-1.6, cmax=1.6, colorbar=colour_bar(ratio_title), line=dict(color=SURFACE, width=2)),
        text=[f"{r:.2f}" for r in frame["ratio"]], textfont=dict(size=11.5, color=INK),
        customdata=frame[["district", "trade", "demand", "supply", "ratio"]].values,
        hovertemplate=hover + "<extra></extra>",
    ))
    figure.update_xaxes(tickvals=list(range(len(trades))), ticktext=short_names, side="top", tickangle=-28, showline=False, ticks="", range=[-0.6, len(trades) - 0.4])
    figure.update_yaxes(tickvals=list(range(len(districts))), ticktext=districts, autorange="reversed", showgrid=False, showline=False, ticks="", range=[len(districts) - 0.5, -0.6])
    figure.update_layout(dragmode=False)
    return base(figure, height=90 + 56 * len(districts), legend=False, top=90)


def trade_bars(frame, demand_label, supply_label, axis_title):
    ordered = frame.sort_values("gap")
    figure = go.Figure()
    figure.add_bar(y=ordered["short"], x=ordered["demand"], name=demand_label, orientation="h", marker_color=DEMAND, hovertemplate="%{y}: %{x:,.0f}<extra></extra>")
    figure.add_bar(y=ordered["short"], x=ordered["supply"], name=supply_label, orientation="h", marker_color=SUPPLY, hovertemplate="%{y}: %{x:,.0f}<extra></extra>")
    figure.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08)
    figure.update_xaxes(title=axis_title, showgrid=True, gridcolor=GRID)
    figure.update_yaxes(showgrid=False, autorange="reversed")
    return base(figure, height=410)


def sector_bars(frame, demand_label, supply_label, axis_title):
    figure = go.Figure()
    figure.add_bar(x=frame["sector"], y=frame["demand"], name=demand_label, marker_color=DEMAND, text=[f"{v:,.0f}" for v in frame["demand"]], textposition="outside", cliponaxis=False)
    figure.add_bar(x=frame["sector"], y=frame["supply"], name=supply_label, marker_color=SUPPLY, text=[f"{v:,.0f}" for v in frame["supply"]], textposition="outside", cliponaxis=False)
    figure.update_layout(barmode="group")
    figure.update_yaxes(title=axis_title)
    figure.update_yaxes(showgrid=True)
    return base(figure, height=300)


def forecast_chart(history, future, supply, labels, axis_title):
    hx, fx = history["month"].dt.to_timestamp(), future["month"].dt.to_timestamp()
    figure = go.Figure()
    figure.add_scatter(x=list(fx) + list(fx[::-1]), y=list(future["upper"]) + list(future["lower"][::-1]), fill="toself", fillcolor="rgba(0,122,255,.12)", line=dict(width=0), name=labels["band"], hoverinfo="skip")
    figure.add_scatter(x=hx, y=history["openings"], name=labels["history"], line=dict(color=DEMAND, width=2.2), hovertemplate="%{y:,.0f}<extra></extra>")
    figure.add_scatter(x=fx, y=future["forecast"], name=labels["forecast"], line=dict(color=DEMAND, width=2.2, dash="dash"), hovertemplate="%{y:,.0f}<extra></extra>")
    figure.add_scatter(x=list(hx) + list(fx), y=[supply / 12] * (len(hx) + len(fx)), name=labels["supply"], line=dict(color=SUPPLY, width=2.2), hovertemplate="%{y:,.0f}<extra></extra>")
    figure.add_vline(x=fx.iloc[0], line_color="#D2D2D7", line_dash="dot")
    figure.update_layout(hovermode="x unified")
    figure.update_yaxes(title=axis_title)
    figure.update_yaxes(showgrid=True)
    return base(figure, height=380)


def band_shapes(figure, axis, upper):
    for status, low, high in s.BANDS:
        start, end = low or 0, high or upper
        if axis == "x":
            figure.add_vrect(x0=start, x1=end, fillcolor=BAND_TINT[status], line_width=0, layer="below")
        else:
            figure.add_hrect(y0=start, y1=end, fillcolor=BAND_TINT[status], line_width=0, layer="below")


def ratio_path(path, label_status, axis_title):
    upper = max(2.0, float(path["ratio"].max()) + 0.2)
    figure = go.Figure()
    band_shapes(figure, "y", upper)
    figure.add_hline(y=1.0, line_color=MUTED, line_dash="dot", line_width=1)
    figure.add_scatter(
        x=path["month"].astype(str), y=path["ratio"], mode="lines+markers", line=dict(color=INK, width=2),
        marker=dict(size=10, color=[STATUS_COLOUR[x] for x in path["status"]], line=dict(color=SURFACE, width=2)),
        customdata=[label_status(x) for x in path["status"]], hovertemplate="%{x}: %{y:.2f} · %{customdata}<extra></extra>",
    )
    figure.update_yaxes(range=[0, upper], title=axis_title, showgrid=False)
    figure.update_xaxes(type="category")
    return base(figure, height=300, legend=False)


def contributions(history, label_source, index_label, axis_title):
    recent = history.tail(12)
    x = recent["month"].dt.to_timestamp()
    figure = go.Figure()
    for source, colour in SOURCE_COLOUR.items():
        figure.add_bar(x=x, y=recent[f"c_{source}"], name=label_source(source), marker=dict(color=colour, line=dict(color=SURFACE, width=1)), hovertemplate="%{y:+.2f}<extra></extra>")
    figure.add_scatter(x=x, y=recent["index"], name=index_label, mode="lines+markers", line=dict(color=INK, width=2), marker=dict(size=8, color=INK, line=dict(color=SURFACE, width=2)), hovertemplate="%{y:+.2f}<extra></extra>")
    figure.update_layout(barmode="relative", barcornerradius=0, hovermode="x unified")
    figure.update_yaxes(title=axis_title)
    figure.update_yaxes(showgrid=True)
    return base(figure, height=300)


def whatif_strip(before, after, before_label, after_label):
    upper = max(2.6, before + 0.3, after + 0.3)
    figure = go.Figure()
    for status, low, high in s.BANDS:
        figure.add_vrect(x0=low or 0, x1=high or upper, fillcolor=BAND_TINT[status].replace(".06", ".20").replace(".05", ".18"), line_width=0, layer="below")
    figure.add_scatter(x=[before], y=[0.5], mode="markers", name=before_label, marker=dict(size=16, color=SURFACE, line=dict(color=MUTED, width=3)), hovertemplate="%{x:.2f}<extra></extra>")
    figure.add_scatter(x=[after], y=[0.5], mode="markers", name=after_label, marker=dict(size=17, symbol="diamond", color=INK, line=dict(color=SURFACE, width=2)), hovertemplate="%{x:.2f}<extra></extra>")
    figure = base(figure, height=150)
    figure.update_xaxes(range=[0, upper], tickvals=[0, 0.6, 0.8, 1.2, 1.5, round(upper, 1)], showgrid=False)
    figure.update_yaxes(visible=False, range=[0, 1], showgrid=False)
    return figure


def sankey(moves, seats_label):
    sources = [f"{m.from_short} · {m.from_district}" for m in moves.itertuples()]
    targets = [f"{m.to_short} · {m.to_district}" for m in moves.itertuples()]
    nodes = list(dict.fromkeys(sources)) + list(dict.fromkeys(targets))
    index = {name: i for i, name in enumerate(nodes)}
    colours = ["#8944AB"] * len(dict.fromkeys(sources)) + ["#D70015"] * len(dict.fromkeys(targets))
    figure = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=nodes, color=colours, pad=14, thickness=14, line=dict(color=SURFACE, width=1)),
        link=dict(source=[index[x] for x in sources], target=[len(dict.fromkeys(sources)) + list(dict.fromkeys(targets)).index(x) for x in targets],
                  value=moves["seats"], color="rgba(0,122,255,.16)", hovertemplate="%{source.label} → %{target.label}<br>%{value} " + seats_label + "<extra></extra>"),
    ))
    return base(figure, height=max(320, 34 * max(len(dict.fromkeys(sources)), len(dict.fromkeys(targets))) + 60), legend=False, top=10)


def quadrant(radar, threshold, x_title, y_title, label_status):
    upper = max(2.2, float(radar["ratio"].max()) + 0.2)
    growth = radar["growth"] * 100
    spread = max(8.0, float(growth.max() - growth.min()) * 0.15)
    figure = go.Figure()
    band_shapes(figure, "y", upper)
    figure.add_vline(x=threshold * 100, line_color=MUTED, line_dash="dot", line_width=1)
    figure.add_hline(y=1.0, line_color=MUTED, line_dash="dot", line_width=1)
    figure.add_scatter(
        x=growth, y=radar["ratio"], mode="markers+text",
        marker=dict(size=16 + 34 * np.sqrt(radar["demand"] / radar["demand"].max()), color=[STATUS_COLOUR[x] for x in radar["status"]], opacity=0.9, line=dict(color=SURFACE, width=2)),
        text=[n if g > threshold or st != "Balanced" else "" for n, g, st in zip(radar["short"], radar["growth"], radar["status"])],
        textposition="top center", textfont=dict(size=11.5, color=INK), cliponaxis=False,
        customdata=[[n, round(d), label_status(st)] for n, d, st in zip(radar["short"], radar["demand"], radar["status"])],
        hovertemplate="%{customdata[0]}<br>%{x:+.1f}% · %{y:.2f} · %{customdata[2]}<br>%{customdata[1]:,}<extra></extra>",
    )
    figure.update_xaxes(title=x_title, range=[float(growth.min()) - spread, float(growth.max()) + spread], zeroline=True, zerolinecolor="#D2D2D7")
    figure.update_yaxes(title=y_title, range=[0, upper], showgrid=False)
    return base(figure, height=440, legend=False)


def growth_bars(radar, threshold, axis_title):
    ordered = radar.sort_values("growth")
    figure = go.Figure(go.Bar(
        y=ordered["short"], x=ordered["growth"] * 100, orientation="h",
        marker_color=[SUPPLY if g > threshold else DEMAND for g in ordered["growth"]],
        text=[f"{g:+.0%}" for g in ordered["growth"]], textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x:+.1f}%<extra></extra>",
    ))
    figure.add_vline(x=threshold * 100, line_color=MUTED, line_dash="dot")
    figure.update_xaxes(title=axis_title, showgrid=True, gridcolor=GRID)
    figure.update_yaxes(showgrid=False)
    return base(figure, height=440, legend=False)


def warning_timeline(warnings, months, label_status, axis_title):
    figure = go.Figure()
    for status in ["Shortage", "Oversupply"]:
        counts = warnings[warnings["projected_status"] == status]["month"].astype(str).value_counts().reindex(months, fill_value=0)
        figure.add_bar(x=months, y=counts.values, name=label_status(status), marker=dict(color=STATUS_COLOUR[status], line=dict(color=SURFACE, width=2)),
                       text=[c or "" for c in counts.values], textposition="inside", textangle=0, textfont=dict(color=SURFACE), hovertemplate="%{x}: %{y}<extra></extra>")
    figure.update_layout(barmode="stack")
    figure.update_xaxes(type="category")
    figure.update_yaxes(title=axis_title, dtick=1)
    figure.update_yaxes(showgrid=True)
    return base(figure, height=300)


def weight_bars(labels, axis_title):
    names = [labels(k) for k in s.WEIGHTS]
    figure = go.Figure(go.Bar(
        x=list(s.WEIGHTS.values()), y=names, orientation="h", marker_color=[SOURCE_COLOUR[k] for k in s.WEIGHTS],
        text=[f"{w:.0%}" for w in s.WEIGHTS.values()], textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x:.0%}<extra></extra>",
    ))
    figure.update_xaxes(title=axis_title, range=[0, 0.42], tickformat=".0%", showgrid=True, gridcolor=GRID)
    figure.update_yaxes(showgrid=False, autorange="reversed")
    return base(figure, height=240, legend=False)


def accuracy_bars(by_trade, model_label, naive_label, axis_title):
    ordered = by_trade.sort_values("mape")
    figure = go.Figure()
    figure.add_bar(y=ordered["short"], x=ordered["mape"], orientation="h", name=model_label, marker_color=DEMAND, hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
    figure.add_bar(y=ordered["short"], x=ordered["naive_mape"], orientation="h", name=naive_label, marker_color="#D2D2D7", hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
    figure.update_layout(barmode="group")
    figure.update_xaxes(title=axis_title, showgrid=True, gridcolor=GRID)
    figure.update_yaxes(showgrid=False)
    return base(figure, height=400)
